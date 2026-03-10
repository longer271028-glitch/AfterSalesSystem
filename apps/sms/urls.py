from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import PhoneViewSet, SmsRecordViewSet, sms_management_view

router = DefaultRouter()
router.register(r'phones', PhoneViewSet, basename='phone')
router.register(r'records', SmsRecordViewSet, basename='sms-record')

urlpatterns = [
    path('', include(router.urls)),
]
