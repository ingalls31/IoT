from django.db import models
import rest_framework

# Create your models here.


class Cache(models.Model):
    key = models.TextField(primary_key=True)
    value = models.TextField()
