from django.urls import include, path
from rest_framework.routers import SimpleRouter

from . import views

router = SimpleRouter()
router.register('', views.TaskViewSet, basename='task')
router.register('', views.ServicesViewSet, basename='service')
router.register('', views.UploaderViewSet, basename='uploader')
router.register('', views.ConfigViewSet, basename='config')
router.register('', views.UIViewSet, basename='ui')
urlpatterns = [
    path('', views.redirect_index),
    path('api/', include('allure_uploader_v2.api.urls'))
]
urlpatterns += router.urls
