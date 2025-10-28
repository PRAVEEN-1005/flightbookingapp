# pylint: disable=no-member

from django.shortcuts import render, redirect, get_object_or_404
from .models import Flight, Passenger, Booking
from django.urls import reverse_lazy
from django.views.generic import UpdateView, DeleteView
import uuid
import datetime
from django.contrib import messages


def home(request):
    flights = None
    return_flights = None

    if request.method == "POST":
        origin = request.POST.get("origin")
        destination = request.POST.get("destination")
        departure_date = request.POST.get("departure_date")
        return_date = request.POST.get("return_date")
        trip_type = request.POST.get("trip_type")

        try:
            dep_date_obj = datetime.datetime.strptime(departure_date, "%Y-%m-%d").date()
        except:
            dep_date_obj = None

        try:
            ret_date_obj = datetime.datetime.strptime(return_date, "%Y-%m-%d").date() if return_date else None
        except:
            ret_date_obj = None

        if dep_date_obj:
            flights = Flight.objects.filter(
                origin__icontains=origin,
                destination__icontains=destination,
                departure_time__date=dep_date_obj
            )

        if trip_type == "round" and ret_date_obj:
            return_flights = Flight.objects.filter(
                origin__icontains=destination,
                destination__icontains=origin,
                departure_time__date=ret_date_obj
            )

    return render(request, "bookings/home.html", {
        "flights": flights,
        "return_flights": return_flights,
    })


def generate_pnr(seat, flight_number):
    """Generate a simple PNR using flight + seat + short UUID"""
    return f"{flight_number}-{seat}-{str(uuid.uuid4())[:6].upper()}"


def book_flight(request, flight_id):
    flight = get_object_or_404(Flight, id=flight_id)

    # ✅ Collect already booked seats
    booked_seats = []
    for b in Booking.objects.filter(flight=flight):
        booked_seats.extend(b.seat_numbers.split(","))

    if request.method == "POST":
        first_name = request.POST.get("first_name")
        last_name = request.POST.get("last_name")
        email = request.POST.get("email")
        seats_selected = request.POST.getlist("seats")

        if not seats_selected:
            error_message = "Please select at least one seat."
            return render(request, "bookings/booking_form.html", {
                "flight": flight,
                "error": error_message,
                "booked_seats": booked_seats,
                "rows": range(1, 7),
                "left_seats": ["A", "B", "C"],
                "right_seats": ["D", "E", "F"],
            })

        # ✅ Prevent double-booking
        for seat in seats_selected:
            if seat in booked_seats:
                error_message = f"Seat {seat} is already booked for this flight."
                return render(request, "bookings/booking_form.html", {
                    "flight": flight,
                    "error": error_message,
                    "booked_seats": booked_seats,
                    "rows": range(1, 7),
                    "left_seats": ["A", "B", "C"],
                    "right_seats": ["D", "E", "F"],
                })

        # ✅ Get or create passenger
        passenger, created = Passenger.objects.get_or_create(
            email=email,
            defaults={"first_name": first_name, "last_name": last_name},
        )
        if not created:
            passenger.first_name = first_name
            passenger.last_name = last_name
            passenger.save()

        # ✅ Create booking (pending until payment)
        booking = Booking.objects.create(
            flight=flight,
            passenger=passenger,
            seat_numbers=",".join(seats_selected),
            total_fare=flight.fare * len(seats_selected),
            payment_status="Pending",
            pnr_codes="",  # Will be filled after payment
        )

        return redirect("pay_booking", booking.id)

    # GET request
    return render(request, "bookings/booking_form.html", {
        "flight": flight,
        "booked_seats": booked_seats,
        "rows": range(1, 7),
        "left_seats": ["A", "B", "C"],
        "right_seats": ["D", "E", "F"],
    })


def my_bookings(request):
    bookings = Booking.objects.all().order_by("-booking_date")
    return render(request, "bookings/my_bookings.html", {"bookings": bookings})


