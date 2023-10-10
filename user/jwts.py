import jwt
import random
import string
from django.conf import settings
from datetime import datetime, timedelta
from .models import Account



def get_access_token(payload):
    return jwt.encode(
        {"exp": datetime.utcnow() + timedelta(days=30), **payload},
        settings.SECRET_KEY,
        algorithm="HS256"
    )

def decode(authorization):
    if not authorization:
        return None
    token = authorization[7:]
    decoded = jwt.decode(token, key=settings.SECRET_KEY, algorithms="HS256")
    try:
        return Account.objects.get(email=decoded["email"])
    except Exception:
        return None