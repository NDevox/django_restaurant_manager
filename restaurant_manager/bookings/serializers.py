from rest_framework import serializers
from bookings.models import Restaurant, Booking


class RestaurantSerializer(serializers.ModelSerializer):
    """
    Serialised format for the Restaurant object.
    """

    class Meta:
        model = Restaurant
        fields = ('pk', 'name', 'description', 'opening_time', 'closing_time')


class BookingSerializer(serializers.ModelSerializer):
    """
    Serialized format for the Booking object.
    """

    class Meta:
        model = Booking
        fields = ('pk', 'restaurant', 'party_size', 'table', 'date', 'time', 'length', 'end_time')
