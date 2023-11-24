import boto3
from django.shortcuts import render


def index(request):
    return render(request, 'base.html', context={'text': 'Hello world'})


def lobby(request):
    return render(request, 'lobby.html')
