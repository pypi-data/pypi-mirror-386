import ipaddress
import django_tables2 as tables
from django.utils.safestring import mark_safe
from django.utils.html import escape
from django_tables2 import Column
from django_tables2.columns import BoundColumn
from django_tables2.columns.base import LinkTransform
from django_tables2.utils import Accessor
from django.utils.translation import gettext_lazy as _
from netbox.tables import NetBoxTable, ToggleColumn, columns
from dcim.models import  Device, Interface
from dcim.tables import BaseInterfaceTable
from .models import SlurpitImportedDevice, SlurpitInitIPAddress, SlurpitInterface, SlurpitPrefix, SlurpitVLAN
from tenancy.tables import TenancyColumnsMixin, TenantColumn
from ipam.models import IPAddress, Prefix, VLAN

def check_link(**kwargs):
    return {}

def greenText(value):
    return f'<span style="background-color:#d7ecd7; color: black">{value}</span>'

def greenLink(link):
    return f'<span class="greenLink" style="background-color:#d7ecd7; color: blue">{link}</span>'

class ImportColumn(BoundColumn):
    pass

AVAILABLE_LABEL = mark_safe('<span class="badge bg-success">Available</span>') #nosec

def importing(*args, **kwargs):
    raise Exception([args, kwargs])


class ConditionalToggle(ToggleColumn):
    def render(self, value, bound_column, record):
        if record.mapped_device_id is None or (
            record.mapped_device.custom_field_data['slurpit_devicetype'] != record.device_type or
            record.mapped_device.custom_field_data['slurpit_hostname'] != record.hostname or
            record.mapped_device.custom_field_data['slurpit_fqdn'] != record.fqdn or
            record.mapped_device.custom_field_data['slurpit_platform'] != record.device_os or 
            record.mapped_device.custom_field_data['slurpit_manufacturer'] != record.brand or
            record.mapped_device.custom_field_data['slurpit_site'] != record.site
        ):
            return super().render(value, bound_column, record)
        return super().render(value, bound_column, record)
        # return '✔'


class ConditionalLink(Column):
    def render(self, value, bound_column, record):
        if record.mapped_device_id is None:

            original_value = ""
            original_device = Device.objects.filter(name__iexact=record.hostname).first()
            _mgmt_ip = getattr(record, "ipv4", None) or getattr(record, "address", None)
            if original_device is None and _mgmt_ip:
                original_device = Device.objects.filter(primary_ip4__address__net_host=_mgmt_ip).first()

            if original_device:
                original_value = original_device.name

            if str(original_value) == str(value):
                return mark_safe(f'<span>{escape(value)}<br/>{escape(original_value)}</span>') #nosec 
            
            if original_device:
                return mark_safe(f'<span">{greenText(escape(value))}<br/>{escape(original_value)}</span>') #nosec 
            else:
                return value
    
            
        link = LinkTransform(attrs=self.attrs.get("a", {}), accessor=Accessor("mapped_device"))
        return link(value, value=value, record=record, bound_column=bound_column)

class ConflictedColumn(Column):
    def render(self, value, bound_column, record):            
        device = Device.objects.filter(name__iexact=record.hostname).first()
        if device is None:
            _mgmt_ip = getattr(record, "ipv4", None) or getattr(record, "address", None)
            if _mgmt_ip:
                device = Device.objects.filter(primary_ip4__address__net_host=_mgmt_ip).first()

        original_value = ""
        column_name = bound_column.verbose_name

        if device:
            if column_name == "Manufacturer":
                original_value = device.device_type.manufacturer
            elif column_name == "Platform":
                original_value = device.platform
            elif column_name == "FQDN":
                if "slurpit_fqdn" in device.custom_field_data:
                    original_value = device.custom_field_data['slurpit_fqdn']
            elif column_name == "IPv4":
                if device.primary_ip4:
                    original_value = str(device.primary_ip4.address)
                    original_value = original_value.split("/")[0]
            else:
                original_value = device.device_type

                if record.mapped_devicetype_id is not None:
                    link = LinkTransform(attrs=self.attrs.get("a", {}), accessor=Accessor("mapped_devicetype"))
                    if str(original_value) != str(value):
                        return mark_safe(f'{greenLink(link(escape(value), value=escape(value), record=record, bound_column=bound_column))}<br />{escape(original_value)}') #nosec 
        
        if str(original_value) == str(value):
            return mark_safe(f'<span>{escape(value)}<br/>{escape(original_value)}</span>') #nosec 
        return mark_safe(f'<span">{greenText(escape(value))}<br/>{escape(original_value)}</span>') #nosec 


