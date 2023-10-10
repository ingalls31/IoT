from django.shortcuts import render
import jwt
from rest_framework.decorators import api_view, action
from rest_framework.response import Response
from django.db.models import Q
from django.shortcuts import redirect, reverse
from django.http import JsonResponse
from django.forms.models import model_to_dict
from django.db.models import ForeignKey 
from rest_framework.viewsets import ViewSet, ModelViewSet, GenericViewSet
from rest_framework.parsers import FormParser, MultiPartParser, JSONParser
from django.contrib.sessions.backends.db import SessionStore
from drf_spectacular.utils import extend_schema, extend_schema_serializer, extend_schema_view
from django.http import HttpResponse
from django.core.mail import send_mail
import os
from django.core.cache import cache
from django.db.models import Q
from .serializers import AccountSerializer, EmailSerializer
from .models import Account, JwtToken
from rest_framework import serializers, status
from . import jwts
from django.contrib.auth import authenticate



@extend_schema(tags=["Account"])
class AccountController(ViewSet):
    parser_classes = (JSONParser, MultiPartParser)
    serializer_class = AccountSerializer
    
    @extend_schema(
        request=AccountSerializer
    )
    @action(detail=False, methods=['POST'])
    def register(self, request): 
        print(request.data)
        data = AccountSerializer(data=request.data)
        if data.is_valid(): 
            try:
                Account.objects.create_account(email=data.validated_data['email'], password=data.validated_data['password'])
                return Response({"Response": "Success"}, status=status.HTTP_200_OK)
            except: 
                return Response({"Response": "Failed"}, status=status.HTTP_400_BAD_REQUEST)
        return Response({"Response": "Failed"}, status=status.HTTP_400_BAD_REQUEST)

    @extend_schema(
        request=AccountSerializer
    )
    @action(detail=False, methods=['POST'])
    def login(self, request):
        data=AccountSerializer(data=request.data)
        data.is_valid(raise_exception=True)
        account = Account.objects.verifycation(
            email=data.validated_data['email'],
            password=data.validated_data['password']
        )
        if not account:
            return Response({"Response": "Failed"}, status=status.HTTP_400_BAD_REQUEST)
        try:
            JwtToken.objects.filter(account=account).delete()
        except:
            pass
        access = jwts.get_access_token({"email": account.email})
        JwtToken.objects.create(
            account=account,
            access=access, 
        )
        return Response({"access": access}, status=status.HTTP_200_OK)
    
    @extend_schema(
        description='Logout'
    )
    @action(detail=False, methods=['GET'])
    def logout(self, request): 
        try:
            account = request.account
        except:
            return Response({"Response": "Failed"}, status=status.HTTP_400_BAD_REQUEST)
        try:
            JwtToken.objects.filter(account=account).delete()
            return Response({"Response": "Success"}, status=status.HTTP_200_OK)
        except:
            return Response({"Response": "Failed"}, status=status.HTTP_400_BAD_REQUEST)
    

     