from django import template

register = template.Library()

@register.filter
def split(value, delimiter=","):
    """Split a string into a list."""
    return value.split(delimiter) if value else []

@register.simple_tag
def seat_pnr_pairs(seat_numbers, pnr_codes):
    """
    Return a list of (seat, pnr) pairs for easier iteration in templates.
    """
    seats = seat_numbers.split(",") if seat_numbers else []
    pnrs = pnr_codes.split(",") if pnr_codes else []
    return list(zip(seats, pnrs))
