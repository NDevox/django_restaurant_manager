from django.shortcuts import render, redirect
from django.http import HttpResponse

from bookings.models import Restaurant, Booking, BookingForm, RestaurantForm, RestaurantChoiceForm


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