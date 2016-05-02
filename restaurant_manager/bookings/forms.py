import datetime

from django.forms import ModelForm, Form, BooleanField, ModelChoiceField, ValidationError, Select, TextInput, SelectDateWidget

from bookings.models import Restaurant, Booking


def available_times(opening_time, closing_time):
    """
    Yield 15 minute time intervals between opening and 1 hour befor closing time.

    Here we assume restaurants only ever want to book in 15 minute intervals which I believe is acceptable.

    We also assume no restaurant will allow bookings within an hour of closing time due to prep/serving times.

    :param opening_time: Time object, the opening time of a restaurant.
    :param closing_time: Time object, the closing time of a restaurant.
    :return: Time object, a time slow for booking.
    """
    time = opening_time

    while time < (datetime.datetime.combine(datetime.date.today(), closing_time) - datetime.timedelta(hours=1)).time():
        yield (time, time.strftime('%H:%M'))
        time = (datetime.datetime.combine(datetime.date.today(), time) + datetime.timedelta(minutes=15)).time()


class RestaurantForm(ModelForm):
    """
    Simple form to make a restaurant, ensure opening and closing times make sense.
    """
    class Meta:
        model = Restaurant

        exclude = ['tables']

        widgets = {
            'opening_time': Select(choices=available_times(datetime.time(0,0,0,0), datetime.time(23,45,0,0))),
            'closing_time': Select(choices=available_times(datetime.time(0,0,0,0), datetime.time(23,45,0,0)))
        }

    def clean(self):
        cleaned_data = super(RestaurantForm, self).clean()

        open = cleaned_data.get('opening_time')
        close = cleaned_data.get('closing_time')

        if close < open:
            raise ValidationError('Closing time cannot be before opening time.')


class BookingForm(ModelForm):
    """
    Control booking creation here.
    """
    optimised = BooleanField(required=False)  # Ask if we want to optimise, e.g. combine tables.

    class Meta:
        model = Booking
        fields = ['restaurant', 'party_size', 'date', 'time', 'length']

        widgets = {
            'restaurant': TextInput(),
            'date': SelectDateWidget(years=(datetime.date.today().year, datetime.date.today().year + 1))
        }

    def __init__(self, restaurant, *args, **kwargs):
        """
        Assign the restaurant and it's initial value - annoyingly this is it's pk for now. Make this readonly.

        Set time limits for booking:
        - Only allow bookings within the opening hours of a restaurant.
        - Don't allow more than 2 hours (Assuming this is a limit).

        :param restaurant: Restaurant obj, the restaurant we are booking for.
        """
        super(BookingForm, self).__init__(*args, **kwargs)
        self.restaurant = restaurant
        self.fields['restaurant'].initial = restaurant
        self.fields['restaurant'].widget.attrs['readonly'] = True

        self.fields['time'].widget = Select(choices=available_times(restaurant.opening_time, restaurant.closing_time))
        self.fields['length'].widget = Select(choices=available_times(datetime.time(0,0,0), datetime.time(3,15,0)))

    def clean(self):
        """
        Do some sense checking.

        Make sure the bookings are within the time limits of the restaurant. Ensure a time has been given.

        Figure out extra parameters for the Booking and remove excess stuff (e.g. optimise).
        """
        cleaned_data = super(BookingForm, self).clean()

        time = cleaned_data.get('time')
        length = cleaned_data.get('length')

        if time and length:
            if (datetime.datetime.combine(datetime.date.today(), time) + length).time() > self.restaurant.closing_time:
                raise ValidationError('Booking exceeds restaurant closing time.')
        else:
            raise ValidationError('No time or length given.')

        # Great, timing is valid - lets get the end time to store.

        end_time = (datetime.datetime.combine(datetime.date.today(), time) + length).time()
        cleaned_data['end_time'] = end_time

        # Now we need to find any spare tables.

        date = cleaned_data.get('date')
        party = cleaned_data.get('party_size')

        cleaned_data['table'] = self.restaurant.find_table(date,
                                                           time,
                                                           end_time,
                                                           party,
                                                           optimise=cleaned_data.pop('optimised'))

        if not cleaned_data['table']:  # If there aren't any tables lets alert the customer
            raise ValidationError('No tables available for this time.')


class RestaurantChoiceForm(Form):
    """
    Simple form to choose a restaurant we will be booking with.
    """
    restaurant_choice = ModelChoiceField(Restaurant.objects.all())
