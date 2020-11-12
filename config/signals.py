from django.core.mail import EmailMessage
from django.dispatch import receiver
from django.template.loader import get_template
from django.urls import reverse
from django_rest_passwordreset.signals import reset_password_token_created


@receiver(reset_password_token_created)
def password_reset_token_created(sender, instance, reset_password_token, *args, **kwargs):
    """
    Handles password reset tokens
    When a token is created, an e-mail needs to be sent to the user
    :param sender: View Class that sent the signal
    :param instance: View Instance that sent the signal
    :param reset_password_token: Token Model Object
    :param args:
    :param kwargs:
    :return:
    """
    # send an e-mail to the user
    context = {
        'user_name': reset_password_token.user.full_name,
        'url': 'http://' + instance.request.headers['Host'] + '/new_password/' + reset_password_token.key
    }
    message = get_template('mailing/recover.html').render(context)
    subject = "Recuperar Contraseña"
    msg = EmailMessage(subject, message, to=[reset_password_token.user.email])
    msg.content_subtype = 'html'
    msg.send()
