from django.db import models
from django.contrib.auth.models import User


class Users(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    verified = models.BooleanField(default=False)
    name = models.CharField(max_length=100)
    username = models.CharField(max_length=50, unique=True)
    email = models.EmailField(max_length=100, unique=True, null=True)
    location = models.CharField(max_length=100, null=True, blank=True)
    bio_picture = models.URLField(max_length=200, null=True, blank=True)
    

    def __str__(self):
        return f"{self.username}"
     


class Category(models.Model):
    name = models.CharField(max_length=30, unique=True)
    created_date = models.DateField(auto_now_add=True)

    def __str__(self):
        return self.name


class Company(models.Model):
    company_category = models.ForeignKey(Category, on_delete=models.PROTECT)
    admin = models.ForeignKey(Users, on_delete=models.PROTECT)
    name = models.CharField(max_length=50, unique=True)
    allow_policies = models.BooleanField(default=True)
    description = models.TextField(max_length=2000)
    rating = models.DecimalField(
        default=3.0, max_digits=3, decimal_places=1, editable=False)  # Support ratings like 4.5
    logo = models.URLField(max_length=500, null=True, blank=True)
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    availability = models.BooleanField(default=True)
    creation_date = models.DateField(auto_now_add=True)
    

    def __str__(self):
        return self.name


class InsurancePolicy(models.Model):
    company = models.ForeignKey(Company, on_delete=models.PROTECT)
    name = models.CharField(max_length=50)
    description = models.TextField()
    coverage_amount = models.DecimalField(max_digits=15, decimal_places=2)  # Insurance amount
    premium = models.DecimalField(max_digits=10, decimal_places=2)  # Monthly premium
    duration = models.CharField(max_length=100)  #use dropdown to select option in flutter frontend
    is_active = models.BooleanField(default=True)
    # rating = models.DecimalField(
    #     default=3.0, max_digits=3, decimal_places=1, editable=False)


    def __str__(self):
        return f"{self.name})"




class Claim(models.Model):
    policy = models.ForeignKey(InsurancePolicy, on_delete=models.PROTECT)
    claimant = models.ForeignKey(Users, on_delete=models.PROTECT, related_name='claims')
    claim_number = models.CharField(max_length=50, unique=True)
    description = models.TextField()
    claim_amount = models.DecimalField(max_digits=15, decimal_places=2)
    status = models.CharField(max_length=20, choices=[('Pending', 'Pending'), ('Approved', 'Approved'), ('Denied', 'Denied')], default='Pending')
    claim_date = models.DateField(auto_now_add=True)
    approval_date = models.DateField(null=True, blank=True)

    def __str__(self):
        return f"Claim {self.claim_number} - {self.status}"



class UserPolicies(models.Model):
    user = models.ForeignKey(User, on_delete=models.PROTECT)
    policy = models.ForeignKey(InsurancePolicy, on_delete=models.PROTECT)
    status = models.CharField(max_length=20, choices=[('Active', 'Active'), ('On Pause', 'On Pause'), ('Complete', 'Complete')], default='Active')
   



class Messages(models.Model):
    sender = models.ForeignKey(Users, on_delete=models.PROTECT, related_name='sent_messages')
    receiver = models.ForeignKey(Users, on_delete=models.PROTECT, related_name='received_messages')
    message = models.TextField(max_length=1000)
    read_status = models.BooleanField(default=False)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Message from {self.sender.name} to {self.receiver.name} at {self.timestamp}"


class Payment(models.Model):
    claim = models.ForeignKey(Claim, on_delete=models.PROTECT)
    amount = models.DecimalField(max_digits=15, decimal_places=2)
    payment_date = models.DateField(auto_now_add=True)
    is_paid = models.BooleanField(default=False)

    def __str__(self):
        return f"Payment of {self.amount} for {self.claim.claim_number}"
