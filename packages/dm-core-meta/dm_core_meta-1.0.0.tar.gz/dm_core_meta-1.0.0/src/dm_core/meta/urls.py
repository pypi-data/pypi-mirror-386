from django.urls import path, re_path
from .views import AppConfigListApi, AppConfigUpdateApi

urlpatterns = [
    re_path(r'^app-config/(?P<pk>[a-zA-Z0-9]{1,255})/v1', AppConfigUpdateApi.as_view(), name='app-config-update'),
    path('app-config/v1', AppConfigListApi.as_view(), name='app-config-list'),
]