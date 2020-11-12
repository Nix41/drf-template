from django.urls import include, path

from .views import ConfigView

urlpatterns = [
    path('', ConfigView.as_view()),
    path('reset_password/', include('django_rest_passwordreset.urls',
                                    namespace='client_password_reset'))
]
