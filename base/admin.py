from django.contrib import admin
from .models import (
Users, UserPolicies, Category, Company, InsurancePolicy, Claim,  Messages, Payment
)

# Register your models here.
admin.site.register(Users)
admin.site.register(UserPolicies)
admin.site.register(Category)
admin.site.register(Company)
admin.site.register(InsurancePolicy)
admin.site.register(Claim)
admin.site.register(Messages)
admin.site.register(Payment)