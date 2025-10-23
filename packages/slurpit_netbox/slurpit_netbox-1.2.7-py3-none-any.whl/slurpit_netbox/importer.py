import requests

from datetime import datetime

from django.core.exceptions import ObjectDoesNotExist
from django.contrib.contenttypes.models import ContentType
from django.db import connection, transaction
from django.db.models import QuerySet, F, OuterRef, Subquery
from django.utils import timezone
from django.db.models.expressions import RawSQL
from django.utils.text import slugify

from . import get_config
from .models import SlurpitImportedDevice, SlurpitStagedDevice, ensure_slurpit_tags, SlurpitSetting, SlurpitPlanning, SlurpitSnapshot
from .management.choices import *
from .references import base_name, plugin_type, custom_field_data_name
from .references.generic import get_default_objects, status_inventory, status_offline, get_create_dcim_objects, set_device_custom_fields, status_active
from .references.imports import *
from dcim.models import Interface, Site
from ipam.models import IPAddress, Prefix

BATCH_SIZE = 512
columns = ('slurpit_id', 'disabled', 'hostname', 'fqdn', 'ipv4', 'device_os', 'device_type', 'brand', "serial", "os_version", "snmp_uptime", 'created', 'last_updated', 'site')

import re

ti = 50
def slug_string(input_string, ti):
    # Remove all characters except hyphens, dots, word characters, and whitespace
    cleaned_string = re.sub(r'[^\-.\w\s]', '', input_string)
    
    # Remove leading and trailing spaces or dots
    cleaned_string = re.sub(r'^[\s.]+|[\s.]+$', '', cleaned_string)
    
    # Replace sequences of hyphens, dots, or whitespace with a single hyphen
    cleaned_string = re.sub(r'[-.\s]+', '-', cleaned_string)
    
    # Convert to lowercase and truncate to length ti
    result_string = cleaned_string.lower()[:ti]
    
    return result_string

def get_devices(offset):
    try:
        setting = SlurpitSetting.objects.get()
        uri_base = setting.server_url
        headers = {
                        'authorization': setting.api_key,
                        'useragent': f"{plugin_type}/requests",
                        'accept': 'application/json'
                    }
        uri_devices = f"{uri_base}/api/devices?offset={offset}&limit={BATCH_SIZE}"
        r = requests.get(uri_devices, headers=headers, timeout=15, verify=False)
        # r.raise_for_status()
        data = r.json()
        return data, ""
    except ObjectDoesNotExist as e:
        log_message = "Api key not configured in settings"
        return None, log_message
    except Exception as e:
        log_message = "Please confirm the Slurp'it server is running and reachable."
        return None, log_message

def start_device_import():
    with connection.cursor() as cursor:
        cursor.execute(f"truncate {SlurpitStagedDevice._meta.db_table} cascade")

def format_address(street, number, zipcode, country):
    return f"{street} {number} {zipcode} {country}"

def create_sites(data):
    for item in data:
        if 'sitename' not in item or item['sitename'] == "":
            continue

        # First, format the address
        address = format_address(item['street'], item['number'], item['zipcode'], item['country'])
        
        if item['latitude'] == '':
            item['latitude'] = None
        
        if item['longitude'] == '':
            item['longitude'] = None

        if item['status'] == '1':
            status = 'active'
        else:
            status = 'retired'

        # Prepare data for the Site instance
        site_data = {
            'description': item['description'],
            'longitude': item['longitude'],
            'latitude': item['latitude'],
            'slug': slug_string(item['sitename'], ti),
            'status': status,
            'physical_address': address,
            'shipping_address': address,
        }

        # Update if exists, create if not
        site, created = Site.objects.update_or_create(
            name=item['sitename'],  # Field to match for finding the record
            defaults=site_data       # Fields to update or set if the object is created
        )

        if created:
            print(f"Created new site with name {item['sitename']}")
        else:
            print(f"Updated existing site with name {item['sitename']}")

def sync_sites():
    try:
        setting = SlurpitSetting.objects.get()
        uri_base = setting.server_url
        headers = {
                        'authorization': setting.api_key,
                        'useragent': f"{plugin_type}/requests",
                        'accept': 'application/json'
                    }
        uri_sites = f"{uri_base}/api/sites"
        r = requests.get(uri_sites, headers=headers, timeout=15, verify=False)
        data = r.json()

        # Import Slurpit Sites to NetBox
        create_sites(data)

        return data, ""
    except ObjectDoesNotExist as e:
        log_message = "Api key not configured in settings"
        return None, log_message
    except Exception as e:
        print(e)
        log_message = "Please confirm the Slurp'it server is running and reachable."
        return None, log_message

def import_devices(devices):
    to_insert = []
    for device in devices:
        # if device.get('disabled') == '1':
        #     continue
        if not isinstance(device, dict):
            continue
        if device.get('device_type') is None:
            continue
        device['slurpit_id'] = device.pop('id')
        
        try:
            device['created'] = timezone.make_aware(datetime.strptime(device['createddate'], '%Y-%m-%d %H:%M:%S'), timezone.get_current_timezone())
            device['last_updated'] = timezone.make_aware(datetime.strptime(device['changeddate'], '%Y-%m-%d %H:%M:%S'), timezone.get_current_timezone())          
        except ValueError:
            continue
        to_insert.append(SlurpitStagedDevice(**{( "ipv4" if key == "address" else key ): value for key, value in device.items() if key in columns or key == "address"}))
    SlurpitStagedDevice.objects.bulk_create(to_insert)
    

