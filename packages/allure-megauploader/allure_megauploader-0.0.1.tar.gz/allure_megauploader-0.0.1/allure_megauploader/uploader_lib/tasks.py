
import datetime
import json
import logging
from dataclasses import dataclass
from datetime import timedelta
from pathlib import Path
from typing import Any

import redis
from celery import shared_task
from celery.exceptions import Ignore
from django.conf import settings
from django.contrib.auth import get_user_model
from django.db import transaction

from allure_megauploader.models import TaskStatus, UploaderConfigV2, UserTask
from allure_megauploader.uploader_lib.utils import ProgressRecorderContext
from allure_megauploader.utils import config_from_json_snapshot, config_json_snapshot, get_md5_from_value

from .downloader import Downloader
from .implementations.parsers import (
    ParserDataServices,
    ParserFSTEK,
    ParserUnique,
    ParserV2,
    TestyParser,
    TestyParserOptimised,
)
from .implementations.uploaders import (
    TestyUploader,
    TestyUploaderOptimised,
    UploaderDataServices,
    UploaderFSTEK,
    UploaderUnique,
    UploaderV2,
)
from .parser import ParserBase
from .services import ResultsCreator
from .uploader import UploaderBase

UserModel = get_user_model()

logger = logging.getLogger('uploader-tasks')


@dataclass
class Configuration:
    parser: type[ParserBase]
    uploader: type[UploaderBase]


service_configuration_dict = {
    1: Configuration(ParserV2, UploaderV2),
    2: Configuration(ParserDataServices, UploaderDataServices),
    3: Configuration(ParserUnique, UploaderUnique),
    4: Configuration(TestyParser, TestyUploader),
    5: Configuration(TestyParserOptimised, TestyUploaderOptimised),
    6: Configuration(ParserFSTEK, UploaderFSTEK),
}


@shared_task(bind=True)
def process_allure_task(
    self,
    allure_url: str,
    tmp_file_dir: str,
    archive_path: str | None,
    config_id: int,
    user_id: int,
):
    try:
        progress_recorder = ProgressRecorderContext(self, total=6, description='Upload started')

        tmp_file_dir = Path(tmp_file_dir)
        if archive_path:
            archive_path = Path(archive_path)

        with transaction.atomic():
            config: UploaderConfigV2 = UploaderConfigV2.objects.get(pk=config_id)

            service_code = config.service.service_code if config.service else 1

            service_configuration = service_configuration_dict.get(
                service_code,
                service_configuration_dict[1]
            )

            parser_class = service_configuration.parser
            uploader_class = service_configuration.uploader

            with Downloader(
                progress_recorder,
                tmp_file_dir,
                allure_url=allure_url,
                archive_path=archive_path
            ) as allure_dir:
                if isinstance(allure_dir, Exception):
                    raise Ignore(f'Error occurred, caused by error: {str(allure_dir)}') from allure_dir
                parser = parser_class(
                    progress_recorder,
                    config,
                    allure_dir,
                    config.jira_projects,
                    config.envs_to_parse,
                    config.custom_attributes,
                )
                parsed_cases = parser.parse_cases()

                content = uploader_class(progress_recorder).find_existing_elements(
                    parsed_cases,
                    config.project,
                    config.auto_suite_name,
                    labels=[{'name': label_name} for label_name in config.labels],
                    user_id=user_id,
                    config=config,
                    task_id=self.request.id,
                    allure_source=allure_url,
                )

            gathered = {
                'content': content,
                'config_id': config_id,
                'config_snapshot': config_json_snapshot(config),
                'user_id': user_id,
                'allure_source': allure_url,
                'parsed_at': datetime.datetime.now().strftime('%m/%d/%Y, %H:%M:%S')
            }
            user = UserModel.objects.get(pk=user_id)
            unique_user_key = get_md5_from_value(user.get_full_name() + str(user.id))
            results_json = json.dumps(gathered, indent=2)

            try:
                redis_client = redis.StrictRedis(settings.REDIS_HOST, settings.REDIS_PORT)
            except Exception as err:
                logger.error(f'An error occurred while trying to connect to redis {err}')
                raise err

            redis_client.set(unique_user_key, results_json)

            redis_client.expire(unique_user_key, timedelta(minutes=30))
            UserTask.objects.filter(task_id=self.request.id).update(status=TaskStatus.SUCCESS)
    except Exception as err:
        msg = str(err)
        UserTask.objects.filter(task_id=self.request.id).update(status=TaskStatus.FAILED, error=msg)
        raise Ignore(msg) from err


