import json
import logging
import time


user_logger = logging.getLogger("user_activity")
login_log = logging.getLogger("login_attempt")


def get_client_ip(request):
    x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
    if x_forwarded_for:
        return x_forwarded_for.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR", "unknown")


class UserActivityMiddleware:
    EXCLUDED_PATHS = {"/users/auth/login/"}

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        start_time = time.perf_counter()
        response = self.get_response(request)
        duration = time.perf_counter() - start_time

        if request.path not in self.EXCLUDED_PATHS:
            user = request.user if getattr(request.user, "is_authenticated", False) else "Anonymous"

            user_logger.info(
                f"USER={user} | METHOD={request.method} | PATH={request.path} | "
                f"STATUS={response.status_code} | DURATION={duration:.3f}s | "
                f"IP={get_client_ip(request)}"
            )

        return response


class LoginAttemptMiddleware:
    LOGIN_URL = "/users/auth/login/"

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.path == self.LOGIN_URL and request.method == "POST":
            try:
                request._body_copy = request.body
            except Exception:
                request._body_copy = b"{}"

        response = self.get_response(request)

        if request.path == self.LOGIN_URL and request.method == "POST":
            self._log_attempt(request, response)

        return response

    def _log_attempt(self, request, response):
        username = "unknown"

        try:
            body = json.loads(request._body_copy.decode("utf-8"))
            username = body.get("username") or body.get("email") or "unknown"
        except (json.JSONDecodeError, UnicodeDecodeError, AttributeError):
            pass

        if response.status_code == 200:
            login_log.info(
                f"LOGIN SUCCESS | username={username} | ip={get_client_ip(request)}"
            )
        elif response.status_code in (400, 401, 403):
            login_log.warning(
                f"FAILED LOGIN | username={username} | ip={get_client_ip(request)} "
                f"| status={response.status_code}"
            )