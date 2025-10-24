
from abc import ABC, abstractmethod
from copy import deepcopy
from datetime import timedelta
from typing import Any

from dateutil.relativedelta import relativedelta
from django.contrib.auth import get_user_model
from django.db.models import Count, QuerySet
from django.utils import timezone
from testy.core.models import Project
from testy.tests_description.models import TestCase, TestSuite
from testy.tests_description.services.cases import TestCaseService
from testy.tests_representation.choices import ResultStatusType
from testy.tests_representation.models import Parameter, ResultStatus, Test, TestPlan, TestResult
from testy.tests_representation.services.results import TestResultService
from testy.users.models import User

from allure_megauploader.models import UploaderConfigV2
from allure_megauploader.uploader_lib.parser import ParsedCase
from allure_megauploader.uploader_lib.utils import ProgressRecorderContext

UserModel = get_user_model()


class UploaderBase(ABC):
    def __init__(self, progress_recorder: ProgressRecorderContext) -> None:
        self.progress_recorder = progress_recorder
        self.mapped_statuses = self._map_statuses()
        super().__init__()

    @classmethod
    def _map_statuses(cls) -> dict[str, ResultStatus]:
        system_statuses_name = ['Failed', 'Passed', 'Skipped', 'Broken', 'Blocked', 'Untested', 'Retest']
        testy_system_statuses = ResultStatus.objects.filter(
            name__in=system_statuses_name,
            project=None,
            type=ResultStatusType.SYSTEM,
        )
        return {result.name.lower(): result for result in testy_system_statuses}

    @abstractmethod
    def create_result_instances(
        self,
        suite_name: str,
        suite_info: dict[str, Any],
        config: UploaderConfigV2,
        user: User,
        plan: TestPlan,
        allure_source: str | None,
    ) -> list[TestResult]:
        return NotImplemented

    @staticmethod
    def find_or_create_plan(
        parent: TestPlan,
        plan_name: str,
        project: Project,
        parameters: QuerySet[Parameter]
    ) -> TestPlan:
        """
        Find or create TestPlan.

        If TestPlan with given parameters was not found create it. If several plans were found select first in list.

        Args:
            parent: TestPlan instance
            plan_name: TestPlan name
            parameters: QuerySet of parameters for child plan
            project: testy Project instance

        Returns:
            TestPlan instance
        """
        parameters_ids = [parameter.id for parameter in parameters]
        found_plans = TestPlan.objects.annotate(count=Count('parameters')).filter(
            count=len(parameters_ids),
            name=plan_name,
            parent=parent,
            project=project,
        )
        for parameter_id in parameters_ids:
            found_plans = found_plans.filter(parameters__pk=parameter_id)

        if not found_plans:
            test_plan = TestPlan.objects.create(
                name=plan_name, parent=parent,
                project=project,
                started_at=timezone.now(),
                due_date=timezone.now() + relativedelta(years=5, days=5)
            )
            test_plan.parameters.set(parameters)
            return test_plan
        return found_plans[0]

    @staticmethod
    def create_suite(suite_name: str, project: Project, auto_suite_name: str) -> TestSuite:
        """
        Create testy TestSuite from parsed info from allure report.

        If auto suite name is provided, create suite inside parsed suite with name auto_suite_name.
        Purpose is to keep automatically generated cases inside separated suite.

        Args:
            suite_name: TestSuite name
            project: testy Project instance
            auto_suite_name: suite name that will be created inside parent suite

        Returns:
            TestSuite instance
        """
        suite = TestSuite.objects.create(name=suite_name, project=project)
        if auto_suite_name:
            suite = TestSuite.objects.create(name=auto_suite_name, parent=suite, project=project)
        return suite

    @classmethod
    def create_case(
        cls,
        case: dict[str, str],
        suite_id: int,
        project: Project,
        labels: list[dict[str, str]] | None = None,
        user: User = None,
    ) -> TestCase:
        """
        Create testy TestCase from parsed info from allure report.

        Args:
            case: case info from parsed allure report.
            suite_id: TestSuite id from TestY
            project: testy Project instance

        Returns:
            TestCase instance
        """
        scenario = case['custom_steps'] if case['custom_steps'] else 'Scenario was not provided'
        if case['test_status'] == 'skipped':
            name_list = case['test_name'].split(':')
            case['test_name'] = ''.join(name_list[1:]) if len(name_list) > 1 else case['test_name']
        case_data = {
            'name': case['test_name'],
            'setup': case['real_test_name'],
            'scenario': scenario,
            'suite': TestSuite.objects.get(pk=suite_id),
            'project': project,
            'description': case['params_str'],
            'user': user,
            'attributes': case['attributes'],
        }

        if labels:
            case_data['labels'] = labels

        return TestCaseService().case_create(data=case_data)

    @abstractmethod
    def find_suite(self, suite_name: Any, project: Project, auto_suite_name: str) -> TestSuite | None:
        """
        Finds list of suites with given parameters.

        Args:
            suite_name: name of suite from parsed allure case
            project: testy Project instance
            auto_suite_name: suite that will be created inside parent suite

        Returns:
            list of dicts containing info about found suites
        """
        return NotImplemented

    @classmethod
    def find_case(
        cls,
        case: ParsedCase,
        suite_id: int,
        project: Project,
        labels: list[str],
        user_id: int,
    ) -> int | None:
        """
        Find case if exists.

        Find case if it exists.
        If status of allure case is unknown case will not be processed.

        Args:
            case: case info from parsed allure report.
            suite_id: id of a testy TestSuite
            project: testy Project instance
            labels: list of labels to add for found test_case

        Returns:
            True and id if element exists. False and None if case not exists.
        """
        if not suite_id:
            return None
        if case.test_status == 'skipped':
            name_list = case.test_name.split(':')
            case.test_name = ''.join(name_list[1:]) if len(name_list) > 1 else case.test_name
        testy_case = TestCase.objects.filter(
            name=case.test_name,
            setup=case.real_test_name,
            suite_id=suite_id,
            project=project,
            description=case.params_str
        ).first()
        if testy_case:
            data = {
                'attributes': case.attributes,
                'user': UserModel.objects.get(pk=user_id),
            }
            if labels:
                data['labels'] = labels
            TestCaseService().case_update(testy_case, data=data)
            return testy_case.id
        return None

    @classmethod
    def find_or_create_test(cls, case_id: int, plan: TestPlan, project: Project) -> Test:
        """
        Find or create test instance in testy.

        Looks for suite with given parameters if several were found returns the first one.
        If none were found creates it and returns.

        Args:
            case_id: id of a foreign key case
            plan: TestPlan instance
            project: testy Project instance

        Returns:
            Test instance
        """
        test = Test.objects.filter(case_id=case_id, project=project, plan=plan).first()
        return test if test else Test.objects.create(case_id=case_id, project=project, plan=plan)

    @classmethod
    def format_attributes(cls, case: dict[str, Any], verbose_names: list[str], keys: list[str]) -> dict[str, str]:
        """
        Parse some values from allure report as attributes json field in testy.

        Args:
            case: Parsed case info from allure
            verbose_names: list of str with verbose names for attributes
            keys: list of keys to search for in parsed allure case

        Returns:
              dictionary with verbose names as keys and its values from allure report
        """
        attributes = {}
        for verbose_name, key in zip(verbose_names, keys):
            if value := case.get(key):
                attributes[verbose_name] = value
        attributes.update(case.get('env_vars', {}))
        return attributes

    def create_result_model(
        self,
        case: dict[str, Any],
        test: Test,
        project: Project,
        user: User,
        additional_parameters: dict[str, str]
    ) -> TestResult:
        """
        Create testy TestResult instance and not save it.

        Args:
            case: case info from parsed allure report.
            test: testy Test instance
            project: testy Project instance
            user: testy UserModel instance,
            additional_parameters: dict of parameters to add to attributes. Key = attribute name, value = attribute val

        Returns:
            TestResult instance that was not saved.
        """
        fields = deepcopy(TestResultService.non_side_effect_fields)
        fields.append('project')
        attributes = self.format_attributes(
            case,
            ['References', 'Source allure report', 'Environment variables'],
            ['refs', 'src_report']
        )
        if additional_parameters:
            attributes.update(additional_parameters)

        data = {
            'test': test,
            'project': project,
            'user': user,
            'status': self.mapped_statuses.get(case['test_status']),
            'attributes': attributes
        }
        if comment := case.get('comment'):
            data['comment'] = comment
        return TestResult.model_create(
            fields=fields,
            data=data,
            commit=False
        )

    @abstractmethod
    def find_existing_elements(
        self,
        suites_to_cases: dict[str, dict[str, Any]],
        project: Project,
        auto_suite_name: str,
        labels: list[str],
        user_id: int,
        **kwargs,
    ) -> dict[str, Any]:
        """
        Find suites and cases by name in TestY and mark objects if they exist or not.

        Args:
            suites_to_cases: mapping of suite name to dict containing list of test cases, and suite info
            project: testy project to check for elements
            auto_suite_name: suite that will be created inside parent suite
            labels: list of label names
            user_id: id of testy user

        Returns:
            Source list of dictionaries with suite ids and case ids added if they exist.
        """
        return NotImplemented

    @classmethod
    def create_plans_hierarchy(cls, parent_plan: TestPlan, plan_names: list[str]) -> TestPlan:
        """
        Create nested test plans by list of names.

        Args:
            parent_plan: Parent plan to add results to
            plan_names: list of plan names to be created

        Returns:
            TestPlan instance
        """
        plan = parent_plan
        default_plan = {
            'started_at': timezone.now(),
            'due_date': timezone.now() + timedelta(days=365)
        }
        for plan_name in plan_names:
            plan, created = TestPlan.objects.get_or_create(
                project=plan.project,
                parent=plan,
                name=plan_name,
                is_archive=False,
                defaults=default_plan
            )
        return plan
