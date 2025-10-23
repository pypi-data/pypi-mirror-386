import requests

from django.contrib import messages
from django.contrib.contenttypes.fields import GenericRel
from django.core.exceptions import FieldDoesNotExist, ValidationError, ObjectDoesNotExist
from django.db import transaction, connection
from django.db.models import ManyToManyField, ManyToManyRel, F, Q, Func
from django.db.models.fields.json import KeyTextTransform
from django.utils.decorators import method_decorator
from django.http import HttpResponse, JsonResponse
from django.shortcuts import redirect, render
from django.urls import reverse
from django.views import View
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
from django.utils.text import slugify

from .. import get_config, forms, importer, models, tables
from ..models import SlurpitImportedDevice, SlurpitSetting
from ..management.choices import *
from ..importer import get_dcim_device, import_from_queryset, run_import, get_devices, BATCH_SIZE, import_devices, process_import, start_device_import, sync_sites, get_ip_device
from ..decorators import slurpit_plugin_registered
from ..references import base_name, custom_field_data_name
from ..references.generic import create_form, get_form_device_data, SlurpitViewMixim, get_default_objects, set_device_custom_fields, status_inventory, get_create_dcim_objects, status_active
from ..references.imports import * 
from ..filtersets import SlurpitImportedDeviceFilterSet
from dcim.models import DeviceType, Interface
from ipam.models import IPAddress, Prefix
from django.db.models.functions import Cast, Substr

class TrimCIDR(Func):
    function = 'substring'
    template = "%(function)s(%(expressions)s FROM 1 FOR POSITION('/' IN %(expressions)s) - 1)"


@method_decorator(slurpit_plugin_registered, name='dispatch')
class SlurpitImportedDeviceListView(SlurpitViewMixim, generic.ObjectListView):
    conflicted_queryset = models.SlurpitImportedDevice.objects.filter(
        mapped_device_id__isnull=True
    ).filter(
        Q(hostname__lower__in=Device.objects.values('name__lower')) |
        Q(ipv4__in=Device.objects.annotate(
            primary_ip4_trimmed=TrimCIDR(Cast(F('primary_ip4__address'), output_field=models.CharField()))
        ).filter(
           Q(primary_ip4__address__regex=r'/32$')
        ).values('primary_ip4_trimmed'))
    )
    to_onboard_queryset = models.SlurpitImportedDevice.objects.filter(mapped_device_id__isnull=True).exclude(pk__in=conflicted_queryset.values('pk'))
    onboarded_queryset = models.SlurpitImportedDevice.objects.filter(mapped_device_id__isnull=False)
    migrate_queryset = models.SlurpitImportedDevice.objects.filter(
                mapped_device_id__isnull=False
            ).annotate(
                slurpit_devicetype=KeyTextTransform('slurpit_devicetype', 'mapped_device__' + custom_field_data_name),
                slurpit_hostname=KeyTextTransform('slurpit_hostname', 'mapped_device__' + custom_field_data_name),
                slurpit_fqdn=KeyTextTransform('slurpit_fqdn', 'mapped_device__' + custom_field_data_name),
                slurpit_platform=KeyTextTransform('slurpit_platform', 'mapped_device__' + custom_field_data_name),
                slurpit_manufacturer=KeyTextTransform('slurpit_manufacturer', 'mapped_device__' + custom_field_data_name),
                slurpit_ipv4=KeyTextTransform('slurpit_ipv4', 'mapped_device__' + custom_field_data_name),
                slurpit_site=KeyTextTransform('slurpit_site', 'mapped_device__' + custom_field_data_name),
                fdevicetype=F('device_type'),
                fhostname=F('hostname'),
                ffqdn=F('fqdn'),
                fipv4=F('ipv4'),
                fdeviceos=F('device_os'),
                fbrand=F('brand'),
                fsite=F('site')
            ).exclude(
                Q(slurpit_devicetype=F('fdevicetype')) & 
                Q(slurpit_hostname=F('fhostname')) & 
                Q(slurpit_fqdn=F('ffqdn')) & 
                Q(slurpit_platform=F('fdeviceos')) & 
                Q(slurpit_manufacturer=F('fbrand')) &
                Q(slurpit_ipv4=F('fipv4')) &
                Q(slurpit_site=F('fsite'))
            )
    
    queryset = to_onboard_queryset
    action_buttons = []
    table = tables.SlurpitImportedDeviceTable
    template_name = f"{base_name}/onboard_device.html"
    filterset = SlurpitImportedDeviceFilterSet
    
    def get(self, request, *args, **kwargs):        
        self.queryset = self.to_onboard_queryset

        if request.GET.get('tab') == "migrate":
            self.queryset = self.migrate_queryset
            self.table = tables.MigratedDeviceTable
        elif request.GET.get('tab') == "conflicted":
            self.queryset = self.conflicted_queryset
            self.table = tables.ConflictDeviceTable
        elif request.GET.get('tab') == "onboarded":
            self.queryset = self.onboarded_queryset
            self.table = tables.SlurpitOnboardedDeviceTable
            
        return super().get(request, *args, **kwargs)
    
    def post(self, request):
        if request.POST.get('_all'):
            qs = self.queryset
        else:
            pks = map(int, request.POST.getlist('pk'))
            qs = self.queryset.filter(pk__in=pks, mapped_device_id__isnull=True)
        import_from_queryset(qs)
        return redirect(request.path)

    def slurpit_extra_context(self):
        appliance_type = ''
        connection_status = ''
        try:
            setting = SlurpitSetting.objects.get()
            server_url = setting.server_url
            api_key = setting.api_key
            appliance_type = setting.appliance_type
            connection_status = setting.connection_status
        except ObjectDoesNotExist:
            setting = None

        return {
            'to_onboard_count': self.to_onboard_queryset.count(),
            'onboarded_count': self.onboarded_queryset.count(),
            'migrate_count': self.migrate_queryset.count(),
            'conflicted_count': self.conflicted_queryset.count(),
            'appliance_type': appliance_type,
            'connection_status': connection_status,
            **self.slurpit_data
        }


