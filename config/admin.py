from django.contrib import admin
from solo.admin import SingletonModelAdmin

from .models import Config

# Register your models here.
admin.site.register(Config, SingletonModelAdmin)