def pay_booking(request, booking_id):
    booking = get_object_or_404(Booking, id=booking_id)

    if request.method == "POST":
        # ✅ Generate fresh PNRs for current seats
        seats = booking.seat_numbers.split(",")
        pnr_list = [generate_pnr(seat, booking.flight.flight_number) for seat in seats]

        booking.pnr_codes = ",".join(pnr_list)
        booking.payment_status = "Confirmed"
        booking.original_fare = booking.total_fare  # store original fare at payment
        booking.refund_needed = False
        booking.refund_amount = None
        booking.refunded_seats = ""  # reset refunded seats
        booking.save()

        return render(request, "bookings/booking_confirmation.html", {
            "booking": booking,
        })

    return render(request, "bookings/payment_page.html", {
        "booking": booking,
    })


class BookingUpdateView(UpdateView):
    model = Booking
    fields = []  # we'll handle seat_numbers manually
    template_name = "bookings/booking_edit.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        flight = self.object.flight

        # Collect already booked seats (exclude current booking)
        booked_seats = []
        for b in Booking.objects.filter(flight=flight).exclude(id=self.object.id):
            booked_seats.extend(b.seat_numbers.split(","))

        selected_seats = self.object.seat_numbers.split(",") if self.object.seat_numbers else []

        context.update({
            "rows": range(1, 7),
            "left_seats": ["A", "B", "C"],
            "right_seats": ["D", "E", "F"],
            "booked_seats": booked_seats,
            "selected_seats": selected_seats,
        })
        return context

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        seat_numbers = request.POST.getlist("seat_numbers")

        if not seat_numbers:
            return self.render_to_response(
                self.get_context_data(form=self.get_form(), error="Please select at least one seat.")
            )

        # Check if any selected seat is already taken
        for b in Booking.objects.filter(flight=self.object.flight).exclude(id=self.object.id):
            taken = b.seat_numbers.split(",")
            if set(seat_numbers) & set(taken):
                return self.render_to_response(
                    self.get_context_data(form=self.get_form(),
                        error=f"One or more seats are already taken: {', '.join(set(seat_numbers) & set(taken))}")
                )

        # Compare fares
        old_fare = self.object.total_fare
        new_fare = self.object.flight.fare * len(seat_numbers)

        # ✅ Track removed seats
        old_seats = set(self.object.seat_numbers.split(",")) if self.object.seat_numbers else set()
        new_seats = set(seat_numbers)
        removed_seats = list(old_seats - new_seats)

        self.object.seat_numbers = ",".join(seat_numbers)
        self.object.total_fare = new_fare

        if new_fare > old_fare:
            # User owes more → reset to pending and payment
            self.object.payment_status = "Pending"
            self.object.pnr_codes = ""
            self.object.refunded_seats = ""  # clear refunded seats
            self.object.save()
            return redirect("pay_booking", booking_id=self.object.id)
        else:
            # Refund case
            refund = old_fare - new_fare
            self.object.original_fare = old_fare
            self.object.refund_needed = True
            self.object.refund_amount = refund
            self.object.refunded_seats = ",".join(removed_seats)  # ✅ store refunded seats
            pnr_list = [generate_pnr(seat, self.object.flight.flight_number) for seat in seat_numbers]
            self.object.pnr_codes = ",".join(pnr_list)
            self.object.payment_status = "Confirmed"
            self.object.save()
            return redirect("my_bookings")


class BookingDeleteView(DeleteView):
    model = Booking
    template_name = "bookings/booking_confirm_delete.html"
    success_url = reverse_lazy("my_bookings")


def request_refund(request, pk):
    booking = get_object_or_404(Booking, pk=pk)

    if booking.payment_status == "Confirmed" and booking.refund_needed:
        booking.payment_status = "Refunded"
        booking.refund_amount = booking.refund_difference
        booking.refund_needed = False
        booking.save()

        refunded = booking.refunded_seats.split(",") if booking.refunded_seats else []

        return render(request, "bookings/refund_confirmation.html", {
            "booking": booking,
            "refunded_seats": refunded,
        })
    else:
        messages.error(request, "⚠️ Refund cannot be processed for this booking.")
        return redirect("my_bookings")
