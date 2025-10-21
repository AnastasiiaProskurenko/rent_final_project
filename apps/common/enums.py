from django.db import models

class AmenityStatus(models.TextChoices):
    YES = 'yes', 'Yes'
    NO = 'no', 'No'
    UNKNOWN = 'unknown', 'Unknown'

class BookingStatus(models.TextChoices):
    WAITING = 'waiting','Waiting'
    AGREED = 'agreed', 'Agreed'
    CANCELED = 'canceled', 'Canceled'
    ENDED = 'ended', 'Ended'

class NotificationType(models.TextChoices):
    BOOKING_CREATED = 'booking_created','Booking_created'
    BOOKING_CONFIRMED = 'booking_confirmed', 'Booking_confirmed'
    BOOKING_REMINDER = 'booking_reminder', 'Booking_reminder'
    REVIEW_REQUEST = 'review_request', 'Review_request'
    NEW_REVIEW = 'new_review', 'New_review'

class PaymentMethod(models.TextChoices):
    CREDIT_CARD = 'credit_card', 'Credit_card'
    PAYPAL = 'paypal', 'Paypal'
    APPLE_PAY = 'apple_pay', 'Apple_pay'
    GOOGLE_PAY ='google_pay', 'Google_pay'
    BANK_TRANSFER = 'bank_transfer', 'Bank_transfer'

class PaymentStatus(models.TextChoices):
    PENDING= 'pending', 'Pending'
    COMPLETED = 'completed', 'Completed'
    FAILED = 'failed', 'Failed'
    REFUNDED = 'refunded', 'Refunded'
    CANCELLED = 'cancelled', 'Cancelled'
