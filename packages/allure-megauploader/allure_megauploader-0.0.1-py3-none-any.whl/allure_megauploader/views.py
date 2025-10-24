import json
import logging
from pathlib import Path
from uuid import uuid4

import redis
from django.conf import settings
from django.contrib.postgres.aggregates import StringAgg
from django.db import models
from django.db.models import Case, F, OuterRef, Q, Value, When
from django.db.models.functions import Concat
from django.shortcuts import redirect, render, get_object_or_404
from django.utils import timezone
from rest_framework import serializers
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.reverse import reverse
from rest_framework.viewsets import GenericViewSet
from testy.tests_representation.models import Parameter, TestPlan
from testy.users.models import User

from .forms import ParsingSubmitForm, UploaderConfigForm
from .models import ServiceType, UploaderConfigV2, UserTask
from .uploader_lib.serializers import TestPlanPreviewSerializer, UploaderUserSerializer
from .uploader_lib.services import UploaderUserService
from .uploader_lib.tasks import process_allure_task, upload_task
from .uploader_lib.utils import ConcatSubquery
from .utils import config_from_json_snapshot, get_md5_from_value, upload_file_to_system


class TaskViewSet(GenericViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = serializers.Serializer
    swagger_schema = None

    @action(
        methods=['get'],
        url_path='tasks',
        url_name='list',
        detail=False,
    )
    def task_list(self, request):
        tasks = UserTask.objects.filter(user=request.user).order_by('-created_at')
        return render(request, 'v2_task_list.html', context={'tasks': tasks})

    @action(
        methods=['get', 'post'],
        url_path=r'tasks/(?P<pk>\d+)/delete',
        url_name='delete',
        detail=False,
    )
    def configs_delete(self, request, pk):
        task = get_object_or_404(UserTask, pk=pk)
        if request.method == 'POST':
            task.delete()
            return redirect('plugins:allure_uploader_v2:task-list')
        return render(request, 'v2_confirm_delete.html', {'object': task.pk})

    @action(
        methods=['get'],
        url_path='tasks/(?P<task_id>[^/.]+)',
        url_name='status',
        detail=False,
    )
    def task_status(self, request, task_id: str):
        return render(request, 'v2_allure_uploader_task_status.html', {'task_id': task_id})


class ServicesViewSet(GenericViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = serializers.Serializer
    swagger_schema = None

    @action(
        methods=['get'],
        url_path='services',
        url_name='list',
        detail=False,
    )
    def service_list(self, request):
        services = ServiceType.objects.all()
        return render(request, 'v2_service_list.html', context={'services': services})


class UploaderViewSet(GenericViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = serializers.Serializer
    swagger_schema = None

    @action(
        methods=['get'],
        url_path='parse',
        url_name='parse',
        detail=False,
    )
    def parse_report(self, request):
        form = ParsingSubmitForm(request)
        context = {
            'title': 'Parse report',
            'form': form,
            'btn_message': 'submit',
        }
        return render(request, 'v2_uploader_form.html', context)

    @parse_report.mapping.post
    def parse_report_post(self, request):
        form = ParsingSubmitForm(request, request.POST)
        if not form.is_valid():
            return render(request, 'v2_uploader_form.html', {'form': form})
        config_id = form.cleaned_data['config'].id
        allure_url = form.cleaned_data.get('allure_url')
        allure_archive = request.FILES.get('allure_archive')

        tmp_file_dir = Path(settings.MEDIA_ROOT, 'allure-uploader-tmp-files', str(uuid4()))
        archive_path = None
        if allure_archive:
            archive_path = upload_file_to_system(tmp_file_dir, 'report.zip', allure_archive)

        task = process_allure_task.delay(
            allure_url,
            str(tmp_file_dir),
            str(archive_path),
            config_id,
            request.user.pk
        )
        UserTask.objects.create(
            name=f'Parsing report {timezone.now()}',
            user=request.user,
            task_id=task.task_id
        )
        return redirect(reverse('plugins:allure_uploader_v2:task-status', kwargs={'task_id': task.task_id}))

    @action(
        methods=['get', 'post'],
        url_path='upload',
        url_name='upload',
        detail=False,
    )
    def upload_report(self, request):
        redis_data_key = get_md5_from_value(request.user.get_full_name() + str(request.user.id))

        try:
            redis_client = redis.StrictRedis(settings.REDIS_HOST, settings.REDIS_PORT)
        except Exception as err:
            err_msg = f'An error occurred while trying to connect to redis {err}'
            logging.error(err_msg)
            return render(request, 'v2_confirm_page.html', {'processing_status': err_msg})

        content_json = redis_client.get(redis_data_key)

        if not content_json:
            return render(request, 'v2_confirm_page.html', {'processing_status': 'Allure content was not received yet'})

        content = json.loads(content_json)
        report_parsed_at = content.pop('parsed_at')
        config_id = content.pop('config_id')
        config_snapshot = content.pop('config_snapshot', None)
        user_id = content.pop('user_id')
        allure_source = content.pop('allure_source')

        if request.POST.get('submit'):
            task = upload_task.delay(content['content'], config_id, config_snapshot, user_id, allure_source)
            redis_client.delete(redis_data_key)
            UserTask.objects.create(
                name=f'Uploading report {timezone.now()}',
                user=request.user,
                task_id=task.task_id
            )
            return redirect(
                reverse(
                    'plugins:allure_uploader_v2:task-status',
                    kwargs={'task_id': task.task_id},
                )
            )

        if request.POST.get('decline'):
            redis_client.delete(redis_data_key)

        config = config_from_json_snapshot(config_snapshot) or UploaderConfigV2.objects.get(id=config_id)

        return render(
            request, 'v2_confirm_page.html',
            {
                'parsed_report_json': content_json,
                'suites': content,
                'processing_status': 'Allure content processed successfully',
                'report_parsed_at': report_parsed_at,
                'skip_creating': config.skip_creating_case,
            }
        )


class ConfigViewSet(GenericViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = serializers.Serializer
    swagger_schema = None

    @action(
        methods=['get'],
        url_path='configs',
        url_name='list',
        detail=False,
    )
    def configs(self, request):
        configs = UploaderUserService.config_list(request.user)
        return render(request, 'v2_configs_list.html', context={'configs': configs})

    @action(
        methods=['get'],
        url_path='configs/add',
        url_name='add',
        detail=False,
    )
    def configs_add(self, request):
        form = UploaderConfigForm(request)
        context = {
            'title': 'Add config',
            'form': form,
            'btn_message': 'add',
        }
        return render(request, 'v2_uploaderconfig_form.html', context=context)

    @configs_add.mapping.post
    def configs_add_post(self, request):
        form = UploaderConfigForm(request, request.POST)
        context = {
            'title': 'Add config',
            'form': form,
            'btn_message': 'add',
        }
        if not form.is_valid():
            return render(request, 'v2_uploaderconfig_form.html', context=context)
        form.save()
        return redirect('plugins:allure_uploader_v2:config-list')

    @action(
        methods=['get', 'post'],
        url_path=r'configs/(?P<pk>\d+)/delete',
        url_name='delete',
        detail=False,
    )
    def configs_delete(self, request, pk):
        config = get_object_or_404(UploaderConfigV2, pk=pk)
        if request.method == 'POST':
            config.delete()
            return redirect('plugins:allure_uploader_v2:config-list')
        return render(request, 'v2_confirm_delete.html', {'object': config.verbose_name})

    @action(
        methods=['get'],
        url_path=r'configs/(?P<pk>\d+)/edit',
        url_name='edit',
        detail=False,
    )
    def configs_edit(self, request, pk):
        config = get_object_or_404(UploaderConfigV2, pk=pk)
        form = UploaderConfigForm(request, instance=config)
        context = {
            'title': 'Edit config',
            'form': form,
            'btn_message': 'edit',
        }
        return render(request, 'v2_uploaderconfig_form.html', context=context)

    @configs_edit.mapping.post
    def configs_edit_post(self, request, pk):
        config = get_object_or_404(UploaderConfigV2, pk=pk)
        form = UploaderConfigForm(request, request.POST, instance=config)
        context = {
            'title': 'Edit config',
            'form': form,
            'btn_message': 'edit',
        }
        if not form.is_valid():
            return render(request, 'v2_uploaderconfig_form.html', context=context)
        form.save()
        return redirect('plugins:allure_uploader_v2:config-list')


class UIViewSet(GenericViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = serializers.Serializer
    swagger_schema = None

    @action(
        methods=['get'],
        url_path='parameters',
        url_name='parameters',
        detail=False,
    )
    def parameters(self, request):
        project_id = request.query_params.get('project')
        parameters = Parameter.objects.filter(project=project_id).extra(select={'title': 'data'}).values(
            'group_name',
            'id',
            'title'
        )
        return Response(data=parameters)

    @action(
        methods=['get'],
        url_path='users',
        url_name='users',
        detail=False,
    )
    def users(self, request):
        qs = User.objects.filter(is_active=True)
        return Response(UploaderUserSerializer(qs, many=True).data)

    @action(
        methods=['get'],
        url_path='plans',
        url_name='plans',
        detail=False,
    )
    def load_plans(self, request):
        project_id = request.query_params.get('project')

        title_annotation = Case(
            When(
                parameter_str__isnull=False,
                then=Concat(
                    F('name'),
                    Value(' '),
                    Value('['),
                    F('parameter_str'),
                    Value(']'),
                    output_field=models.TextField()
                )
            ),
            default=F('name'),
            output_field=models.TextField()
        )

        parent_title_subquery = TestPlan.objects.filter(
            Q(path__ancestor=OuterRef('parent__path')) | Q(id=OuterRef('parent__id'))
        ).order_by('path').annotate(
            parameter_str=StringAgg('parameters__data', delimiter=', ', output_field=models.TextField()),
            title=title_annotation
        ).values('title')

        plans = TestPlan.objects.annotate(
            parameter_str=StringAgg('parameters__data', delimiter=', ', output_field=models.TextField()),
            title=title_annotation,
            parent_title=ConcatSubquery(
                parent_title_subquery,
                separator='->',
                output_field=models.TextField()
            ),
        ).filter(project_id=project_id, is_archive=False)

        return Response(data=TestPlanPreviewSerializer(plans, many=True).data)


def redirect_index(request):
    return redirect(reverse('plugins:allure_uploader_v2:config-list'))
