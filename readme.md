# Restaurant Manager

A sample Django app designed to help manage restaurants and book tables.

## Setup

- Make a virtualenv for python3 (this is untested in python2).
- pip install -r requirements.txt

Then in restaurant_manager run:

python manage.py createsuperuser

- This will allow you to make a superuser to login to the admin

python manage.py runserver

- This should get the webserver running on localhost:8000.

## Using

Putting localhost:8000/make_restaurant into your browser will allow you to make a restaurant.

That page contains a form which does some sense checking which the admin doesn't do.

Afterwards it will be worth logging in to localhost:8000/admin where you can add tables to the restaurant.

Once that is done go to localhost:8000/bookings to access a restaurant and try and make some bookings.

This will do some sense checking to make sure bookings won't overlap, as well as whether you want to optimise or not.

## Tests

There is only a minimal amount of test coverage right now (I will update it soon).

These are primarily just to cover the basic booking system.

To run the tests use:

python manage.py test
