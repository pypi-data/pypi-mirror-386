
from pathlib import Path
from uuid import uuid4

from django.conf import settings
from django.utils import timezone
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework import status, viewsets, mixins
from rest_framework.generics import get_object_or_404
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from testy.paginations import StandardSetPagination

from allure_megauploader.api.serializers import (
    AllureUploaderConfigV2Serializer,
    AllureUploaderSerializerV2,
    APITaskResponseSerializerV2,
    UserTaskSerializer,
)
from allure_megauploader.models import UploaderConfigV2, UserTask
from allure_megauploader.swagger import tasks_list_schema
from allure_megauploader.uploader_lib.tasks import upload_api_task
from allure_megauploader.utils import upload_file_to_system


class AllureUploaderViewSet(APIView):
    permission_classes = [IsAuthenticated, ]
    schema_tags = ['Allure uploader v2']

    @swagger_auto_schema(
        request_body=AllureUploaderSerializerV2,
        responses={200: APITaskResponseSerializerV2},
    )
    def post(self, request):
        serializer = AllureUploaderSerializerV2(data=request.data)
        serializer.is_valid(raise_exception=True)
        archive_path = None
        tmp_file_dir = Path(settings.MEDIA_ROOT, 'allure-uploader-tmp-files', str(uuid4()))
        if allure_archive := serializer.validated_data.pop('allure_file', None):
            archive_path = upload_file_to_system(tmp_file_dir, 'report.zip', allure_archive)
        task = upload_api_task.delay(
            str(tmp_file_dir),
            str(archive_path),
            serializer.data,
            request.user.id,
        )
        UserTask.objects.create(
            name=f'Api parsing {timezone.now()}',
            user=request.user,
            task_id=task.task_id
        )
        return Response(data=APITaskResponseSerializerV2({'task_id': task.id}).data, status=status.HTTP_200_OK)


class UploaderConfigViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated, ]
    serializer_class = AllureUploaderConfigV2Serializer
    queryset = UploaderConfigV2.objects.all()
    schema_tags = ['Allure uploader v2']


@tasks_list_schema
class UserTaskView(viewsets.GenericViewSet, mixins.ListModelMixin, mixins.RetrieveModelMixin, mixins.DestroyModelMixin):
    permission_classes = [IsAuthenticated]
    serializer_class = UserTaskSerializer
    queryset = UserTask.objects.none()
    schema_tags = ['Allure uploader v2']
    pagination_class = StandardSetPagination

    def get_queryset(self):
        status = self.request.query_params.get('status')
        if status is not None:
            return UserTask.objects.filter(user=self.request.user, status__icontains=status).order_by('-created_at')
        return UserTask.objects.filter(user=self.request.user).order_by('-created_at')

    @swagger_auto_schema(
        manual_parameters=[
            openapi.Parameter(
                'id',
                openapi.IN_PATH,
                type=openapi.TYPE_STRING,
                description='UUID of task',
                required=True,
            ),
        ],
    )
    def retrieve(self, request, pk=None, *args, **kwargs):
        instance = get_object_or_404(UserTask, task_id=pk, user=self.request.user)
        serializer = self.get_serializer(instance)
        return Response(serializer.data)
