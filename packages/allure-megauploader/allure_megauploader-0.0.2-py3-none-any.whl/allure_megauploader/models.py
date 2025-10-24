from django.contrib.auth import get_user_model
from django.contrib.postgres.fields import ArrayField
from django.db import models
from testy.core.models import Project
from testy.root.models import BaseModel
from testy.tests_representation.models import Parameter, TestPlan

UserModel = get_user_model()


def default_labels() -> list[str]:
    return ['autotest']


class TaskStatus(models.TextChoices):
    FAILED = 'FAILED'
    SUCCESS = 'SUCCESS'
    IN_PROGRESS = 'IN_PROGRESS'


class ServiceType(BaseModel):
    verbose_name = models.CharField(max_length=255)
    service_code = models.IntegerField()
    description = models.CharField(max_length=255, null=True, blank=True)

    def __str__(self):
        return self.verbose_name


class UploaderConfigV2(BaseModel):
    project = models.ForeignKey(Project, on_delete=models.CASCADE)
    service = models.ForeignKey(ServiceType, on_delete=models.SET_NULL, null=True)
    plan = models.ForeignKey(TestPlan, on_delete=models.SET_NULL, null=True)
    child_plan = models.CharField(max_length=255, blank=True)
    parameters = models.ManyToManyField(Parameter, blank=True)
    auto_suite_name = models.CharField(max_length=255, blank=True, default='auto')
    jira_projects = models.CharField(max_length=255, blank=True)
    custom_attributes = models.TextField(blank=True)
    envs_to_parse = models.TextField(blank=True)
    additional_parameters = models.JSONField(default=dict, blank=True)
    verbose_name = models.CharField(max_length=255)
    owner = models.ForeignKey(UserModel, on_delete=models.CASCADE)
    allowed_users = models.ManyToManyField(UserModel, blank=True, related_name='allowed_users')
    labels = ArrayField(models.CharField(max_length=255), default=default_labels)
    add_allure_source = models.BooleanField(default=False)
    skip_creating_case = models.BooleanField(default=False)

    def __str__(self):
        return self.verbose_name


class UserTask(BaseModel):
    user = models.ForeignKey(UserModel, on_delete=models.CASCADE)
    task_id = models.CharField(max_length=255)
    name = models.CharField(max_length=255)
    plan = models.ForeignKey(TestPlan, on_delete=models.SET_NULL, null=True)
    status = models.CharField(default=TaskStatus.IN_PROGRESS, choices=TaskStatus.choices)
    error = models.CharField(null=True)
