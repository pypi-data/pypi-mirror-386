from uuid import uuid4
from django.contrib.gis.db import models
from .managers import AddressModelManager

def generate_uuid():
    return uuid4().hex

# ISO 3166 standard
class AdministrativeAreaType(models.TextChoices):
    STATE = "STATE", "State"
    PROVINCE = "PROVINCE", "Province"


class LocalityType(models.TextChoices):
    CITY = "CITY", "City"
    TOWN = "TOWN", "Town"
    VILLAGE = "VILLAGE", "Village"
    DISTRICT = "DISTRICT", "District"


class SubLocalityType(models.TextChoices):
    SUBURB = "SUBURB", "Suburb"


class AddressEntityTypeModel(models.Model):

    name = models.CharField(max_length=255, primary_key=True)
    description = models.CharField(max_length=255, default='', blank=True, null=True)

    def __str__(self):
        return self.name

    class Meta:
        db_table = 'dm_client_spatial_address_entity_type'


class AddressModel(models.Model):
    id = models.CharField(primary_key=True, default=generate_uuid, editable=False, max_length=32)
    country = models.CharField(max_length=2)                # ISO 3166
    administrative_area = models.CharField(max_length=100)  # State or province
    administrative_area_type = models.CharField(max_length=32, choices=AdministrativeAreaType.choices, default=AdministrativeAreaType.STATE)
    locality = models.CharField(max_length=100, null=True, blank=True)
    locality_type = models.CharField(max_length=32, blank=True, default=LocalityType.CITY, choices=LocalityType.choices)
    sub_locality = models.CharField(max_length=100, null=True, blank=True)
    sub_locality_type = models.CharField(max_length=32, blank=True, choices=SubLocalityType.choices, default=SubLocalityType.SUBURB)
    thoroughfare = models.CharField(max_length=200)  # Street name
    address_number = models.CharField(max_length=10)  # Street number
    postal_code = models.CharField(max_length=20, null=True, blank=True)
    full_address = models.CharField(max_length=1000, null=False) # Complete address
    geom = models.PointField()  # Stores latitude and longitude as a point
    entity_type = models.ForeignKey(AddressEntityTypeModel, on_delete=models.CASCADE)

    objects = AddressModelManager()

    def __str__(self):
        return f"{self.address_number} {self.thoroughfare}, {self.locality}, {self.administrative_area}, {self.country}, {self.postal_code}"

    class Meta:
        db_table = 'dm_client_spatial_address'