import requests
from datetime import datetime

from django.contrib import messages
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.core.exceptions import ObjectDoesNotExist
from django.core.cache import cache
from django.conf import settings
from django.views.generic import View
from django.utils.decorators import method_decorator
from django_tables2 import RequestConfig, tables, Column
from django.urls import reverse

from netbox.views import generic
from netbox.views.generic.base import BaseObjectView
from users.models import Token
from account.models import UserToken
from dcim.models import Device
from dcim.views import DeviceComponentsView
from utilities.htmx import htmx_partial
from utilities.views import register_model_view, ViewTab
from utilities.paginator import EnhancedPaginator, get_paginate_count

from ..forms import SlurpitPlanningTableForm, SlurpitApplianceTypeForm
from ..models import (
    create_default_data_mapping, SlurpitSetting, SlurpitPlanning, 
    SlurpitSnapshot, SlurpitImportedDevice, SlurpitStagedDevice, 
    SlurpitInitIPAddress, SlurpitInterface, SlurpitPrefix, SlurpitVLAN
)
from ..tables import SlurpitPlanningTable
from ..management.choices import *
from ..decorators import slurpit_plugin_registered
from ..utilities import generate_random_string
from ..importer import get_latest_data_on_planning, import_plannings
from requests.packages.urllib3.exceptions import InsecureRequestWarning
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

from json import JSONEncoder
import json

class OrderedEncoder(JSONEncoder):
    def encode(self, o):
        if isinstance(o, dict):
            return "{" + ", ".join(f'{self.encode(k)}: {self.encode(v)}' for k, v in o.items()) + "}"
        return super().encode(o)
    
BATCH_SIZE = 128

