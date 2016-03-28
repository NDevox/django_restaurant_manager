from django.db import models


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
    tables = models.ManyToManyField()

    def optimise(self):
        """
        Stub for the optimise function where we combine multiple tables together for some parties.
        :return: tables
        """
        pass

    def __unicode__(self):
        return '{restaurant}\n\n{description}'.format(restaurant=self.name, description=self.description)


class Booking(models.Model):
    """
    Bookings need to know the number of people, the restaurant, the tables and the time they occur so we don't overbook.
    """
    restaurant = models.ForeignKey(Restaurant)
    party_size = models.PositiveIntegerField()
    table = models.ManyToManyField(Table)  # It is possible to have more than one table.
    time = models.DateTimeField()
    length = models.DurationField()

    def __unicode__(self):
        return 'Booking for {party} at {restaurant} on {date}'.format(party=self.party_size,
                                                                      restaurant=self.restaurant,
                                                                      date=self.time)
