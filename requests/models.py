from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ValidationError

# Custom validations
def validate_phone(phone):
    if len(phone) != 10 or not phone.isdigit():
        raise ValidationError('Phone number must be 10 digits long and contain only numbers')
    

def validate_state(state):
    if state not in VALID_STATES:
        raise ValidationError(f'Invalid State. Must be in network {VALID_STATES}')


REQUEST_STATUSES = ['Pending', 'Info Required', 'Approved', 'Partially Approved', 'Denied', 'Completed']
VALID_STATES = ['NJ', 'PA', 'NY', 'DE', 'MD']
BILL_TYPES = ['Medical', 'Rent', 'Utilities', 'Insurance']
MARITAL_STATUSES = ['Single', 'Married', 'Divorced', 'Separated', 'Widowed']
TREATMENT_CENTERS = ['Fox Chase Cancer Center', 'Paoli', 'Lankenau', 'Jefferson', 'Einstein Cancer Center']


class CfcUser(AbstractUser):
    email = models.EmailField(unique=True)
    organization = models.CharField(max_length=100, blank=True)
    job_title = models.CharField(max_length=50, blank=True)


# Manually allowlist users by adding their emails to this table and validate on signup
class ApprovedUser(models.Model):
    email = models.EmailField(unique=True, primary_key=True, default='')
    is_staff = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    signed_up = models.BooleanField(default=False)


class Applicant(models.Model):
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=10, validators=[validate_phone])
    street_address = models.CharField(max_length=100)
    street_address_2 = models.CharField(max_length=100, blank=True)
    city = models.CharField(max_length=50)
    state = models.CharField(max_length=2, validators=[validate_state])
    zip_code = models.CharField(max_length=5)
    marital_status = models.CharField(max_length=20)
    cancer_type = models.CharField(max_length=50)
    date_diagnosed = models.DateField()
    treatment_location = models.CharField(max_length=100)
    doctor_name = models.CharField(max_length=50)
    doctor_phone = models.CharField(max_length=10, validators=[validate_phone])
    household = models.JSONField()
    total_supporting_income = models.DecimalField(max_digits=10, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)


class Request(models.Model):
    applicant = models.ForeignKey(Applicant, on_delete=models.CASCADE)
    statement_of_need = models.CharField(max_length=1000)
    requested_by = models.ForeignKey(CfcUser, on_delete=models.CASCADE)
    last_updated = models.DateTimeField(auto_now=True)
    status = models.CharField(
        max_length=20, choices=[(s, s) for s in REQUEST_STATUSES], default='Pending'
    )
    is_test = models.BooleanField(default=False)
    amount_approved = models.DecimalField(max_digits=10, decimal_places=2, null=True)
    created_at = models.DateTimeField(auto_now_add=True)


class Bill(models.Model):
    request = models.ForeignKey(Request, on_delete=models.CASCADE)
    type = models.CharField(
        max_length=50, choices=[(b, b) for b in BILL_TYPES], blank=True
    )
    amount_requested = models.DecimalField(max_digits=10, decimal_places=2)
    company = models.CharField(max_length=100)
    street_address = models.CharField(max_length=100)
    street_address_2 = models.CharField(max_length=100, blank=True)
    city = models.CharField(max_length=50)
    state = models.CharField(max_length=2)
    zip_code = models.CharField(max_length=5)
    due_date = models.DateField()
    paid = models.BooleanField(default=False)
    paid_date = models.DateField(null=True, blank=True)
    attachment = models.CharField(max_length=100, blank=True)
    approved = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)


class Approval(models.Model):
    request = models.ForeignKey(Request, on_delete=models.CASCADE)
    approved_by = models.ForeignKey(CfcUser, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
