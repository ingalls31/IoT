from django.urls import path, include
from . import views
from .views import AccountController
from rest_framework.routers import DefaultRouter

router = DefaultRouter() 
router.register(r"account", AccountController, basename="account")


urlpatterns = [
    path("", include(router.urls)),
]