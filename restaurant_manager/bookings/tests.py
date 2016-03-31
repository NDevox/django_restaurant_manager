import datetime

from django.test import TestCase

from bookings.models import Restaurant, Table, Booking, BookingForm


class TestBookings(TestCase):
    def setUp(self):

        open = datetime.time(hour=8)

        close = datetime.time(hour=23)

        self.restaurant = Restaurant(name='test',
                                     description='test',
                                     opening_time=open,
                                     closing_time=close)

        self.restaurant.save()

        for x in [2,2,2,4,4,4,6,6,8]:
            table = Table(size=x)
            table.save()
            self.restaurant.tables.add(table)

    def test_find_tables(self):
        table = self.restaurant.find_table(date=datetime.date.today(),
                                           time=datetime.time(10),
                                           length=datetime.timedelta(hours=1),
                                           party=8)

        self.assertIsInstance(table, list)

        self.assertEqual(len(table), 1)

        self.assertEqual(table[0].size, 8)

    def test_non_optimised_booking(self):

        form = BookingForm(self.restaurant,
                           {'restaurant':self.restaurant.pk,
                            'date':datetime.date.today(),
                            'time':datetime.time(10),
                            'length':datetime.timedelta(hours=1),
                            'party_size':8})

        self.assertEqual(form.is_valid(), True)

        tables = form.cleaned_data.pop('table')

        booking = Booking(**form.cleaned_data)

        booking.save()

        booking.table.add(*tables)

        table = self.restaurant.find_table(datetime.date.today(),
                                           datetime.time(10),
                                           datetime.timedelta(hours=1),
                                           8)

        self.assertIsNone(table)

        table = self.restaurant.find_table(datetime.date.today(),
                                           datetime.time(10, 30),
                                           datetime.timedelta(hours=1),
                                           8)

        self.assertIsNone(table)

        table = self.restaurant.find_table(datetime.date.today(),
                                           datetime.time(11),
                                           datetime.timedelta(hours=1),
                                           8)

        self.assertIsNone(table)

        table = self.restaurant.find_table(datetime.date.today(),
                                           datetime.time(11, 30),
                                           datetime.timedelta(hours=1),
                                           8)

        self.assertIsInstance(table, list)
        self.assertEqual(table[0].size, 8)

    def test_optimised_booking(self):
        """
        Ensure that when using optimised,
        :return:
        """
        form = BookingForm(self.restaurant,
                           {'restaurant':self.restaurant.pk,
                            'date':datetime.date.today(),
                            'time':datetime.time(10),
                            'length':datetime.timedelta(hours=1),
                            'party_size':8})

        self.assertEqual(form.is_valid(), True)

        tables = form.cleaned_data.pop('table')

        booking = Booking(**form.cleaned_data)

        booking.save()

        booking.table.add(*tables)

        table = self.restaurant.find_table(datetime.date.today(),
                                           datetime.time(10),
                                           datetime.timedelta(hours=1),
                                           8,
                                           optimise=True)

        self.assertIsInstance(table, list)

        self.assertGreater(len(table), 1)

        self.assertEqual(sum([x.size for x in table]), 8)