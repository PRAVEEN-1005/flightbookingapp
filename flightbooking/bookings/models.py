# pylint: disable=no-member

"""Database models for the flight booking system."""
from django.db import models

class Flight(models.Model):
    """Represents a flight between two locations."""
    flight_number = models.CharField(max_length=10, unique=True)
    origin = models.CharField(max_length=100)
    destination = models.CharField(max_length=100)
    departure_time = models.DateTimeField()
    arrival_time = models.DateTimeField()
    fare = models.DecimalField(max_digits=10, decimal_places=2)  # ticket price

    def __str__(self):
        return f"{self.flight_number}: {self.origin} → {self.destination}"


class Passenger(models.Model):
    """Represents a passenger who can book flights."""
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    email = models.EmailField(unique=True)

    def __str__(self):
        return f"{self.first_name} {self.last_name}"


class Booking(models.Model):
    """Represents a booking made by a passenger for a flight."""
    flight = models.ForeignKey(Flight, on_delete=models.CASCADE)
    passenger = models.ForeignKey(Passenger, on_delete=models.CASCADE)
    seat_numbers = models.CharField(max_length=100)  # CSV of seats
    total_fare = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    booking_date = models.DateTimeField(auto_now_add=True)
    payment_status = models.CharField(
        max_length=20,
        choices=[("Pending", "Pending"), ("Confirmed", "Confirmed"), ("Refunded", "Refunded")],
        default="Pending"
    )
    pnr_codes = models.TextField(blank=True, null=True)  # ✅ PNRs for each seat

    # 🔥 Refund tracking
    original_fare = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    refund_needed = models.BooleanField(default=False)
    refund_amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)

    # ✅ NEW: track which seats were refunded
    refunded_seats = models.CharField(max_length=200, blank=True, null=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['flight', 'passenger'], name='unique_passenger_per_flight'),
        ]

    def __str__(self):
        return f"Booking {self.id} - {self.passenger} on {self.flight} ({self.seat_numbers})"

    @property
    def refund_difference(self):
        """Compute refund difference dynamically if needed."""
        if self.original_fare and self.total_fare and self.original_fare > self.total_fare:
            return self.original_fare - self.total_fare
        return 0