def process_import(delete=True):
    if delete:
        handle_parted()
    handle_changed()
    handle_new_comers()
    
def run_import():
    devices = get_devices()
    if devices is not None:
        start_device_import()
        import_devices(devices)
        process_import()
        return 'done'
    else:
        return 'none'


def handle_parted():
    parted_qs = SlurpitImportedDevice.objects.exclude(
        slurpit_id__in=SlurpitStagedDevice.objects.values('slurpit_id')
    )
    
    count = 0
    for device in parted_qs:
        if device.mapped_device is None:
            device.delete()
        # elif device.mapped_device.status == status_offline():
        #     continue
        # else:
        #     device.mapped_device.status=status_offline()
        #     device.mapped_device.save()
        count += 1
    

def handle_new_comers():
    unattended = get_config('unattended_import')
    
    qs = SlurpitStagedDevice.objects.exclude(
        slurpit_id__in=SlurpitImportedDevice.objects.values('slurpit_id')
    )

    offset = 0
    count = len(qs)

    while offset < count:
        batch_qs = qs[offset:offset + BATCH_SIZE]
        to_import = []        
        for device in batch_qs:
            to_import.append(get_from_staged(device, unattended))
        SlurpitImportedDevice.objects.bulk_create(to_import, ignore_conflicts=True)
        offset += BATCH_SIZE

    
def handle_changed():
    latest_changed_subquery = SlurpitImportedDevice.objects.filter(
        slurpit_id=OuterRef('slurpit_id')
    ).order_by('-last_updated').values('last_updated')[:1]
    qs = SlurpitStagedDevice.objects.annotate(
        latest_changed=Subquery(latest_changed_subquery)
    ).filter(
        last_updated__gt=F('latest_changed')
    )
    offset = 0
    count = len(qs)

    while offset < count:
        batch_qs = qs[offset:offset + BATCH_SIZE]
        to_import = []        
        for device in batch_qs:
            result = SlurpitImportedDevice.objects.get(slurpit_id=device.slurpit_id)
            result.copy_staged_values(device)
            
            result.save()
            get_create_dcim_objects(device)
            if result.mapped_device:
                if device.disabled == True:
                    if result.mapped_device.status != status_offline():
                        result.mapped_device.status=status_offline()
                # else:
                #     if result.mapped_device.status==status_offline():
                #         result.mapped_device.status=status_active()

                if device.serial:
                    result.mapped_device.serial = device.serial
                set_device_custom_fields(result.mapped_device, {
                    'slurpit_hostname': device.hostname,
                    'slurpit_fqdn': device.fqdn,
                    'slurpit_ipv4':  getattr(device, "ipv4", None) or getattr(device, "address", None),
                    'slurpit_serial': device.serial,
                    'slurpit_os_version': device.os_version,
                    'slurpit_snmp_uptime': device.snmp_uptime
                })   
                
                _mgmt_ip = getattr(device, "ipv4", None) or getattr(device, "address", None)
                if _mgmt_ip:
                    #### Remove Primary IPv4 on other device
                    other_device = Device.objects.filter(primary_ip4__address__net_host=_mgmt_ip).exclude(id=result.mapped_device.id).first()
                    if other_device:
                        other_device.primary_ip4 = None
                        other_device.save()

                    ipaddress = get_ip_device(_mgmt_ip, result.mapped_device)
                    if result.mapped_device.primary_ip4 != ipaddress:
                        result.mapped_device.primary_ip4 = ipaddress

                result.mapped_device.name = device.hostname

                result.mapped_device.save()
        offset += BATCH_SIZE

def import_from_queryset(qs: QuerySet, **extra):
    count = len(qs)
    offset = 0

    while offset < count:
        batch_qs = qs[offset:offset + BATCH_SIZE]
        to_import = []        
        for device in batch_qs:
            device.mapped_device = get_dcim_device(device, **extra)
            to_import.append(device)
        SlurpitImportedDevice.objects.bulk_update(to_import, fields={'mapped_device_id'})
        offset += BATCH_SIZE



def get_ip_device(ipv4: str, device: Device):
    update_ip = False
    prefix = Prefix.objects.filter(prefix__net_contains=ipv4).order_by('-prefix').first()
    if prefix:                            
        address = f'{ipv4}/{prefix.prefix.prefixlen}'
    else:
        address = f'{ipv4}/32'
    ipaddress = IPAddress.objects.filter(address__net_host=ipv4)
    if ipaddress:
        ipaddress = ipaddress.first()
        if ipaddress.address != address:
            ipaddress.address = address
            update_ip = True
    else:
        ipaddress = IPAddress.objects.create(address=address, status='active')  

    content_type = ContentType.objects.get_for_model(Interface)

    if ipaddress.assigned_object_type != content_type or ipaddress.assigned_object.device != device:
        interface = Interface.objects.filter(device=device, name='management1')
        if interface:
            ipaddress.assigned_object = interface.first()
        else:
            ipaddress.assigned_object = Interface.objects.create(name='management1', device=device, type='other')
        update_ip = True
    if update_ip:
        ipaddress.save()

    return ipaddress

