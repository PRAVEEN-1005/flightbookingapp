from django.contrib import admin
from .models import Flight, Passenger, Booking


@admin.register(Flight)
class FlightAdmin(admin.ModelAdmin):
    list_display = ("flight_number", "origin", "destination", "departure_time", "arrival_time", "fare")
    search_fields = ("flight_number", "origin", "destination")
    list_filter = ("origin", "destination")  # ✅ quick filtering


@admin.register(Passenger)
class PassengerAdmin(admin.ModelAdmin):
    list_display = ("first_name", "last_name", "email")
    search_fields = ("first_name", "last_name", "email")


@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = ("id", "flight", "passenger", "seat_numbers", "total_fare", "payment_status", "booking_date")
    search_fields = ("flight__flight_number", "passenger__first_name", "passenger__last_name", "passenger__email", "seat_numbers")
    list_filter = ("payment_status", "flight")  # ✅ quick filtering
