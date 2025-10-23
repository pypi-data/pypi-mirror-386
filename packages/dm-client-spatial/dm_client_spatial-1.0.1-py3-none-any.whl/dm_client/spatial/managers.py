from django.db.models import Manager
from django.contrib.gis.geos import Point


class AddressModelManager(Manager):

    def create_address(self, entity_type: str, **kwargs):
        from .models import AdministrativeAreaType, LocalityType, SubLocalityType
        geom = Point(float(kwargs.get('longitude')), float(kwargs.get('latitude')))
        address_components = kwargs.get('address_components')
        address_instance = self.create(
            country=address_components.get('country'),
            administrative_area=address_components.get('administrative_area'),
            administrative_area_type=AdministrativeAreaType.STATE,
            locality=address_components.get('locality'),
            locality_type=LocalityType.CITY,
            sub_locality=address_components.get('sub_locality'),
            sub_locality_type=SubLocalityType.SUBURB,
            thoroughfare=address_components.get('thoroughfare'),
            address_number=address_components.get('address_number'),
            postal_code=address_components.get('postal_code'),
            full_address=kwargs.get('full_address'),
            geom=geom,
            entity_type_id=entity_type
        )
        return address_instance
