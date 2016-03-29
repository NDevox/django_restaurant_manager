import datetime
from itertools import combinations

from django.db import models
from django import forms
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

    # Lesser than would be safer, but assuming we restrict when opening and closing times can be, != is more accurate.
    while time != (datetime.datetime.combine(datetime.date.today(), close) - datetime.timedelta(hours=1)).time():
        yield (time, time.strftime('%H:%M'))
        time = (datetime.datetime.combine(datetime.date.today(), time) + datetime.timedelta(minutes=15)).time()


class Table(models.Model):
    """
    Store the tables in a model so we can gather tables based on queries.
    """
    size = models.PositiveIntegerField()

    def __unicode__(self):
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
        Stub for the optimise function where we combine multiple tables together for some parties.

        :param smaller_tables: lst [Table], a list of tables smaller than the party size.
        :param bigger_tables: lst [Table], a list of tables larger than the party size.
        :param party: int, the size of the party.
        :return: lst [Tab;e], a list of the usable tables.
        """
        if smaller_tables:
            for combination in combinations(smaller_tables, 2):
                if sum([table.size for table in smaller_tables]) == party:
                    return combination

        if bigger_tables:
            bigger_tables.sort(key=lambda x: x.size)

            return bigger_tables[:1]  # need to return as a list.

    def find_table(self, date, time, length, party, optimise):
        """
        Find available tables for the given time.

        :param date: Date obj, day of the booking.
        :param time: Time obj, time of the booking.
        :param length: TimeDelta obj, length of the booking.
        :param party: int, size of party.
        :param optimise: bool, are we comibining or using larger tables?
        :return: lst [Table], list of Tables needed for booking.
        """

        tables = self.tables.all()

        available_tables = []

        for table in tables:
            if table.booking_set.filter(date=date, time__lte=time+length, time__gte=time):
                continue
            else:
                available_tables.append(table)


        smaller_tables = []

        bigger_tables = []

        for table in available_tables:
            if table.size == party:
                return table
            elif table.size < party:
                smaller_tables.append(table)
            else:
                bigger_tables.append(table)
        else:
            if optimise:
                return self.optimise(smaller_tables, bigger_tables, party)

    def __unicode__(self):
        return '{restaurant}\n\n{description}'.format(restaurant=self.name, description=self.description)


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

    def __unicode__(self):
        return 'Booking for {party} at {restaurant} on {date}'.format(party=self.party_size,
                                                                      restaurant=self.restaurant,
                                                                      date=self.time)


class RestaurantForm(ModelForm):
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
    class Meta:
        model = Booking
        fields = ['restaurant', 'party_size', 'date', 'time', 'length']

        widgets = {
            'restaurant': TextInput(),
            'date': SelectDateWidget(years=(datetime.date.today().year, datetime.date.today().year + 1))
        }

    def __init__(self, restaurant, *args, **kwargs):
        super(BookingForm, self).__init__(*args, **kwargs)
        self.restaurant = restaurant
        self.fields['restaurant'].initial = restaurant.name
        self.fields['restaurant'].widget.attrs['readonly'] = True
        self.fields['time'].widget = Select(choices=available_times(restaurant.opening_time, restaurant.closing_time))

        self.fields['length'].widget = Select(choices=available_times(datetime.time(0,0,0), datetime.time(3,15,0)))

    def clean(self):
        cleaned_data = super(BookingForm, self).clean()

        time = cleaned_data.get('time')
        length = cleaned_data.get('length')

        if time and length:
            if time + length > self.restaurant.closing_time:
                raise ValidationError('Booking exceeds restaurant closing time.')
        else:
            raise ValidationError('No time or length given.')

        date = cleaned_data.get('date')
        party = cleaned_data.get('party_size')
        cleaned_data['table'] = self.restaurant.find_table(date, time, length, party, True)

        if not cleaned_data['table']:
            raise ValidationError('No tables available for this time.')


class RestaurantChoiceForm(Form):
    restaurant_choice = forms.ModelChoiceField(Restaurant.objects.all())