import datetime
from itertools import combinations

from django import forms
from django.db import models
from django.db.models import Q
from django.forms import ModelForm, Select, ValidationError, TextInput, Form, SelectDateWidget


def available_times(open, close):
    """
    Yield 15 minute time intervals between opening and 1 hour befor closing time.

    Here we assume restaurants only ever want to book in 15 minute intervals which I believe is acceptable.

    We also assume no restaurant will allow bookings within an hour of closing time due to prep/serving times.

    :param open: Time object, the opening time of a restaurant.
    :param close: Time object, the closing time of a restaurant.
    :return: Time object, a time slow for booking.
    """
    time = open

    while time < (datetime.datetime.combine(datetime.date.today(), close) - datetime.timedelta(hours=1)).time():
        yield (time, time.strftime('%H:%M'))
        time = (datetime.datetime.combine(datetime.date.today(), time) + datetime.timedelta(minutes=15)).time()


class Table(models.Model):
    """
    Store the tables in a model so we can gather tables based on queries.
    """
    size = models.PositiveIntegerField()

    def __str__(self):
        return str(self.size)


class Restaurant(models.Model):
    """
    Manage bookings for each restaurant. Might want to consider adding a reference to bookings so we don't rely on a
    back reference when checking for over bookings.
    """
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=False)
    opening_time = models.TimeField()
    closing_time = models.TimeField()
    tables = models.ManyToManyField(Table)

    def optimise(self, smaller_tables, bigger_tables, party):
        """
        This calculates whether smaller tables can be joined to fit the customers needs, or if we can use a bigger table.

        A current limitation is it will not consider a combination of smaller tables which add up to more than the
        requirement. This should be relatvely simple to fix though.

        :param smaller_tables: lst [Table], a list of tables smaller than the party size.
        :param bigger_tables: lst [Table], a list of tables larger than the party size.
        :param party: int, the size of the party.
        :return: lst [Table], a list of the usable tables.
        """

        if smaller_tables:  # It is better to start with smaller tables. as they may fit perfectly.
            for combination in combinations(smaller_tables, 2):
                if sum([table.size for table in combination]) == party:
                    return list(combination)  # We have a perfect combination, return it.

        if bigger_tables:
            # lets not waste too much table space, so return the smallest table bigger than the requirements.
            bigger_tables.sort(key=lambda x: x.size)

            return list(bigger_tables[:1])  # need to return as a list.

    def find_table(self, date, time, end_time, party, optimise=False):
        """
        Find available tables for the given time.

        If optimised, give a combination of tables - or a larger table.

        :param date: Date obj, day of the booking.
        :param time: Time obj, time of the booking.
        :param end_time: Time obj, time the booking finishes.
        :param party: int, size of party.
        :param optimise: bool, are we comibining or using larger tables?
        :return: lst [Table], list of Tables needed for booking.
        """

        tables = self.tables.all()

        available_tables = []

        for table in tables:
            # range is inclusive, but I think we can assume that some time is needed for cleanup between meals.
            if table.booking_set.filter(Q(date=date, time__range=(time, end_time)) | Q(date=date, end_time__range=(time, end_time))):
                # There is already a booking covering the given times so we can't use this table.
                continue
            else:  # Table is free, add it to available tables.
                available_tables.append(table)

        smaller_tables = []

        bigger_tables = []

        for table in available_tables:
            if table.size == party:
                return [table]  # Great this is perfectly sized, use it.
            elif table.size < party:
                smaller_tables.append(table)
            else:
                bigger_tables.append(table)
        else:  # If we haven't returned yet, we may need to optimise.
            if optimise:
                return self.optimise(smaller_tables, bigger_tables, party)

    def __str__(self):
        return self.name


class Booking(models.Model):
    """
    Bookings need to know the number of people, the restaurant, the tables and the time they occur so we don't overbook.
    """
    restaurant = models.ForeignKey(Restaurant)
    party_size = models.PositiveIntegerField()
    table = models.ManyToManyField(Table)  # It is possible to have more than one table.
    date = models.DateField()
    time = models.TimeField()
    length = models.DurationField()
    end_time = models.TimeField()

    def __str__(self):
        return 'Booking for {party} at {restaurant} on {date}'.format(party=self.party_size,
                                                                      restaurant=self.restaurant,
                                                                      date=self.time)


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
    optimised = forms.BooleanField(required=False)  # Ask if we want to optimise, e.g. combine tables.

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
    restaurant_choice = forms.ModelChoiceField(Restaurant.objects.all())