@method_decorator(slurpit_plugin_registered, name='dispatch')
class SettingsView(View):
    
    app_label = "dcim"
    model_name = "device"
    
    def get(self, request):
        reset_param = request.GET.get('reset', None)
        if reset_param:
            SlurpitImportedDevice.objects.all().delete()
            SlurpitStagedDevice.objects.all().delete()
            SlurpitSnapshot.objects.all().delete()
            SlurpitSetting.objects.all().delete()
            SlurpitPlanning.objects.all().delete()
            SlurpitInitIPAddress.objects.all().delete()
            SlurpitPrefix.objects.all().delete()
            SlurpitInterface.objects.all().delete()
            SlurpitVLAN.objects.all().delete()
            create_default_data_mapping()

            return HttpResponseRedirect(reverse("plugins:slurpit_netbox:settings"))
        
        appliance_type = ''
        try:
            setting = SlurpitSetting.objects.get()
            server_url = setting.server_url
            api_key = setting.api_key
            appliance_type = setting.appliance_type

        except Exception as e:
            setting = None
            
        push_api_key = ''
        
        connection_status = "" if setting is None else setting.connection_status 

        tokens = UserToken.objects.all().count()

        if tokens > 0:
            push_api_key = 'existed'
        
        tab_param = request.GET.get('tab', None)
        plannings = []
        slurpit_apis = []
        initial_data = {
            "appliance_type": appliance_type
        }

        form = SlurpitApplianceTypeForm(initial=initial_data)
        
        if tab_param == 'data_tabs':
            sync_param = request.GET.get('sync', None)
            if sync_param == 'true' and setting is not None:
                new_plannings = self.get_planning_list(request, server_url, api_key)
                if new_plannings is not None:
                    import_plannings(new_plannings)

            plannings = SlurpitPlanning.objects.all().order_by('id')
            
        else:   
            appliance_type_param = request.GET.get('appliance_type', None)

            if appliance_type_param:
                if setting is None:
                    setting = SlurpitSetting.objects.create()
                setting.appliance_type = appliance_type_param
                setting.save()

                return HttpResponseRedirect(reverse("plugins:slurpit_netbox:settings"))

            slurpit_apis = [
                {
                    "type": "POST",
                    "url": "api/plugins/slurpit/ipam/"
                },
                {
                    "type": "POST",
                    "url": "api/plugins/slurpit/interface/"
                },
                {
                    "type": "POST",
                    "url": "api/plugins/slurpit/prefix/"
                },
                {
                    "type": "GET",
                    "url": "api/plugins/slurpit/prefix/all/"
                },
                {
                    "type": "POST",
                    "url": "api/plugins/slurpit/device/"
                },
                {
                    "type": "POST",
                    "url": "api/plugins/slurpit/site/"
                },
                {
                    "type": "POST",
                    "url": "api/plugins/slurpit/device/sync_start/"
                },
                {
                    "type": "POST",
                    "url": "api/plugins/slurpit/device/sync/"
                },
                {
                    "type": "POST",
                    "url": "api/plugins/slurpit/device/sync_end/"
                },
                {
                    "type": "DELETE",
                    "url": "api/plugins/slurpit/device/delete/{hostname}/"
                },
                {
                    "type": "DELETE",
                    "url": "api/plugins/slurpit/device/delete-all/"
                },
                {
                    "type": "GET",
                    "url": "api/plugins/slurpit/test/api/"
                },
                {
                    "type": "GET",
                    "url": "api/plugins/slurpit/netbox-device/all/"
                }
            ]

            test_param = request.GET.get('test',None)
            if test_param =='test':
                if setting is None:
                    messages.warning(request, "You can not test. To use the Slurp'it plugin you should first configure the server settings. Go to settings and configure the Slurp'it server in the parameter section.")
                else:
                    connection_status = self.connection_test(request, server_url, api_key)
                    setting.connection_status = connection_status
                    setting.save()
                    
            action_param = request.GET.get('action',None)
            if action_param == 'generate':
                if setting is None:
                    setting = SlurpitSetting.objects.create()

                token, __annotations__ = Token.objects.get_or_create(user=request.user)
                push_api_key = Token.generate_key()
                token.key = push_api_key
                token.save()
                setting.push_api_key = push_api_key
                setting.save()

        debug = settings.DEBUG
        return render(
            request,
            "slurpit_netbox/settings.html",
            {
                "setting": setting, 
                "connection_status": connection_status,
                "push_api_key": push_api_key,
                "plannings": plannings,
                "slurpit_apis": slurpit_apis,
                "form": form,
                "appliance_type": appliance_type,
                "debug": debug,
            },
        )
    
    def post(self, request):
        return_url = request.GET.get('return_url', None)
        if return_url is None:
            id = request.POST.get('setting_id')
            server_url = request.POST.get('server_url')
            api_key = request.POST.get('api_key')
            if id == "":
                obj, created = SlurpitSetting.objects.get_or_create(id=0, defaults={'server_url': server_url, 'api_key': api_key})
            else:
                obj, created = SlurpitSetting.objects.get_or_create(id=id, defaults={'server_url': server_url, 'api_key': api_key})
            log_message = "Added the settings parameter successfully."

            connection_status = self.connection_test(request, server_url, api_key)
            obj.connection_status = connection_status

            if not created:
                obj.server_url = server_url
                obj.api_key = api_key
                log_message = "Updated the settings parameter successfully."
                messages.success(request, "Updated the settings parameter successfully.")
            obj.save()
            
        else:
            plans = request.POST.getlist('pk')
            total_planning_ids = []

            # Split id: 1#plan_name
            for plan in plans:
                plan_arr = plan.split('#')
                total_planning_ids.append(plan_arr[0])
                
            SlurpitPlanning.objects.filter(id__in=total_planning_ids).update(selected=True)
            SlurpitPlanning.objects.exclude(id__in=total_planning_ids).update(selected=False)

            return redirect(return_url)
        
        return redirect(request.path)


    def connection_test(self, request, server_url, api_key):
        headers = {
                    'authorization': api_key,
                    'useragent': 'netbox/requests',
                    'accept': 'application/json'
                }
        connection_test = f"{server_url}/api/platform/ping"
        try:
            response = requests.get(connection_test, headers=headers, timeout=15, verify=False)
            r = response.json()
        except Exception as e:
            messages.error(request, "Please confirm the Slurp'it server is running and reachable.")
            
            return "not connected"
        
        if response.status_code == 200:
            r = response.json()
            if r.get('status') == "up":
                messages.success(request, "Tested the connection to the Slurp'it server successfully.")
            return 'connected'
        else:
            messages.error(request, "Failed testing the connection to the Slurp'it server.")
            return "not connected"
    
    def get_planning_list(self, request, server_url, api_key):
        headers = {
                    'authorization': api_key,
                    'useragent': 'netbox/requests',
                    'accept': 'application/json'
                }
        try:
            response = requests.get(f"{server_url}/api/planning", headers=headers, timeout=15, verify=False)
        except Exception as e:
            messages.error(request, "Please confirm the Slurp'it server is running and reachable.")
            return []
        
        if response.status_code == 200:
            r = response.json()
            planning_list = []
            for plan in r:
                planning_list.append({
                    'id': plan['id'],
                    'name': plan['name'],
                    'comment': plan['comment'],
                    'disabled': plan['disabled']
                })
            
            return planning_list
        return None

def get_refresh_url(request, pk):
    get_params = request.GET.copy()
    get_params['refresh'] = 'none'
    get_params['sync'] = 'none'

    path = f"/dcim/devices/{pk}/Slurpit/"
    query_string = get_params.urlencode()
    url_no_refresh = f"{path}?{query_string}" if query_string else path

    return url_no_refresh

class SlurpitViewTab(ViewTab):
    def render(self, instance):
        device = get_object_or_404(Device, pk=instance.pk)
        if device and device.custom_field_data and 'slurpit_hostname' in device.custom_field_data:
            slurpit_hostname = device.custom_field_data['slurpit_hostname']
            if slurpit_hostname is None:
                return None
        else:
            return None
        """Return the attributes needed to render a tab in HTML."""
        badge_value = self._get_badge_value(instance)
        if self.badge and self.hide_if_empty and not badge_value:
            return None
        return {
            'label': self.label,
            'badge': badge_value,
            'weight': self.weight,
        }
    
