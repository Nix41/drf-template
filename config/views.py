from django.shortcuts import render
from rest_framework.generics import RetrieveUpdateAPIView

from config import serializers

from .models import Config
from .permissions import SettingsPermission

# Create your views here.


class ConfigView(RetrieveUpdateAPIView):
    permission_classes = [SettingsPermission]
    serializer_class = serializers.ConfigSerializer

    def get_object(self):
        return Config.objects.get()