class DeviceTypeColumn(Column):
    def render(self, value, bound_column, record):
        if record.mapped_devicetype_id is None:
            return value
        link = LinkTransform(attrs=self.attrs.get("a", {}), accessor=Accessor("mapped_devicetype"))
        return link(record.mapped_devicetype.model, value=record.mapped_devicetype.model, record=record, bound_column=bound_column)


class SlurpitImportedDeviceTable(NetBoxTable):
    actions = columns.ActionsColumn(actions=tuple())
    pk = ConditionalToggle()
    hostname = ConditionalLink()
    device_type = DeviceTypeColumn()

    brand = tables.Column(
        verbose_name = _('Manufacturer')
    )

    device_os = tables.Column(
        verbose_name = _('Platform')
    )

    ipv4 = tables.Column(
        verbose_name = _('IPv4')
    )

    site = tables.Column(
        verbose_name = _('Site')
    )

    last_updated = tables.Column(
        verbose_name = _('Last seen')
    )

    serial = tables.Column(
        verbose_name = _('Serialname')
    )
    
    os_version = tables.Column(
        verbose_name = _('Os Version')
    )
    
    snmp_uptime = tables.Column(
        verbose_name = _('Snmp Uptime')
    )

    class Meta(NetBoxTable.Meta):
        model = SlurpitImportedDevice
        fields = ('pk', 'id', 'hostname', 'fqdn','brand', 'IP', 'ipv4', 'device_os', 'site', 'device_type', "serial", "os_version", "snmp_uptime", 'last_updated')
        default_columns = ('hostname', 'fqdn', 'device_os', 'brand' , 'device_type', 'ipv4', 'site', "serial", "os_version", "snmp_uptime", 'last_updated')

class PlatformTypeColumn(Column):
    def render(self, value, bound_column, record):
        if record.mapped_device:
            return record.mapped_device.device_type.default_platform
        return "-"
    
class ManufactureColumn(Column):
    def render(self, value, bound_column, record):
        if record.mapped_device:
            return record.mapped_device.device_type.manufacturer
        return "-"


class SlurpitOnboardedDeviceTable(NetBoxTable):
    actions = columns.ActionsColumn(actions=tuple())
    pk = ConditionalToggle()
    hostname = ConditionalLink()
    device_type = DeviceTypeColumn()

    brand = ManufactureColumn(
        verbose_name = _('Manufacturer')
    )

    device_os = PlatformTypeColumn(verbose_name="Platform Type")

    ipv4 = tables.Column(
        verbose_name = _('IPv4')
    )

    site = tables.Column(
        verbose_name = _('Site')
    )

    last_updated = tables.Column(
        verbose_name = _('Last seen')
    )

    serial = tables.Column(
        verbose_name = _('Serialname')
    )
    
    os_version = tables.Column(
        verbose_name = _('Os Version')
    )
    
    snmp_uptime = tables.Column(
        verbose_name = _('Snmp Uptime')
    )

    class Meta(NetBoxTable.Meta):
        model = SlurpitImportedDevice
        fields = ('pk', 'id', 'hostname', 'fqdn','brand', 'IP', 'ipv4', 'device_os', 'device_type', 'site', "serial", "os_version", "snmp_uptime", 'last_updated')
        default_columns = ('hostname', 'fqdn', 'device_os', 'brand' , 'device_type', 'ipv4', 'site', "serial", "os_version", "snmp_uptime",'last_updated')

