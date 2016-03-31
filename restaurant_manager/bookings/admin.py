from django.contrib import admin

from bookings.models import Restaurant, Table, Booking


admin.site.register(Restaurant)
admin.site.register(Table)
admin.site.register(Booking)