def get_dcim_device(staged: SlurpitStagedDevice | SlurpitImportedDevice, **extra) -> Device:
    kw = get_default_objects()
    cf = extra.pop(custom_field_data_name, {})
    interface_name = extra.pop('interface_name', 'management1')

    cf.update({
        'slurpit_hostname': staged.hostname,
        'slurpit_fqdn': staged.fqdn,
        'slurpit_platform': staged.device_os,
        'slurpit_manufacturer': staged.brand,
        'slurpit_devicetype': staged.device_type,
        'slurpit_ipv4': getattr(staged, "ipv4", None) or getattr(staged, "address", None),
        'slurpit_site': staged.site,
        'slurpit_serial': staged.serial,
        'slurpit_os_version': staged.os_version,
        'slurpit_snmp_uptime': staged.snmp_uptime
    })    

    try:
        platform = Platform.objects.get(name=staged.device_os)
    except:
        platform = Platform.objects.get(slug=slugify(staged.device_os))
    
    devicetype = None
    if 'device_type' in extra:
        devicetype = extra['device_type']
        staged.mapped_devicetype = extra['device_type']
        staged.save()

    elif 'device_type' not in extra and staged.mapped_devicetype is not None:
        devicetype = staged.mapped_devicetype
    
    if devicetype:
        platform = devicetype.default_platform
        
    kw.update({
        'name': staged.hostname,
        'platform': platform,
        custom_field_data_name: cf,
        **extra,
        # 'primary_ip4_id': int(ip_address(staged.fqdn)),
    })
    if staged.serial:
        kw['serial'] = staged.serial
    if 'device_type' not in extra and staged.mapped_devicetype is not None:
        kw['device_type'] = staged.mapped_devicetype
        
    if staged.disabled == True:
        kw.setdefault('status', status_offline())
    # else:
    #     kw.setdefault('status', status_active())
    
    device = Device.objects.filter(name=staged.hostname)

    if device:
        device = device.first()
        device.update(**kw)
    else:
        device = Device.objects.create(**kw)
    ensure_slurpit_tags(device)

    _mgmt_ip = getattr(staged, "ipv4", None) or getattr(staged, "address", None)
    #Interface for new device.
    if _mgmt_ip:
        #### Remove Primary IPv4 on other device
        other_device = Device.objects.filter(primary_ip4__address__net_host=_mgmt_ip).exclude(id=device.id).first()
        if other_device:
            other_device.primary_ip4 = None
            other_device.save()
            
        ipaddress = get_ip_device(_mgmt_ip, device)            
        device.primary_ip4 = ipaddress
        device.save()
    
    return device

def get_from_staged(
        staged: SlurpitStagedDevice,
        add_dcim: bool
) -> SlurpitImportedDevice:
    device = SlurpitImportedDevice()
    device.copy_staged_values(staged)

    device.mapped_devicetype = get_create_dcim_objects(staged)
    if add_dcim:
        extra = {'device_type': device.mapped_devicetype} if device.mapped_devicetype else {}
        device.mapped_device = get_dcim_device(staged, **extra)
    return device


    
def get_latest_data_on_planning(hostname, planning_id):
    try:
        setting = SlurpitSetting.objects.get()
        uri_base = setting.server_url
        headers = {
                        'authorization': setting.api_key,
                        'useragent': f"{plugin_type}/requests",
                        'accept': 'application/json'
                    }
        uri_devices = f"{uri_base}/api/devices/snapshot/single/{hostname}/{planning_id}"

        r = requests.get(uri_devices, headers=headers, timeout=15, verify=False)
        # r.raise_for_status()
        if r.status_code != 200:
            return None

        data = r.json()
        log_message = f"Get the latest data from Slurp'it in {plugin_type.capitalize()} on planning ID."
        return data
    except ObjectDoesNotExist:
        setting = None
        log_message = "Need to set the setting parameter"
        return None

def import_plannings(plannings, delete=True):
    ids = {str(row['id']) : row for row in plannings if row['disabled'] == '0'}

    with transaction.atomic():
        if delete:
            count = SlurpitPlanning.objects.exclude(planning_id__in=ids.keys()).delete()[0]
            SlurpitSnapshot.objects.filter(planning_id__in=ids.keys()).delete()
            
        update_objects = SlurpitPlanning.objects.filter(planning_id__in=ids.keys())
        for planning in update_objects:
            obj = ids.pop(str(planning.planning_id))
            planning.name = obj['name']
            planning.comments = obj['comment']
            planning.save()
        
        to_save = []
        for obj in ids.values():
            to_save.append(SlurpitPlanning(name=obj['name'], comments=obj['comment'], planning_id=obj['id']))
        SlurpitPlanning.objects.bulk_create(to_save)
        