class ConflictDeviceTable(NetBoxTable):
    actions = columns.ActionsColumn(actions=tuple())
    pk = ConditionalToggle()
    hostname = ConditionalLink()
    device_type = ConflictedColumn()

    brand = ConflictedColumn(
        verbose_name = _('Manufacturer')
    )

    device_os = ConflictedColumn(
        verbose_name = _('Platform')
    )

    ipv4 = ConflictedColumn(
        verbose_name = _('IPv4')
    )

    fqdn = ConflictedColumn(
        verbose_name = _('FQDN')
    )

    last_updated = tables.Column(
        verbose_name = _('Last seen')
    )

    class Meta(NetBoxTable.Meta):
        model = SlurpitImportedDevice
        fields = ('pk', 'id', 'hostname', 'fqdn','brand', 'IP', 'device_os', 'device_type', 'ipv4', "serial", "os_version", "snmp_uptime", 'last_updated')
        default_columns = ('hostname', 'fqdn', 'device_os', 'brand' , 'device_type', 'ipv4', "serial", "os_version", "snmp_uptime", 'last_updated')


class MigratedDeviceTable(NetBoxTable):
    actions = columns.ActionsColumn(actions=tuple())
    pk = ConditionalToggle()
    hostname = ConditionalLink()
    device_type = DeviceTypeColumn()

    brand = tables.Column(
        verbose_name = _('Manufacturer')
    )

    device_os = tables.Column(
        verbose_name = _('Platform')
    )

    site = tables.Column(
        verbose_name = _('Site')
    )

    last_updated = tables.Column(
        verbose_name = _('Last seen')
    )

    serial = tables.Column(
        verbose_name = _('Serialname')
    )
    
    os_version = tables.Column(
        verbose_name = _('Os Version')
    )
    
    snmp_uptime = tables.Column(
        verbose_name = _('Snmp Uptime')
    )

    # slurpit_devicetype = tables.Column(
    #     accessor='slurpit_device_type', 
    #     verbose_name='Original Device Type'
    # )

    class Meta(NetBoxTable.Meta):
        model = SlurpitImportedDevice
        fields = ('pk', 'id', 'hostname', 'fqdn','brand', 'IP', 'device_os', 'device_type', 'site', "serial", "os_version", "snmp_uptime", 'last_updated')
        default_columns = ('hostname', 'fqdn', 'device_os', 'brand' , 'device_type', 'site', "serial", "os_version", "snmp_uptime", 'last_updated')

    def render_device_os(self, value, record):
        original_val = record.mapped_device.custom_field_data["slurpit_platform"]
        if str(value) == str(original_val):
            return mark_safe(f'<span">{escape(value)}<br/>{escape(original_val)}</span>') #nosec 
        
        return mark_safe(f'<span">{greenText(escape(value))}<br/>{escape(original_val)}</span>') #nosec
    
    def render_site(self, value, record):
        original_val = record.mapped_device.custom_field_data["slurpit_site"]
        if str(value) == str(original_val):
            return mark_safe(f'<span">{escape(value)}<br/>{escape(original_val)}</span>') #nosec 
        
        return mark_safe(f'<span">{greenText(escape(value))}<br/>{escape(original_val)}</span>') #nosec
    
    def render_brand(self, value, record):
        original_val = record.mapped_device.custom_field_data["slurpit_manufacturer"]
        if str(value) == str(original_val):
            return mark_safe(f'<span">{escape(value)}<br/>{escape(original_val)}</span>') #nosec 
        return mark_safe(f'<span">{greenText(escape(value))}<br/>{escape(original_val)}</span>') #nosec
    
    def render_device_type(self, value, bound_column, record):
        if record.mapped_devicetype_id is None:
            return value
        link = LinkTransform(attrs=self.attrs.get("a", {}), accessor=Accessor("mapped_devicetype"))

        original_val = record.mapped_device.custom_field_data["slurpit_devicetype"]
        if str(value) == str(original_val):
            return mark_safe(f'<span">{escape(value)}<br/>{escape(original_val)}</span>') #nosec 
        return mark_safe(f'<span>{greenLink(link(escape(value), value=escape(value), record=record, bound_column=bound_column))}<br/>{escape(record.mapped_device.custom_field_data["slurpit_devicetype"])}</span>') #nosec 
    
