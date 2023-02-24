from .models import Watchtdog
from django.contrib import admin


# Register your models here.

@admin.register(Watchtdog)
class AuthorAdmin(admin.ModelAdmin):
    pass
