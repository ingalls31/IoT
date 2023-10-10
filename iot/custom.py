from user import jwts
from django.contrib.auth.backends import ModelBackend
from user.models import Account
from django.contrib.auth.hashers import make_password, check_password

class HeaderValidationMiddleware:
    
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        try:
            authorization = request.headers['Authorization']
            account = jwts.decode(authorization)
            print(account)
            request.account = account
        except Exception as e:
            print(str(e))
        response = self.get_response(request)
        return response
    
class AuthenticationBackend(ModelBackend):
    def authenticate(self, request, email=None, password=None):
        try:
            account = Account.objects.get(email=email)
        except Account.DoesNotExist:
            return None
        if check_password(password, account.password):
            return account
        return None