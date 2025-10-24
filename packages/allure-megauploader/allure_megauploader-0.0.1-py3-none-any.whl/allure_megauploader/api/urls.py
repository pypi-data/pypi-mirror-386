
from django.urls import path
from rest_framework.routers import SimpleRouter

from allure_megauploader.api import views

router = SimpleRouter()
router.register('configs', views.UploaderConfigViewSet)
router.register('tasks', views.UserTaskView)
urlpatterns = [
    path('upload-report/', views.AllureUploaderViewSet.as_view(), name='parse-report')
]

urlpatterns += router.urls
