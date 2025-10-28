# pylint: disable=no-member

import pytest
from django.urls import reverse
from .models import Flight, Passenger, Booking   # ✅ relative import
from django.utils import timezone
from decimal import Decimal
from datetime import timedelta


# 1. Homepage test
@pytest.mark.django_db
def test_homepage_accessible(client):
    url = reverse("home")
    response = client.get(url)
    assert response.status_code == 200
    assert b"Flight Booking" in response.content


# 2. Flight creation test
@pytest.mark.django_db
def test_create_flight():
    flight = Flight.objects.create(
        flight_number="AB123",
        origin="Dublin",
        destination="London",
        departure_time=timezone.now() + timedelta(days=1),
        arrival_time=timezone.now() + timedelta(days=1, hours=2),
        fare=Decimal("199.99"),
    )
    assert flight.flight_number == "AB123"
    assert str(flight) == "AB123: Dublin → London"


# 3. Passenger creation test
@pytest.mark.django_db
def test_create_passenger():
    passenger = Passenger.objects.create(
        first_name="John",
        last_name="Doe",
        email="john@example.com",
    )
    assert passenger.email == "john@example.com"
    assert str(passenger) == "John Doe"


# 4. Booking creation test
@pytest.mark.django_db
def test_create_booking():
    flight = Flight.objects.create(
        flight_number="CD456",
        origin="Paris",
        destination="Berlin",
        departure_time=timezone.now() + timedelta(days=2),
        arrival_time=timezone.now() + timedelta(days=2, hours=3),
        fare=Decimal("150.00"),
    )
    passenger = Passenger.objects.create(
        first_name="Alice",
        last_name="Smith",
        email="alice@example.com",
    )
    booking = Booking.objects.create(
        flight=flight,
        passenger=passenger,
        seat_numbers="12A,12B",
        total_fare=Decimal("300.00"),
        payment_status="Confirmed",
    )
    assert booking.payment_status == "Confirmed"
    assert "Alice Smith" in str(booking)


# 5. My Bookings view test
@pytest.mark.django_db
def test_my_bookings_view(client):
    url = reverse("my_bookings")
    response = client.get(url)
    # Since no bookings yet for the logged-in user, just check the page loads
    assert response.status_code == 200
