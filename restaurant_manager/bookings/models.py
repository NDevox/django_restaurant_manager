import datetime
from itertools import combinations

from django import forms
from django.db import models
from django.db.models import Q
from django.forms import ModelForm, Select, ValidationError, TextInput, Form, SelectDateWidget


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