class SlurpitPlanningTable(tables.Table):

    class Meta:
        attrs = {
            "class": "table table-hover object-list",
        }
        empty_text = _("No results found")

    def __init__(self, data, **kwargs):
        super().__init__(data, **kwargs)

# IPADDRESS_LINK = """
# {% if record.address %}
#     <a href="{{ record.get_absolute_url }}" id="ipaddress_{{ record.pk }}" target="_blank">{{ record.address }}</a>
# {% else %}
#     <span>Default</span>
# {% endif %}
# """


# NAME_LINK = """
# {% if record.name != '' %}
#     <a href="{{ record.get_absolute_url }}" id="ipaddress_{{ record.pk }}" target="_blank">{{ record.name }}</a>
# {% else %}
#     <span></span>
# {% endif %}
# """

IPADDRESS_LINK = """
{% if record.address %}
    <a id="ipaddress_{{ record.pk }}" pk={{record.pk}} class="reconcile-detail-btn">{{ record.address }}</a>
{% else %}
    <span>Default</span>
{% endif %}
"""

# href="?tab=interface&pk={{record.pk}}"
NAME_LINK = """
{% if record.name != '' %}
    <a id="edit_{{ record.pk }}" class="reconcile-detail-btn" pk="{{record.pk}}">{{ record.name }}</a>
{% else %}
    <span></span>
{% endif %}
"""

EDIT_LINK = """
{% if record.name != '' %}
    <a href="{{record.get_edit_url}}" id="edit_{{ record.pk }}" type="button" class="btn btn-yellow">
        <i class="mdi mdi-pencil"></i>
    </a>
{% else %}
    <span></span>
{% endif %}
"""

class SlurpitIPAMTable(TenancyColumnsMixin,NetBoxTable):
    actions = columns.ActionsColumn(actions=tuple())
    
    last_updated = tables.Column(
        verbose_name = _('Last updated')
    )

    status = columns.ChoiceFieldColumn(
        verbose_name=_('Status'),
        default=AVAILABLE_LABEL
    )

    address = tables.TemplateColumn(
        template_code=IPADDRESS_LINK,
        verbose_name=_('IP Address')
    )

    commit_action = tables.Column(
        verbose_name = _('Commit Action'),
        empty_values=(),
        orderable=False
    )

    pk = ToggleColumn()
    
    edit = tables.TemplateColumn(
        template_code=EDIT_LINK,
        verbose_name=_('')
    )
    class Meta(NetBoxTable.Meta):
        model = SlurpitInitIPAddress
        fields = ('pk', 'id', 'address', 'vrf', 'status','dns_name', 'description', 'last_updated', 'commit_action')
        default_columns = ('address', 'vrf', 'status', 'commit_action', 'dns_name', 'description', 'last_updated', 'edit')

    def render_commit_action(self, record):
        ip = str(ipaddress.ip_interface(record.address.ip))
        obj = IPAddress.objects.filter(address__net_host=ip, vrf=record.vrf)
        if obj:
            return 'Changing'
        return 'Adding'
    

class SlurpitInterfaceTable(BaseInterfaceTable):
    device = tables.Column(
        verbose_name=_('Device'),
        linkify={
            'viewname': 'dcim:device_interfaces',
            'args': [Accessor('device_id')],
        }
    )
    
    speed_formatted = columns.TemplateColumn(
        template_code='{% load helpers %}{{ value|humanize_speed }}',
        accessor=Accessor('speed'),
        verbose_name=_('Speed')
    )

    name = tables.TemplateColumn(
        template_code=NAME_LINK,
        verbose_name=_('Name')
    )

    commit_action = tables.Column(
        verbose_name = _('Commit Action'),
        empty_values=(),
        orderable=False
    )

    edit = tables.TemplateColumn(
        template_code=EDIT_LINK,
        verbose_name=_('')
    )

    actions = columns.ActionsColumn(actions=tuple())

    class Meta(NetBoxTable.Meta):
        model = SlurpitInterface
        fields = (
            'pk', 'name', 'device', 'label', 'enabled', 'type', 'description','commit_action', 'duplex'
        )
        default_columns = ('pk', 'name', 'device', 'commit_action', 'label', 'enabled', 'type', 'duplex', 'description', 'edit')

    def render_commit_action(self, record):
        obj = Interface.objects.filter(name=record.name, device=record.device)
        if obj:
            return 'Changing'
        return 'Adding'
    

