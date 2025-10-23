from django.db import models
from dcim.models import Device, DeviceType
from django.utils.translation import gettext_lazy as _

"""
"hostname": "SW-PLC-33.amphia.zh",
"fqdn": "10.64.144.31",
"device_os": "cisco_ios",
"device_type": "CATALYST 4510R+E",
"added": "finder",
"created": "2023-10-30 13:29:17",
"last_updated": "2023-11-01 23:02:51"
"""

from netbox.models import NetBoxModel, PrimaryModel

class SlurpitStagedDevice(NetBoxModel):
    slurpit_id = models.BigIntegerField (unique=True)
    disabled = models.BooleanField(default=False)
    hostname = models.CharField(max_length=255, unique=True)
    fqdn = models.CharField(max_length=128)
    ipv4 = models.CharField(max_length=23, null=True)
    device_os = models.CharField(max_length=128)
    device_type = models.CharField(max_length=255)
    site = models.CharField(max_length=255, null=True)
    brand = models.CharField(max_length=255)
    serial = models.CharField(max_length=255, null=True)
    os_version = models.CharField(max_length=255, null=True)
    snmp_uptime = models.CharField(max_length=255, null=True)
    
    def __str__(self):
        return f"{self.hostname}"

    class Meta:
        ordering = ('hostname',)
        verbose_name = _('Slurpit Staged Device')
        verbose_name_plural = _('Slurpit Staged Devices')
    
    
class SlurpitImportedDevice(NetBoxModel):
    slurpit_id = models.BigIntegerField(unique=True)
    disabled = models.BooleanField(default=False)
    hostname = models.CharField(max_length=255, unique=True)
    fqdn = models.CharField(max_length=128)
    ipv4 = models.CharField(max_length=23, null=True)
    device_os = models.CharField(max_length=128)
    device_type = models.CharField(max_length=255)
    site = models.CharField(max_length=255, null=True)
    brand = models.CharField(max_length=255)
    serial = models.CharField(max_length=255, null=True)
    os_version = models.CharField(max_length=255, null=True)
    snmp_uptime = models.CharField(max_length=255, null=True)
    mapped_devicetype = models.ForeignKey(to=DeviceType, null=True, on_delete=models.SET_NULL)
    mapped_device = models.OneToOneField(to=Device, null=True, on_delete=models.CASCADE)

    def get_absolute_url(self):
        return '/'
    
    def __str__(self):
        return f"{self.hostname}"
    
    @property
    def slurpit_device_type(self):
        # Returns the 'slurpit_devicetype' value from the mapped_device's custom_field_data or None if not present.
        return self.mapped_device.custom_field_data.get('slurpit_devicetype')

    def copy_staged_values(self, device: SlurpitStagedDevice):
        self.slurpit_id = device.slurpit_id
        self.disabled = device.disabled
        self.hostname = device.hostname
        self.ipv4 = getattr(device, "ipv4", None) or getattr(device, "address", None)
        self.fqdn = device.fqdn
        self.device_os = device.device_os
        self.device_type = device.device_type
        self.serial = device.serial
        self.os_version = device.os_version
        self.snmp_uptime = device.snmp_uptime
        self.brand = device.brand
        self.site = device.site
        self.created = device.created
        self.last_updated = device.last_updated

    class Meta:
        ordering = ('hostname',)
        verbose_name = _('Slurpit Imported Device')
        verbose_name_plural = _('Slurpit Imported Devices')

    
