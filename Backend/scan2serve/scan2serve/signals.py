# myproject/signals.py
import logging
from django.contrib.auth.signals import (
    user_logged_in,
    user_logged_out,
    user_login_failed,
)
from django.dispatch import receiver

user_log = logging.getLogger('user_activity')

@receiver(user_logged_in)
def on_login(sender, request, user, **kwargs):
    ip = (
        request.META.get('HTTP_X_FORWARDED_FOR', '').split(',')[0]
        or request.META.get('REMOTE_ADDR')
    )
    user_log.info(
        f"LOGIN | user={user.username} | email={user.email} | ip={ip}"
    )

@receiver(user_logged_out)
def on_logout(sender, request, user, **kwargs):
    ip = (
        request.META.get('HTTP_X_FORWARDED_FOR', '').split(',')[0]
        or request.META.get('REMOTE_ADDR')
    )
    user_log.info(
        f"LOGOUT | user={user.username} | ip={ip}"
    )

@receiver(user_login_failed)
def on_login_failed(sender, credentials, request, **kwargs):
    ip = (
        request.META.get('HTTP_X_FORWARDED_FOR', '').split(',')[0]
        or request.META.get('REMOTE_ADDR')
    )
    user_log.warning(
        f"FAILED LOGIN | username={credentials.get('username')} | ip={ip}"
    )