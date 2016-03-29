from django.contrib import admin

from bookings.models import Restaurant, Table, Booking


admin.register(Restaurant)
admin.register(Table)
admin.register(Booking)
