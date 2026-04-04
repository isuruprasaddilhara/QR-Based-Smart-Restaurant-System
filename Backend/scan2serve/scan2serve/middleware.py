import logging
import time

user_logger = logging.getLogger('user_activity')

class UserActivityMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        start_time = time.time()

        response = self.get_response(request)

        duration = time.time() - start_time
        user = request.user if request.user.is_authenticated else 'Anonymous'

        user_logger.info(
            f"USER={user} | METHOD={request.method} | PATH={request.path} | "
            f"STATUS={response.status_code} | DURATION={duration:.3f}s | "
            f"IP={self.get_client_ip(request)}"
        )

        return response

    def get_client_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        return x_forwarded_for.split(',')[0] if x_forwarded_for else request.META.get('REMOTE_ADDR')