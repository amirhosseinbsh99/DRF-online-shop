
import secrets
from django.utils import timezone
from datetime import timedelta
from django.conf import settings
from .models import Customer
from kavenegar import *

def generate_and_send_otp(customer, purpose):
    # Generate a 5-digit OTP
    otp = secrets.randbelow(90000) + 10000
    if getattr(settings, 'OTP_TEST_MODE', False):
        otp = 12345  # Test mode OTP
    
    # Log OTP to check if it's being generated
    print(f"Generated OTP for {purpose}: {otp}")

    # Set different fields based on the purpose
    if purpose == "signup":
        customer.token_send = otp
        customer.created_at = timezone.now()
    elif purpose == "password_reset":
        customer.token_send = otp
        customer.created_at = timezone.now()

    # Explicitly save the customer object to the database
    customer.save()

    # Log customer details after saving to ensure changes were persisted
    print(f"Customer saved after OTP generation: {customer}")

    # Send OTP via SMS
    if getattr(settings, 'OTP_TEST_MODE', False):
        print(f"Test mode: OTP for {purpose} is {otp}")
    else:
        api_key = settings.KAVENEGAR_API_KEY
        if not api_key:
            raise ValueError("Kavenegar API key is missing")

        api = KavenegarAPI(api_key)
        params = {
            'token': otp,
            'receptor': customer.phone_number,
            'template': 'verify',
            'type': 'sms'
        }
        response = api.verify_lookup(params)
        print(f"Kavenegar response: {response}")

    return otp


def verify_otp(customer, otp_code, purpose):
    """
    Verifies the OTP based on the purpose (e.g., password_reset).
    Returns True if valid, False otherwise.
    """
    # Check OTP for the given customer and purpose
    if purpose == "password_reset":
        otp = customer.token_send
        otp_created_at = customer.created_at
    elif purpose == "signup":
        otp = customer.token_send
        otp_created_at = customer.created_at
    else:
        return False  # Invalid purpose

    if not otp:
        return False  # No OTP found for the customer

    # Check if OTP matches
    
    if int(otp) != int(otp_code):
        
        return False  # OTP does not match

    # Check if OTP has expired (e.g., 5 minutes expiry)
    if timezone.now() > otp_created_at + timedelta(seconds=30):
        return False  # OTP expired
        
    
    return True  # OTP is valid
