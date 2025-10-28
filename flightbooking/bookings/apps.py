"""App configuration for the Bookings module."""
from django.apps import AppConfig


class BookingsConfig(AppConfig):
    """Configuration class for the bookings app."""
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'bookings'
