from rest_framework.throttling import UserRateThrottle, AnonRateThrottle

class LoginAnonThrottle(AnonRateThrottle):
    scope = "login_anon"

class LoginUserThrottle(UserRateThrottle):
    scope = "login_user"

class OrderCreateThrottle(AnonRateThrottle):
    scope = "order_create"

class ChatbotThrottle(UserRateThrottle):
    scope = "chatbot"

class RegisterThrottle(UserRateThrottle):
    scope = "register"

class PasswordResetThrottle(UserRateThrottle):
    scope = "password_reset"