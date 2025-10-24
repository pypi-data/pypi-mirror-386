
from typing import Iterable

from django.contrib.auth import get_user_model
from django.db.models import Q, QuerySet
from testy.users.models import User
from testy.tests_representation.models import TestResult, TestStepResult
from testy.tests_representation.services.results import TestResultService
from django.contrib.contenttypes.models import ContentType
from testy.core.models import Attachment

from allure_megauploader.models import UploaderConfigV2

UserModel = get_user_model()


class UploaderUserService:

    @classmethod
    def config_list(cls, user: UserModel) -> QuerySet[User]:
        return UploaderConfigV2.objects.filter(
            Q(owner=user) | Q(allowed_users__id=user.id)
        ).distinct()

class ResultsCreator:
    @classmethod
    def create_results(
        cls,
        results: Iterable[TestResult],
        step_results: Iterable[TestStepResult],
        user: User,
    ):
        created_results = TestResultService.result_bulk_create(results, user)
        test_result_ct = ContentType.objects.get_for_model(TestResult)
        for test_result in created_results:
            if attachment_ids := getattr(test_result, 'attachment_ids', None):
                Attachment.objects.filter(
                    id__in=attachment_ids,
                ).update(
                    object_id=test_result.id,
                    content_type=test_result_ct,
                )
        TestStepResult.objects.bulk_create(step_results)
