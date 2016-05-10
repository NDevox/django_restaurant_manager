from django.shortcuts import render, redirect
from django.http import HttpResponse

from rest_framework.renderers import JSONRenderer

from bookings.forms import BookingForm, RestaurantForm, RestaurantChoiceForm
from bookings.models import Restaurant, Booking
from bookings.serializers import RestaurantSerializer


class JSONResponse(HttpResponse):
    """
    HttpResponse which returns JSON.
    """
    def __init__(self, data, *args, **kwargs):
        """
        Add JSON Data to HTTPResponse init

        :param data: JSON Data to add.
        """
        content = JSONRenderer().render(data)
        kwargs['content_type'] = 'application/json'
        super(JSONResponse, self).__init__(content, *args, **kwargs)


def get_restaurants(request):
    """
    List all Restaurants.

    :param request:
    :return: JSONResponse, JSON of all the Restaurants.
    """

    if request.method == 'GET':
        restaurants = Restaurant.objects.all()
        serializer = RestaurantSerializer(restaurants, many=True)
        return JSONResponse(serializer.data)



def make_restaurant(request):
    if request.method == 'POST':
        form = RestaurantForm(request.POST)

        if form.is_valid():
            Restaurant.objects.create(**form.cleaned_data)

            return HttpResponse('made')
    else:
        form = RestaurantForm()
    return render(request, 'bookings/restaurant.html', {'form':form})


def choose_restaurant(request):
    if request.method == 'POST':
        form = RestaurantChoiceForm(request.POST)

        if form.is_valid():

            return redirect('bookings:make_booking', form.cleaned_data['restaurant_choice'].pk)

    else:
        form = RestaurantChoiceForm()

    return render(request, 'bookings/choose_restaurant.html', {'form': form})


def make_booking(request, restaurant_pk):
    restaurant = Restaurant.objects.get(pk=restaurant_pk)
    if request.method == 'POST':
        form = BookingForm(restaurant, request.POST)

        if form.is_valid():
            tables = form.cleaned_data.pop('table')
            booking = Booking.objects.create(**form.cleaned_data)
            booking.table.add(*tables)

            return HttpResponse('Done')

    else:
        form = BookingForm(restaurant=restaurant)

    return render(request, 'bookings/book.html', {'form': form})