# PREFIX_LINK = """
# {% if record.pk %}
#     {% if record.prefix %}
#         <a href="{{ record.get_absolute_url }}" id="prefix_{{ record.pk }}" target="_blank">{{ record.prefix }}</a>
#     {% else %}
#         <span>Default</span>
#     {% endif %}
# {% else %}
#   <a href="{% url 'ipam:prefix_add' %}?prefix={{ record }}{% if object.vrf %}&vrf={{ object.vrf.pk }}{% endif %}{% if object.site %}&site={{ object.site.pk }}{% endif %}{% if object.tenant %}&tenant_group={{ object.tenant.group.pk }}&tenant={{ object.tenant.pk }}{% endif %}" target="_blank">{{ record.prefix }}</a>
# {% endif %}
# """

PREFIX_LINK = """
{% if record.pk %}
    {% if record.prefix %}
        <a id="prefix_{{ record.pk }}" pk={{record.pk}} class="reconcile-detail-btn">{{ record.prefix }}</a>
    {% else %}
        <span>Default</span>
    {% endif %}
{% else %}
  <a href="{% url 'ipam:prefix_add' %}?prefix={{ record }}{% if object.vrf %}&vrf={{ object.vrf.pk }}{% endif %}{% if object.site %}&site={{ object.site.pk }}{% endif %}{% if object.tenant %}&tenant_group={{ object.tenant.group.pk }}&tenant={{ object.tenant.pk }}{% endif %}" target="_blank">{{ record.prefix }}</a>
{% endif %}
"""


PREFIX_COPY_BUTTON = """
{% copy_content record.pk prefix="prefix_" %}
"""

PREFIX_LINK_WITH_DEPTH = """
{% load helpers %}
{% if record.depth %}
    <div class="record-depth">
        {% for i in record.depth|as_range %}
            <span>•</span>
        {% endfor %}
    </div>
{% endif %}
""" + PREFIX_LINK

VRF_LINK = """
{% if value %}
    <a href="{{ record.vrf.get_absolute_url }}">{{ record.vrf }}</a>
{% elif object.vrf %}
    <a href="{{ object.vrf.get_absolute_url }}">{{ object.vrf }}</a>
{% else %}
    Global
{% endif %}
"""


class SlurpitPrefixTable(TenancyColumnsMixin, NetBoxTable):
    prefix = columns.TemplateColumn(
        verbose_name=_('Prefix'),
        template_code=PREFIX_LINK_WITH_DEPTH,
        export_raw=True,
        attrs={'td': {'class': 'text-nowrap'}}
    )
    status = columns.ChoiceFieldColumn(
        verbose_name=_('Status'),
        default=AVAILABLE_LABEL
    )
    vrf = tables.TemplateColumn(
        template_code=VRF_LINK,
        verbose_name=_('VRF')
    )
    scope_type = columns.ContentTypeColumn(
        verbose_name=_('Scope Type'),
    )
    scope = tables.Column(
        verbose_name=_('Scope'),
        linkify=True,
        orderable=False
    )
    
    site = tables.Column(
        verbose_name=_('Site'),
        linkify=True
    )

    commit_action = tables.Column(
        verbose_name = _('Commit Action'),
        empty_values=(),
        orderable=False
    )

    vlan = tables.Column(
        linkify=True,
        verbose_name=_('VLAN')
    )
    role = tables.Column(
        verbose_name=_('Role'),
        linkify=True
    )
    
    edit = tables.TemplateColumn(
        template_code=EDIT_LINK,
        verbose_name=_('')
    )

    actions = columns.ActionsColumn(actions=tuple())

    class Meta(NetBoxTable.Meta):
        model = SlurpitPrefix
        fields = (
            'pk', 'id', 'prefix','status', 'vrf',  'tenant',
            'scope', 'scope_type', 'vlan', 'role', 'description','commit_action'
        )
        default_columns = (
            'pk', 'prefix', 'status','vrf', 'commit_action', 'tenant', 'vlan', 'role', 'description', 'edit',
        )
        row_attrs = {
            'class': lambda record: 'success' if not record.pk else '',
        }

    def render_commit_action(self, record):
        obj = Prefix.objects.filter(prefix=record.prefix, vrf=record.vrf)
        if obj:
            return 'Changing'
        return 'Adding'