@register_model_view(Device, "Slurpit")
class SlurpitPlanningning(View):
    template_name = "slurpit_netbox/planning_table.html"
    tab = SlurpitViewTab("Slurpit", permission="slurpit_netbox.view_devicetable")
    form = SlurpitPlanningTableForm()

    def get(self, request, pk):
        device = get_object_or_404(Device, pk=pk)
        
        connection_status = appliance_type = ''
        setting = None
        try:
            setting = SlurpitSetting.objects.get()
            appliance_type = setting.appliance_type
            connection_status = setting.connection_status
        except ObjectDoesNotExist:
            pass
        
        data = None
        cached_time = None
        result_status = "No Data"
        columns = []
        refresh = request.GET.get('refresh')
        sync = request.GET.get('sync')
        if 'planning_id' in request.GET and (planning := SlurpitPlanning.objects.filter(planning_id=request.GET.get('planning_id')).first()):
            self.form = SlurpitPlanningTableForm({'planning_id': planning.planning_id})
            self.form.id = planning.planning_id
            result_type = request.GET.get('result_type')
            
            if result_type is None:
                result_type = "planning"

            cache_key = f"slurpit_plan_{planning.planning_id}_{device.name}_{result_type}"

            url_no_refresh = get_refresh_url(request, pk)

            if sync == "sync":
                if appliance_type != "push":
                    sync_snapshot(cache_key, device.name, planning)
                
                return HttpResponseRedirect(url_no_refresh)
            
            if refresh == "refresh":
                if appliance_type != "push":
                    sync_snapshot(cache_key, device.name, planning)
                else:
                    cache.delete(cache_key)
                    
                return HttpResponseRedirect(url_no_refresh)

            cached_time, data = cache.get(cache_key, (None, None))
            if cached_time:
                result_status = "Cached"

            if data is None or len(data) == 0:
                data = []
                try: 
                    result_key = f"{result_type}_result"
                    temp = SlurpitSnapshot.objects.filter(hostname=device.name, planning_id=planning.planning_id, result_type=result_key)
                    # Empty case
                    if temp.count() == 0:
                        if appliance_type != "push":
                            sync_snapshot(cache_key, device.name, planning)
                        temp = SlurpitSnapshot.objects.filter(hostname=device.name, planning_id=planning.planning_id, result_type=result_key)
                    
                    for r in temp:
                        try:
                            r = json.loads(r.content)
                        except:
                            r = r.content
                        # raw = r[result_key]
                        data.append({**r})
                    result_status = "Live"
                    cache.set(cache_key, (datetime.now(), data), 60 * 60 * 8)
                    
                except Exception as e:
                    messages.error(request, e)

        if refresh == "refresh":
            url_no_refresh = get_refresh_url(request, pk)
            return HttpResponseRedirect(url_no_refresh)
        
        if not data:
            data = []
        
        if len(data) > 0:
            raw = data[0]
            columns = list(raw.keys())
        
        columns = [(k, Column()) for k in columns]
        table = SlurpitPlanningTable(data, extra_columns=columns)

        RequestConfig(
            request,
            {
                "paginator_class": EnhancedPaginator,
                "per_page": get_paginate_count(request),
            },
        ).configure(table)

        if htmx_partial(request):
            return render(
                request,
                "htmx/table.html",
                {
                    "table": table,
                },
            )

        return render(
            request,
            self.template_name,
            {
                "object": device,
                "tab": self.tab,
                "form": self.form,
                "table": table,
                "result_status": result_status,
                "cached_time": cached_time,
                "appliance_type": appliance_type,
                "connection_status": connection_status,
            },
        )

def sync_snapshot(cache_key, device_name, plan, test=False, data={}):
    if cache_key != "":
        cache.delete(cache_key)
    
    if test == False:
        data = get_latest_data_on_planning(device_name, plan.planning_id)
  
    if data is not None:
        temp = data[plan.name]["planning_results"]
        
        if temp is not None:
            count = SlurpitSnapshot.objects.filter(hostname=device_name, planning_id=plan.planning_id).delete()[0]
            
        new_items = []
        for item in temp:
            content = json.dumps(item, cls=OrderedEncoder)
            new_items.append(SlurpitSnapshot(hostname=device_name, planning_id=plan.planning_id, content=content, result_type="planning_result"))

        temp = data[plan.name]["template_results"]

        for item in temp:
            content = json.dumps(item, cls=OrderedEncoder)
            new_items.append(SlurpitSnapshot(hostname=device_name, planning_id=plan.planning_id, content=content, result_type="template_result"))
        
        SlurpitSnapshot.objects.bulk_create(new_items, batch_size=BATCH_SIZE, ignore_conflicts=True)