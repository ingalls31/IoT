from typing import Any
from django.db import models
from django.contrib.auth.hashers import make_password, check_password
import uuid

# Create your models here.

class AccountManager(models.Manager):
    def create_account(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("Email must be set.")
        if self.filter(email=email).exists():
            raise ValueError("Email already exists.")
        account = Account.objects.create(
            email=email,
            password=make_password(password), 
        )
        return account
    def change_password(self, email, password):
        account = Account.objects.get(email=email)
        account.password = make_password(password)
        account.save()
        return account
    def verifycation(self, email=None, password=None):
        try:
            account = Account.objects.get(email=email)
        except Account.DoesNotExist:
            return None
        if check_password(password, account.password):
            return account
        return None
    

class Role(models.Model): 
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255, null=True)
    
    def __str__(self) -> str:
        return self.name
    class Meta: 
        db_table = 'role'

class Account(models.Model):
    email = models.EmailField(primary_key=True, unique=True)
    password = models.CharField(max_length=32)
    roles = models.ManyToManyField(Role, blank=True)
    
    objects = AccountManager()
    class Meta:
        db_table = 'account' 
        
        
class VerifyToken(models.Model):
    account = models.OneToOneField(
        Account, on_delete=models.CASCADE, null=True
    )
    token = models.CharField(max_length=8, null=True, blank=True)
    
    class Meta:
        db_table = 'verify_token'

class JwtToken(models.Model):
    account = models.OneToOneField(
        Account, on_delete=models.CASCADE, null=True
    )
    access = models.TextField()
    
    class Meta: 
        db_table = 'jwt_token'
