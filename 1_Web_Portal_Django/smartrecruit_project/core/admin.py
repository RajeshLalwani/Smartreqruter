from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User

# Register the Custom User Model
admin.site.register(User, UserAdmin)
