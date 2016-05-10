from rest_framework import serializers
from bookings.models import Restaurant, Booking


class RestaurantSerializer(serializers.Serializer):
    """
    Serialised format for the Restaurant object.
    """
    pk = serializers.IntegerField(read_only=True)
    name = serializers.CharField(required=True, max_length=100)
    description = serializers.CharField(required=True, min_length=20)
    opening_time = serializers.TimeField()
    closing_time = serializers.TimeField()

    def create(self, validated_data):
        """
        Create a Restaurant object using validated data.

        :param validated_data: dict, data used to create a Restaurant.
        :return: Restaurant object.
        """
        return Restaurant.objects.create(**validated_data)

    def update(self, instance, validated_data):
        """
        Update a Restaurant object based on validated data.

        :param instance: Restaurant, restaurant to be updated.
        :param validated_data: dict, data used to update the restaurant.
        :return: updated Restaurant object.
        """
        instance.name = validated_data.get('name', instance.name)
        instance.description = validated_data.get('description', instance.description)
        instance.opening_time = validated_data.get('opening_time', instance.opening_time)
        instance.closing_time = validated_data.get('closing_time', instance.closing_time)

        instance.save()

        return instance
