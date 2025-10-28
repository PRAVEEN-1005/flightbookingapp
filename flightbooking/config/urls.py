from django.contrib import admin
from django.urls import path
from bookings import views   # ✅ correct import

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", views.home, name="home"),
    path("book/<int:flight_id>/", views.book_flight, name="book_flight"),
    path("my-bookings/", views.my_bookings, name="my_bookings"),
    path("booking/<int:pk>/edit/", views.BookingUpdateView.as_view(), name="booking_edit"),
    path("booking/<int:pk>/delete/", views.BookingDeleteView.as_view(), name="booking_delete"),
    path("pay/<int:booking_id>/", views.pay_booking, name="pay_booking"),


    # ✅ NEW Refund Route
    path("booking/<int:pk>/refund/", views.request_refund, name="request_refund"),


]
