from rest_framework import serializers
from bookings.models import Restaurant, Booking



class RestaurantSerializer(serializers.Serializer):
    pk = serializers.IntegerField(read_only=True)
    name = serializers.CharField(required=True, max_length=100)
    description = serializers.CharField(required=True, min_length=20)
    opening_time = serializers.TimeField()
    closing_time = serializers.TimeField()
