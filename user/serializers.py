from rest_framework import serializers
from django.core.exceptions import ValidationError
import re

class AccountSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(max_length=100)
    
class EmailSerializer(serializers.Serializer):
    email = serializers.EmailField()