@method_decorator(slurpit_plugin_registered, name='dispatch')
class SlurpitImportedDeviceOnboardView(SlurpitViewMixim, generic.BulkEditView):
    template_name = f"{base_name}/bulk_edit.html"
    queryset = models.SlurpitImportedDevice.objects.all()
    table = tables.SlurpitImportedDeviceTable
    model_form = forms.OnboardingForm
    form = forms.OnboardingForm
    filterset = SlurpitImportedDeviceFilterSet

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['models_queryset'] = self.queryset
        return kwargs

    def post(self, request, **kwargs):
        model = self.queryset.model

        if request.POST.get('_all') and self.filterset is not None:
            pk_list = self.filterset(request.GET, self.queryset.values_list('pk', flat=True), request=request).qs
            self.queryset = models.SlurpitImportedDevice.objects.all()
        else:
            pk_list = request.POST.getlist('pk')
            self.queryset = models.SlurpitImportedDevice.objects.filter(pk__in=pk_list)

        # Remove
        if 'remove' in request.GET:
            if len(pk_list) == 0:
                messages.warning(request, "No {} were selected.".format(model._meta.verbose_name_plural))
                log_message = "Failed to remove since no devices were selected."
                
            else:
                if 'onboarded' in request.GET:
                    for onboarded_item in self.queryset:
                        cf = onboarded_item.mapped_device.custom_field_data
                        cf.pop('slurpit_hostname')
                        cf.pop('slurpit_fqdn')
                        cf.pop('slurpit_platform')
                        cf.pop('slurpit_manufacturer')
                        cf.pop('slurpit_devicetype')
                        cf.pop('slurpit_ipv4')
                        cf.pop('slurpit_site')
                        onboarded_item.mapped_device.custom_field_data = cf
                        onboarded_item.mapped_device.save()
                self.queryset.delete()
                msg = f'Removed {len(pk_list)} {model._meta.verbose_name_plural}'
                messages.success(self.request, msg)
            return redirect(self.get_return_url(request))

        device_types = list(self.queryset.values_list('device_type').distinct())
        sites = list(self.queryset.values_list('site').distinct())

        form = create_form(self.form, request.POST, models.SlurpitImportedDevice, {'pk': pk_list, 'device_types': device_types, 'sites': sites})
        restrict_form_fields(form, request.user)

        if '_apply' in request.POST:
            if form.is_valid():
                try:
                    with transaction.atomic():
                        updated_objects, status, error, obj_name = self._update_objects(form, request)
                        
                        if status == "fail":
                            msg = f'{error[0:-1]} at {obj_name}.'
                            messages.error(self.request, msg)
                            return redirect(self.get_return_url(request))
                        if updated_objects:
                            msg = f'Onboarded {len(updated_objects)} {model._meta.verbose_name_plural}'
                            messages.success(self.request, msg)

                    return redirect(self.get_return_url(request))

                except ValidationError as e:
                    messages.error(self.request, ", ".join(e.messages))
                    # clear_webhooks.send(sender=self)
                    return JsonResponse({"status": "error", "error": str(e)})
                except Exception as e:
                    messages.error(self.request, str(e))
                    form.add_error(None, str(e))
                    # clear_webhooks.send(sender=self)
                    return JsonResponse({"status": "Error", "error": str(e)})
            return JsonResponse({"status": "error", "error": "validation error"})  
        
        elif 'migrate' in request.GET:
            migrate = request.GET.get('migrate')
            if migrate == 'create':                
                for obj in self.queryset:
                    device = obj.mapped_device
                    obj.mapped_device = None
                    obj.save()
                    device.delete() #delete last to prevent cascade delete
            elif migrate == 'update_slurpit':
                for obj in self.queryset:
                    device = obj.mapped_device
                    device.name = obj.hostname
                    
                    if obj.serial:
                        device.serial = obj.serial
                        
                    set_device_custom_fields(device, {
                        'slurpit_hostname': obj.hostname,
                        'slurpit_fqdn': obj.fqdn,
                        'slurpit_platform': obj.device_os,
                        'slurpit_manufacturer': obj.brand,
                        'slurpit_devicetype': obj.device_type,
                        'slurpit_ipv4': getattr(obj, "ipv4", None) or getattr(obj, "address", None),
                        'slurpit_site': obj.site,
                        'slurpit_serial': obj.serial,
                        'slurpit_os_version': obj.os_version,
                        'slurpit_snmp_uptime': obj.snmp_uptime
                    })    

                    # Update Site           
                    defaults = get_default_objects()
                    site = defaults['site']
                    if obj.site is not None and obj.site != "":
                        site = Site.objects.get(name=obj.site)
                        device.site = site

                    device.save()

                msg = f'Migration is done successfully.'
                messages.success(self.request, msg)

                return redirect(self.get_return_url(request))
            else:
                for obj in self.queryset:
                    device = obj.mapped_device
                    device.name = obj.hostname
                    
                    if obj.serial:
                        device.serial = obj.serial
                    set_device_custom_fields(device, {
                        'slurpit_hostname': obj.hostname,
                        'slurpit_fqdn': obj.fqdn,
                        'slurpit_platform': obj.device_os,
                        'slurpit_manufacturer': obj.brand,
                        'slurpit_devicetype': obj.device_type,
                        'slurpit_ipv4': getattr(obj, "ipv4", None) or getattr(obj, "address", None),
                        'slurpit_site': obj.site,
                        'slurpit_serial': obj.serial,
                        'slurpit_os_version': obj.os_version,
                        'slurpit_snmp_uptime': obj.snmp_uptime
                    })               

                    # Update Site           
                    defaults = get_default_objects()
                    site = defaults['site']
                    if obj.site is not None and obj.site != "":
                        site = Site.objects.get(name=obj.site)
                        device.site = site

                    device.device_type = get_create_dcim_objects(obj)
                    
                    try:
                        device.platform = Platform.objects.get(name=obj.device_os)
                    except:
                        device.platform = Platform.objects.get(slug=slugify(obj.device_os))

                    if device.device_type:
                        device.platform = device.device_type.default_platform
                    
                    device.save()
                    obj.save()

                    # Interface
                    _mgmt_ip = getattr(obj, "ipv4", None) or getattr(obj, "address", None)
                    if _mgmt_ip:
                        #### Remove Primary IPv4 on other device
                        other_device = Device.objects.filter(primary_ip4__address__net_host=_mgmt_ip).exclude(id=device.id).first()
                        if other_device:
                            other_device.primary_ip4 = None
                            other_device.save()

                        ipaddress = get_ip_device(_mgmt_ip, device)
                        if device.primary_ip4 != ipaddress:
                            device.primary_ip4 = ipaddress
                            device.save()

                    
                msg = f'Migration is done successfully.'
                messages.success(self.request, msg)

                return redirect(self.get_return_url(request))

        elif 'conflicted' in request.GET:
            conflic = request.GET.get('conflicted')
            if conflic == 'create':
                Device.objects.filter(name__lower__in=self.queryset.values('hostname__lower')).delete()

                for ipv4 in self.queryset.values_list('ipv4', flat=True).distinct():
                    if ipv4 is None:
                        continue
                    Device.objects.filter(primary_ip4__address__net_host=ipv4).delete()

            elif conflic == 'update_slurpit':
                for obj in self.queryset:
                    device = Device.objects.filter(name__iexact=obj.hostname).first()
                    # Management IP Case
                    if device is None:
                        _mgmt_ip = getattr(obj, "ipv4", None) or getattr(obj, "address", None)
                        if _mgmt_ip:
                            device = Device.objects.filter(primary_ip4__address__net_host=_mgmt_ip).first()

                    if obj.serial:
                        device.serial = obj.serial
                    
                    _mgmt_ip = getattr(obj, "ipv4", None) or getattr(obj, "address", None)
                    set_device_custom_fields(device, {
                        'slurpit_hostname': obj.hostname,
                        'slurpit_fqdn': obj.fqdn,
                        'slurpit_platform': obj.device_os,
                        'slurpit_manufacturer': obj.brand,
                        'slurpit_devicetype': obj.device_type,
                        'slurpit_ipv4': _mgmt_ip,
                        'slurpit_site': obj.site,
                        'slurpit_serial': obj.serial,
                        'slurpit_os_version': obj.os_version,
                        'slurpit_snmp_uptime': obj.snmp_uptime
                    })     
                    other_imported_device = SlurpitImportedDevice.objects.filter(mapped_device=device).first()
                    if other_imported_device:
                        other_imported_device.delete()

                    obj.mapped_device = device
                    
                    # Update Site           
                    defaults = get_default_objects()
                    site = defaults['site']
                    if obj.site is not None and obj.site != "":
                        site = Site.objects.get(name=obj.site)
                        device.site = site

                    device.save()
                    obj.save()

                    
                msg = f'Conflicts successfully resolved.'
                messages.success(self.request, msg)

                return redirect(self.get_return_url(request))
            else:
                for obj in self.queryset:
                    device = None
                    
                    _mgmt_ip = getattr(obj, "ipv4", None) or getattr(obj, "address", None)
                    if _mgmt_ip:
                        device = Device.objects.filter(primary_ip4__address__net_host=_mgmt_ip).first()

                    if device is None: # Name Case
                        device = Device.objects.filter(name__iexact=obj.hostname).first()
                    else:
                        if device.name != obj.hostname:
                            other_device = Device.objects.filter(name__iexact=obj.hostname).first()
                            if other_device:
                                other_device.delete()
                            
                            device.name = obj.hostname
                    
                    if obj.serial:
                        device.serial = obj.serial
                    set_device_custom_fields(device, {
                        'slurpit_hostname': obj.hostname,
                        'slurpit_fqdn': obj.fqdn,
                        'slurpit_platform': obj.device_os,
                        'slurpit_manufacturer': obj.brand,
                        'slurpit_devicetype': obj.device_type,
                        'slurpit_ipv4': getattr(obj, "ipv4", None) or getattr(obj, "address", None),
                        'slurpit_site': obj.site,
                        'slurpit_serial': obj.serial,
                        'slurpit_os_version': obj.os_version,
                        'slurpit_snmp_uptime': obj.snmp_uptime
                    })    
                      
                    other_imported_device = SlurpitImportedDevice.objects.filter(mapped_device=device).first()
                    if other_imported_device:
                        other_imported_device.delete()

                    obj.mapped_device = device    

                    device.device_type = get_create_dcim_objects(obj)

                    try:
                        device.platform = Platform.objects.get(name=obj.device_os)
                    except:
                        device.platform = Platform.objects.get(slug=slugify(obj.device_os))
                    
                    if device.device_type:
                        device.platform = device.device_type.default_platform

                    # Update Site           
                    defaults = get_default_objects()
                    site = defaults['site']
                    if obj.site is not None and obj.site != "":
                        site = Site.objects.get(name=obj.site)
                        device.site = site

                    device.save()
                    obj.save()

                    # Interface
                    _mgmt_ip = getattr(obj, "ipv4", None) or getattr(obj, "address", None)
                    if _mgmt_ip:
                        #### Remove Primary IPv4 on other device
                        other_device = Device.objects.filter(primary_ip4__address__net_host=_mgmt_ip).exclude(id=device.id).first()
                        if other_device:
                            other_device.primary_ip4 = None
                            other_device.save()

                        ipaddress = get_ip_device(_mgmt_ip, device)
                        if device.primary_ip4 != ipaddress:
                            device.primary_ip4 = ipaddress
                            device.save()

                    
                msg = f'Conflicts successfully resolved.'
                messages.success(self.request, msg)

                return redirect(self.get_return_url(request))
        
        initial_data = {'pk': pk_list, 'device_types': device_types, 'sites': sites}
        for k, v in get_default_objects().items():
            initial_data.setdefault(k, str(v.id))
        initial_data.setdefault('status', status_active())

        if request.POST.get('_all'):
            initial_data['_all'] = 'on'

        if len(device_types) > 1:
            initial_data['device_type'] = 'keep_original'
        if len(device_types) == 1 and (dt := DeviceType.objects.filter(model__iexact=device_types[0][0]).first()):
            initial_data['device_type'] = dt.id
        
        if len(sites) > 1:
            initial_data['site'] = 'keep_original'
        
        if len(sites) == 1 and (site := Site.objects.filter(name=sites[0][0]).first()):
            initial_data['site'] = site.id

        form = create_form(self.form, None, models.SlurpitImportedDevice, initial_data)
        restrict_form_fields(form, request.user)
                
        # Retrieve objects being edited
        table = self.table(self.queryset.filter(mapped_device_id__isnull=True), orderable=False)
        if not table.rows:
            messages.warning(request, "No {} were selected.".format(model._meta.verbose_name_plural))
            return redirect(self.get_return_url(request))

        return render(request, self.template_name, {
            'model': model,
            'form': form,
            'table': table,
            'obj_type_plural': self.queryset.model._meta.verbose_name_plural,
            'return_url': self.get_return_url(request),
            **self.slurpit_data
        })

    def _update_objects(self, form, request):
        device_type = None
        if form.cleaned_data['device_type'] != 'keep_original':
            device_type = DeviceType.objects.filter(id=form.cleaned_data['device_type']).first()

        site = None
        if form.cleaned_data['site'] != 'keep_original':
            site = Site.objects.filter(id=form.cleaned_data['site']).first()

        updated_objects = []
        data = get_form_device_data(form)

        objs = self.queryset.filter(pk__in=form.cleaned_data['pk'])
        
        for obj in objs:
            if obj.mapped_device_id is not None:
                continue

            dt = device_type
            if not device_type:
                dt = obj.mapped_devicetype
            
            item_site = site
            if not item_site:
                if obj.site is None or obj.site == "":
                    defaults = get_default_objects()
                    item_site = defaults['site']
                else:
                    item_site = Site.objects.get(name=obj.site)
            try:
                device = get_dcim_device(obj, device_type=dt, site=item_site, **data)
                obj.mapped_device = device
                obj.save()
                updated_objects.append(obj)
            except Exception as e:
                return [], "fail", str(e), obj.hostname
            # Take a snapshot of change-logged models
            if hasattr(device, 'snapshot'):
                device.snapshot()
            
            if form.cleaned_data.get('add_tags', None):
                device.tags.add(*form.cleaned_data['add_tags'])
            if form.cleaned_data.get('remove_tags', None):
                device.tags.remove(*form.cleaned_data['remove_tags'])

        return updated_objects, "success", "", ""


@method_decorator(slurpit_plugin_registered, name='dispatch')
class ImportDevices(View):
    def get(self, request, *args, **kwargs):
        offset = request.GET.get("offset", None)
        try:
            if offset is not None:
                offset = int(offset)
                if offset == 0:
                    sync_sites()
                    
                    start_device_import()
                devices, log_message = get_devices(offset)
                if devices is not None and len(devices) > 0:
                    import_devices(devices)
                    offset += len(devices)
                if devices is None:
                    messages.error(request, "Please confirm the Slurp'it server is running and reachable.")
                    # return HttpResponseRedirect(reverse("plugins:slurpit_netbox:onboard"))
                    return JsonResponse({"action": "error", "error": "ERROR"})
                return JsonResponse({"action": "import", "offset": offset})
            
            process_import()
            messages.info(request, "Synced the devices from Slurp'it.")
            return JsonResponse({"action": "process"})
        except requests.exceptions.RequestException as e:
            messages.error(request, "An error occured during querying Slurp'it!")
            
        return JsonResponse({"action": "", "error": "ERROR"})
    