VLAN_LINK = """
{% if record.pk %}
    <a href="{{ record.get_absolute_url }}">{{ record.vid }}</a>
{% elif perms.ipam.add_vlan %}
    <a href="{% url 'ipam:vlan_add' %}?vid={{ record.vid }}{% if record.vlan_group %}&group={{ record.vlan_group.pk }}{% endif %}" class="btn btn-sm btn-success">{{ record.available }} VLAN{{ record.available|pluralize }} available</a>
{% else %}
    {{ record.available }} VLAN{{ record.available|pluralize }} available
{% endif %}
"""

VLAN_PREFIXES = """
{% for prefix in value.all %}
    <a href="{% url 'ipam:prefix' pk=prefix.pk %}">{{ prefix }}</a>{% if not forloop.last %}<br />{% endif %}
{% endfor %}
"""

class SlurpitVLANTable(TenancyColumnsMixin, NetBoxTable):
    vid = tables.Column(
        verbose_name=_('VID')
    )
    name = tables.TemplateColumn(
        template_code=NAME_LINK,
        verbose_name=_('Name')
    )
    site = tables.Column(
        verbose_name=_('Site'),
        linkify=True
    )
    group = tables.Column(
        verbose_name=_('Group'),
    )
    status = columns.ChoiceFieldColumn(
        verbose_name=_('Status'),
        default=AVAILABLE_LABEL
    )
    role = tables.Column(
        verbose_name=_('Role'),
        linkify=True
    )
    l2vpn = tables.Column(
        accessor=tables.A('l2vpn_termination__l2vpn'),
        linkify=True,
        orderable=False,
        verbose_name=_('L2VPN')
    )
    prefixes = columns.TemplateColumn(
        template_code=VLAN_PREFIXES,
        orderable=False,
        verbose_name=_('Prefixes')
    )
    comments = columns.MarkdownColumn(
        verbose_name=_('Comments'),
    )
    tags = columns.TagColumn(
        url_name='ipam:vlan_list'
    )

    commit_action = tables.Column(
        verbose_name = _('Commit Action'),
        empty_values=(),
        orderable=False
    )

    edit = tables.TemplateColumn(
        template_code=EDIT_LINK,
        verbose_name=_('')
    )

    actions = columns.ActionsColumn(actions=tuple())

    class Meta(NetBoxTable.Meta):
        model = SlurpitVLAN
        fields = (
            'pk', 'id', 'vid', 'name', 'site', 'group', 'prefixes', 'tenant', 'tenant_group', 'status', 'role',
            'description', 'comments', 'tags', 'l2vpn', 'created', 'last_updated',
        )
        default_columns = ('pk', 'name', 'vid', 'group', 'commit_action', 'status', 'role', 'tenant', 'description', 'edit')
        row_attrs = {
            'class': lambda record: 'success' if not isinstance(record, SlurpitVLAN) else '',
        }

    def render_commit_action(self, record):
        obj = VLAN.objects.filter(name=record.name, group__name=record.group)
        if obj is None:
            obj = VLAN.objects.filter(vid=record.vid, group__name=record.group)
        if obj:
            return 'Changing'
        return 'Adding'