@shared_task(bind=True)
def upload_task(self, content: dict[str, Any], config_id, config_snapshot, user_id, allure_source):
    try:
        config = config_from_json_snapshot(config_snapshot) or UploaderConfigV2.objects.get(pk=config_id)
        user = UserModel.objects.get(pk=user_id)
        service_code = config.service.service_code if config.service else 1
        service_configuration = service_configuration_dict.get(
            service_code,
            service_configuration_dict[1]
        )

        uploader_class = service_configuration.uploader

        progress_recorder = ProgressRecorderContext(self, total=5)

        plan = config.plan
        parameters = config.parameters.all() if config.parameters else None
        if config.child_plan:
            plan = uploader_class.find_or_create_plan(
                parent=plan,
                plan_name=config.child_plan,
                project=config.project,
                parameters=parameters,
            )

        results_to_create = []
        steps_to_create = []
        with transaction.atomic():
            progress_recorder.progress_step('Creating result instances.')
            for suite_name, suite_info in content.items():
                result_instances = uploader_class(progress_recorder).create_result_instances(
                    suite_name,
                    suite_info=suite_info,
                    config=config,
                    user=user,
                    plan=plan,
                    allure_source=allure_source,
                )
                if isinstance(result_instances, tuple):
                    results, step_results = result_instances
                else:
                    results = result_instances
                    step_results = []
                results_to_create.extend(results)
                steps_to_create.extend(step_results)
            ResultsCreator.create_results(results_to_create, steps_to_create, user)
            UserTask.objects.filter(task_id=self.request.id).update(plan=plan, status=TaskStatus.SUCCESS)
    except Exception as err:
        msg = str(err)
        UserTask.objects.filter(task_id=self.request.id).update(status=TaskStatus.FAILED, error=msg)
        raise Ignore(msg) from err


@shared_task(bind=True)
def upload_api_task(
    self,
    tmp_file_dir: str,
    archive_path: str | None,
    data: dict[str, Any],
    user_id: int,
):
    try:
        progress_recorder = ProgressRecorderContext(self, total=5)

        config: UploaderConfigV2 = UploaderConfigV2.objects.get(pk=data.get('config'))

        tmp_file_dir = Path(tmp_file_dir)
        if archive_path:
            archive_path = Path(archive_path)

        service_configuration = service_configuration_dict.get(
            config.service.service_code,
            service_configuration_dict[1]
        )

        uploader_class = service_configuration.uploader
        parser_class = service_configuration.parser
        plan = config.plan

        project = config.project
        user = UserModel.objects.get(pk=user_id)

        results_to_create = []
        steps_to_create = []
        with transaction.atomic():
            with Downloader(
                progress_recorder,
                tmp_file_dir,
                allure_url=data.get('allure_url'),
                archive_path=archive_path
            ) as allure_dir:
                if isinstance(allure_dir, Exception):
                    raise Ignore(f'Error occurred, caused by error: {str(allure_dir)}') from allure_dir
                parser = parser_class(
                    progress_recorder,
                    config,
                    allure_dir,
                    data.get('jira_projects'),
                    data.get('envs_to_parse'),
                    config.custom_attributes,
                )
                parsed_cases = parser.parse_cases()
                if plans_hierarchy := data.get('plans_hierarchy'):
                    plans_hierarchy = plans_hierarchy.split(data['hierarchy_separator'])
                    plan = uploader_class.create_plans_hierarchy(plan, plans_hierarchy)

                content = uploader_class(progress_recorder).find_existing_elements(
                    parsed_cases,
                    project,
                    config.auto_suite_name,
                    labels=[{'name': label_name} for label_name in config.labels],
                    user_id=user_id,
                    config=config,
                    plan=plan,
                    allure_source=data.get('allure_url'),
                )

                progress_recorder.progress_step('Creating result instances.')

                for suite_name, suite_info in content.items():
                    result_instances = uploader_class(progress_recorder).create_result_instances(
                        suite_name,
                        suite_info=suite_info,
                        config=config,
                        user=user,
                        plan=plan,
                        allure_source=data.get('allure_url'),
                    )
                    if isinstance(result_instances, tuple):
                        results, step_results = result_instances
                    else:
                        results = result_instances
                        step_results = []
                    results_to_create.extend(results)
                    steps_to_create.extend(step_results)
                ResultsCreator.create_results(results_to_create, steps_to_create, user)
                UserTask.objects.filter(task_id=self.request.id).update(plan=plan, status=TaskStatus.SUCCESS)
    except Exception as err:
        msg = str(err)
        UserTask.objects.filter(task_id=self.request.id).update(status=TaskStatus.FAILED, error=msg)
        raise Ignore(msg) from err
