from django.contrib import admin
from .models import CfcUser, ApprovedUser, Request, Bill
from django.contrib.auth.admin import UserAdmin
from django.contrib.admin import ModelAdmin


@admin.register(CfcUser)
class CfcUserAdmin(UserAdmin):
    pass

@admin.register(ApprovedUser)
class ApprovedUserAdmin(ModelAdmin):
    pass
