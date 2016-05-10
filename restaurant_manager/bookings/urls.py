from django.conf.urls import url

from bookings import views

urlpatterns = [
    url(r'^make_restaurant$', views.make_restaurant, name='make_restaurant'),
    url(r'^$', views.choose_restaurant, name='choose_restaurant'),
    url(r'^(?P<restaurant_pk>[0-9]*)$', views.make_booking, name='make_booking'),
    url(r'^api/restaurants$', views.RestaurantList.as_view(), name='get_restaurants'),
]