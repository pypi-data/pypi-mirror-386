
import logging
import math
from dataclasses import asdict
from typing import Any, Generator

from django.contrib.contenttypes.models import ContentType
from django.db.models import F, OuterRef, Q
from simple_history.utils import (
    bulk_create_with_history,
    bulk_update_with_history,
    get_history_model_for_model,
)
from testy.core.models import Label, LabeledItem, Project
from testy.tests_description.models import TestCase, TestSuite, TestCaseStep
from testy.tests_description.selectors.cases import TestCaseSelector
from testy.tests_description.services.cases import TestCaseService
from testy.tests_representation.models import Test, TestPlan, TestResult, TestStepResult
from testy.tests_representation.services.results import TestResultService
from testy.users.models import User

from allure_megauploader.models import TaskStatus, UploaderConfigV2, UserTask
from allure_megauploader.uploader_lib.parser import ParsedCase
from allure_megauploader.uploader_lib.uploader import UploaderBase

logger = logging.getLogger('uploader-service')


class UploaderV2(UploaderBase):

    def find_existing_elements(
        self,
        suites_to_cases: dict[str, dict[str, Any]],
        project: Project,
        auto_suite_name: str,
        labels: list[str],
        user_id: int,
        **kwargs,
    ) -> dict[str, dict[str, Any]]:
        self.progress_recorder.progress_step('Discovering already existing cases and suites')
        for suite_name, suite_info in suites_to_cases.items():
            found_suite = self.find_suite(suite_name, project, auto_suite_name)
            if not found_suite:
                suite_info['suite_id'] = None
                continue
            suite_info['suite_id'] = found_suite.id
            for case_info in suite_info['cases']:
                case_info.case_id = self.find_case(case_info, found_suite.id, project, labels, user_id)
        for suite_info in suites_to_cases.values():
            suite_info['cases'] = [asdict(case) for case in suite_info['cases']]
        return suites_to_cases

    def find_suite(self, suite_name: str, project: Project, auto_suite_name: str) -> TestSuite | None:
        if auto_suite_name:
            found_suites = TestSuite.objects.filter(project=project, parent__name=suite_name, name=auto_suite_name)
        else:
            found_suites = TestSuite.objects.filter(project=project, name=suite_name)
        return found_suites.first()

    def create_result_instances(
        self,
        suite_name: str,
        suite_info: dict[str, Any],
        config: UploaderConfigV2,
        user: User,
        plan: TestPlan,
        allure_source: str | None,
    ) -> list[TestResult]:
        results_to_create: list[TestResult] = []
        labels = [{'name': label_name} for label_name in config.labels]
        suite_id = suite_info.get('suite_id')
        if suite_id is None and config.skip_creating_case:
            return []
        elif suite_id is None:
            suite_id = self.create_suite(suite_name, config.project, config.auto_suite_name).id

        for case in suite_info['cases']:
            if case['test_status'] == 'unknown':
                continue
            case_id = case.get('case_id')
            if not case_id and config.skip_creating_case:
                continue
            elif not case_id:
                case_id = self.create_case(case, suite_id, config.project, labels=labels, user=user).id
            test = self.find_or_create_test(case_id, plan, config.project)

            additional_params = config.additional_parameters
            if config.add_allure_source:
                additional_params['ALLURE_SOURCE'] = allure_source if allure_source else 'File provided as allure source'

            result_instance = self.create_result_model(
                case,
                test,
                config.project,
                user,
                additional_params,
            )
            result_instance.test_case_version = TestCaseSelector().case_version(test.case)
            results_to_create.append(
                result_instance
            )
        return results_to_create


class UploaderDataServices(UploaderBase):

    def create_result_instances(
        self,
        suite_name: str,
        suite_info: dict[str, Any],
        config: UploaderConfigV2,
        user: User,
        plan: TestPlan,
        allure_source: str | None,
    ) -> list[TestResult]:
        results_to_create: list[TestResult] = []
        labels = [{'name': label_name} for label_name in config.labels]
        suite_id = suite_info.get('suite_id')
        if suite_id is None and config.skip_creating_case:
            return []
        elif suite_id is None:
            suite_id = self.create_suite(suite_name.split('::'), config.project, config.auto_suite_name).id

        for case in suite_info['cases']:
            if case['test_status'] == 'unknown':
                continue
            case_id = case.get('case_id')
            if not case_id and config.skip_creating_case:
                continue
            elif not case_id:
                case_id = self.create_case(case, suite_id, config.project, labels=labels, user=user).id
            test = self.find_or_create_test(case_id, plan, config.project)

            additional_params = config.additional_parameters
            if config.add_allure_source:
                additional_params['ALLURE_SOURCE'] = allure_source if allure_source else 'File provided as allure source'

            result_instance = self.create_result_model(
                case,
                test,
                config.project,
                user,
                additional_params,
            )
            result_instance.test_case_version = TestCaseSelector().case_version(test.case)
            results_to_create.append(
                result_instance
            )
        return results_to_create

    def find_existing_elements(
        self,
        suites_to_cases: dict[str, dict[str, Any]],
        project: Project,
        auto_suite_name: str,
        labels: list[str],
        user_id: int,
        **kwargs,
    ) -> dict[str, dict[str, Any]]:
        self.progress_recorder.progress_step('Discovering already existing cases and suites')
        for concatenated_suite_name, suite_info in suites_to_cases.items():
            found_suite = self.find_suite(concatenated_suite_name.split('::'), project, auto_suite_name)
            if not found_suite:
                suite_info['suite_id'] = None
                continue
            suite_info['suite_id'] = found_suite.id
            for case_info in suite_info['cases']:
                case_info.case_id = self.find_case(case_info, found_suite.id, project, labels, user_id)
        for suite_info in suites_to_cases.values():
            suite_info['cases'] = [asdict(case) for case in suite_info['cases']]
        return suites_to_cases

    def find_suite(self, suite_name: Any, project: Project, auto_suite_name: str) -> TestSuite | None:
        return self.find_suite_by_hierarchy(suite_name, project, auto_suite_name)

    @classmethod
    def find_suite_by_hierarchy(
        cls,
        suite_hierarchy: list[str],
        project: Project,
        auto_suite_name: str,
    ) -> TestSuite | None:
        parent = None
        for suite_name in suite_hierarchy:
            parent = TestSuite.objects.filter(
                name=suite_name,
                project=project,
                parent=parent,
                is_deleted=False
            ).first()
        if auto_suite_name:
            parent = TestSuite.objects.filter(
                name=auto_suite_name,
                project=project,
                parent=parent,
                is_deleted=False
            ).first()
        return parent

    @classmethod
    def get_or_create_hierarchy_suites(
        cls,
        suite_hierarchy: list[str],
        project: Project,
        auto_suite_name: str,
    ):
        parent = None
        for suite_name in suite_hierarchy:
            parent = cls.get_or_create_suite(name=suite_name, project=project, parent=parent, is_deleted=False)
        if auto_suite_name:
            parent = cls.get_or_create_suite(name=auto_suite_name, project=project, parent=parent, is_deleted=False)
        return parent

    @classmethod
    def create_suite(cls, suite_name: list[str], project: Project, auto_suite_name: str) -> TestSuite:
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
        parent = None
        for name in suite_name:
            parent = cls.get_or_create_suite(name=name, project=project, parent=parent, is_deleted=False)
        if auto_suite_name:
            parent = cls.get_or_create_suite(name=auto_suite_name, project=project, parent=parent, is_deleted=False)
        return parent

    @classmethod
    def get_or_create_suite(cls, **kwargs):
        suite = TestSuite.objects.filter(**kwargs).first()
        if not suite:
            return TestSuite.objects.create(**kwargs)
        return suite


class UploaderUnique(UploaderV2):

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
            user_id: integer user id

        Returns:
            True and id if element exists. False and None if case not exists.
        """
        if not suite_id:
            return None
        if case.test_status == 'skipped':
            name_list = case.test_name.split(':')
            case.test_name = ''.join(name_list[1:]) if len(name_list) > 1 else case.test_name
        testy_case = TestCase.objects.filter(
            suite_id=suite_id,
            project=project,
            setup=case.allure_history_id
        ).first()
        if not testy_case:
            return None
        if payload := cls.update_payload(user_id, testy_case, case, labels):
            TestCaseService().case_update(testy_case, data=payload)
        return testy_case.id

    @classmethod
    def update_payload(
        cls,
        user_id: int,
        testy_case: TestCase,
        parsed_case: ParsedCase,
        labels: list[str],
    ) -> dict[str, Any] | None:
        payload = {
            'attributes': testy_case.attributes,
            'user': User.objects.get(pk=user_id),
            'description': parsed_case.params_str,
            'scenario': parsed_case.custom_steps,
        }
        if labels:
            payload['labels'] = labels
        if all(
            [
                testy_case.description == parsed_case.params_str,
                parsed_case.attributes == testy_case.attributes,
                testy_case.scenario == parsed_case.custom_steps,
            ]
        ):
            return None
        return payload

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
            'setup': case['allure_history_id'],
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


class TestyUploader(UploaderV2):
    def create_result_instances(
        self,
        suite_name: str,
        suite_info: dict[str, Any],
        config: UploaderConfigV2,
        user: User,
        plan: TestPlan,
        allure_source: str | None,
    ) -> list[TestResult]:
        results_to_create: list[TestResult] = []
        labels = [{'name': label_name} for label_name in config.labels]
        suite_id = suite_info.get('suite_id')
        if suite_id is None and config.skip_creating_case:
            return []
        elif suite_id is None:
            suite_id = self.create_suite(suite_name.split('::'), config.project, config.auto_suite_name).id

        for case in suite_info['cases']:
            if case['test_status'] == 'unknown':
                continue
            case_id = case.get('case_id')
            if not case_id and config.skip_creating_case:
                continue
            elif not case_id:
                case_id = self.create_case(case, suite_id, config.project, labels=labels, user=user).id
            test = self.find_or_create_test(case_id, plan, config.project)

            additional_params = config.additional_parameters
            if config.add_allure_source:
                additional_params['ALLURE_SOURCE'] = allure_source if allure_source else 'File provided as allure source'

            result_instance = self.create_result_model(
                case,
                test,
                config.project,
                user,
                additional_params,
            )

            result_instance.test_case_version = TestCaseSelector().case_version(test.case)
            results_to_create.append(
                result_instance
            )
        return results_to_create

    def find_existing_elements(
        self,
        suites_to_cases: dict[str, dict[str, Any]],
        project: Project,
        auto_suite_name: str,
        labels: list[str],
        user_id: int,
        **kwargs,
    ) -> dict[str, dict[str, Any]]:
        self.progress_recorder.progress_step('Discovering already existing cases and suites')
        for concatenated_suite_name, suite_info in suites_to_cases.items():
            found_suite = self.find_suite(concatenated_suite_name.split('::'), project, auto_suite_name)
            if not found_suite:
                suite_info['suite_id'] = None
                continue
            suite_info['suite_id'] = found_suite.id
            for case_info in suite_info['cases']:
                case_info.case_id = self.find_case(case_info, found_suite.id, project, labels, user_id)
        for suite_info in suites_to_cases.values():
            suite_info['cases'] = [asdict(case) for case in suite_info['cases']]
        return suites_to_cases

    def find_suite(self, suite_name: Any, project: Project, auto_suite_name: str) -> TestSuite | None:
        return self.find_suite_by_hierarchy(suite_name, project, auto_suite_name)

    @classmethod
    def find_suite_by_hierarchy(
        cls,
        suite_hierarchy: list[str],
        project: Project,
        auto_suite_name: str,
    ) -> TestSuite | None:
        parent = None
        for suite_name in suite_hierarchy:
            parent = TestSuite.objects.filter(
                name=suite_name,
                project=project,
                parent=parent,
                is_deleted=False
            ).first()
        if auto_suite_name:
            parent = TestSuite.objects.filter(
                name=auto_suite_name,
                project=project,
                parent=parent,
                is_deleted=False
            ).first()
        return parent

    @classmethod
    def get_or_create_hierarchy_suites(
        cls,
        suite_hierarchy: list[str],
        project: Project,
        auto_suite_name: str,
    ):
        parent = None
        for suite_name in suite_hierarchy:
            parent = cls.get_or_create_suite(name=suite_name, project=project, parent=parent, is_deleted=False)
        if auto_suite_name:
            parent = cls.get_or_create_suite(name=auto_suite_name, project=project, parent=parent, is_deleted=False)
        return parent

    @classmethod
    def create_suite(cls, suite_name: list[str], project: Project, auto_suite_name: str) -> TestSuite:
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
        parent = None
        for name in suite_name:
            parent = cls.get_or_create_suite(name=name, project=project, parent=parent, is_deleted=False)
        if auto_suite_name:
            parent = cls.get_or_create_suite(name=auto_suite_name, project=project, parent=parent, is_deleted=False)
        return parent

    @classmethod
    def get_or_create_suite(cls, **kwargs):
        suite = TestSuite.objects.filter(**kwargs).first()
        if not suite:
            return TestSuite.objects.create(**kwargs)
        return suite

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
            user_id: integer user id

        Returns:
            True and id if element exists. False and None if case not exists.
        """
        if not suite_id:
            return None
        if case.test_status == 'skipped':
            name_list = case.test_name.split(':')
            case.test_name = ''.join(name_list[1:]) if len(name_list) > 1 else case.test_name
        testy_case = TestCase.objects.filter(
            suite_id=suite_id,
            project=project,
            setup=case.allure_history_id
        ).first()
        if not testy_case:
            return None
        if payload := cls.update_payload(user_id, testy_case, case, labels):
            TestCaseService().case_update(testy_case, data=payload)
        return testy_case.id

    @classmethod
    def update_payload(
        cls,
        user_id: int,
        testy_case: TestCase,
        parsed_case: ParsedCase,
        labels: list[str],
    ) -> dict[str, Any] | None:
        payload = {
            'attributes': testy_case.attributes,
            'user': User.objects.get(pk=user_id),
            'description': parsed_case.params_str,
            'scenario': parsed_case.custom_steps,
        }
        if labels:
            payload['labels'] = labels
        if all(
            [
                testy_case.description == parsed_case.params_str,
                parsed_case.attributes == testy_case.attributes,
                testy_case.scenario == parsed_case.custom_steps,
            ]
        ):
            return None
        return payload

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
            'setup': case['allure_history_id'],
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


class TestyUploaderOptimised(UploaderV2):
    def find_existing_elements(
        self,
        suites_to_cases: Generator,
        project: Project,
        auto_suite_name: str,
        labels: list[str],
        user_id: int,
        **kwargs
    ) -> dict[str, dict[str, Any]]:
        """Overrides to follow source uploader protocol"""
        config: UploaderConfigV2 = kwargs.get('config')
        cases_count = next(suites_to_cases)
        batch_size = kwargs.get('batch_size', 1000)
        plan: TestPlan | None = kwargs.get('plan')
        allure_source = kwargs.get('allure_source')
        if plan is None:
            plan = config.plan
            parameters = config.parameters.all() if config.parameters else None
            if config.child_plan:
                plan = self.find_or_create_plan(
                    parent=plan,
                    plan_name=config.child_plan,
                    project=config.project,
                    parameters=parameters,
                )

        user = User.objects.get(pk=user_id)
        label_objs = []
        for label_dict in labels:
            name = label_dict.get('name')
            if name is None:
                continue
            label, _ = Label.objects.get_or_create(project=project, name=name)
            label_objs.append(label)

        suites_map = {}
        logger.info(f'Debug log cases count is: {cases_count}')
        batches_count = math.ceil(cases_count / batch_size)
        for batch in range(1, batches_count + 1):
            additional_params = config.additional_parameters
            if config.add_allure_source:
                additional_params['ALLURE_SOURCE'] = allure_source if allure_source else 'File provided as allure source'
            logger.info(f'Starting batch {batch} of {batches_count}')
            self.create_descriptions(
                suites_to_cases,
                config.project,
                config.auto_suite_name,
                user_id,
                labels=label_objs,
                suites_map=suites_map,
                batch_size=batch_size,
                user=user,
                plan=plan,
                additional_parameters=additional_params,
                skip_creating_case=config.skip_creating_case,
            )
        task_id = kwargs.get('task_id')
        UserTask.objects.filter(task_id=task_id).update(status=TaskStatus.SUCCESS, plan=plan)
        return {}

    def create_tests(self, case_ids: list[int], plan: TestPlan) -> dict[str, Test]:
        found_tests = Test.objects.filter(
            case__in=case_ids,
            plan=plan,
        )
        cases = TestCase.objects.filter(~Q(tests__in=found_tests) & Q(pk__in=case_ids))
        tests_for_creation = []
        for case in cases:
            tests_for_creation.append(Test(case=case, project=case.project, plan=plan))

        bulk_create_with_history(tests_for_creation, Test, batch_size=500)

        created_tests = Test.objects.filter(pk__in=[test.pk for test in tests_for_creation])

        all_tests = (found_tests | created_tests).annotate(
            allure_history_id=F('case__attributes__allure_history_id'),
        )

        return {test.allure_history_id: test for test in all_tests}

    def create_descriptions(
        self,
        suites_to_cases: Generator,
        project: Project,
        auto_suite_name: str,
        user_id: int,
        labels: list[Label],
        suites_map: dict[str, int],
        batch_size: int,
        user: User,
        plan: TestPlan,
        additional_parameters: dict[str, Any],
        skip_creating_case: bool = False,
    ) -> None:
        case_ids = []
        cases_for_update = []
        case_ids_for_not_update = []
        all_history_data = {}
        data_for_creation = {}
        label_ids = {label.id for label in labels}
        for idx, case_data in enumerate(suites_to_cases):
            concatenated_suite = case_data.get('suite')
            suite_id = suites_map.get(concatenated_suite)
            if not suite_id:
                suite_id = self.get_or_create_hierarchy_suites(
                    concatenated_suite.split('::'),
                    project,
                    auto_suite_name,
                ).pk
                suites_map[concatenated_suite] = suite_id
            case_data['suite_id'] = suite_id
            allure_history_id = case_data['allure_history_id']
            all_history_data[allure_history_id] = self.prepare_case_data(case_data, project, user_id)
            if not skip_creating_case:
                data_for_creation[allure_history_id] = all_history_data[allure_history_id]
            if idx == batch_size - 1:
                break
        updated_fields = [*TestCaseService.non_side_effect_fields, 'attributes']
        for case in TestCase.objects.filter(
            attributes__allure_history_id__in=all_history_data.keys(),
            project=project
        ):
            case_label_ids = set(case.label.first().ids)
            allure_history_id = case.attributes.get('allure_history_id')
            allure_attributes = all_history_data[allure_history_id].get('attributes', {}) or {}
            all_history_data[allure_history_id]['attributes'] = {
                **case.attributes,
                **allure_attributes
            }
            case, updated = case.model_update(
                updated_fields,
                data=all_history_data[allure_history_id],
                commit=False,
            )
            if updated or label_ids != case_label_ids:
                cases_for_update.append(case)
            else:
                case_ids_for_not_update.append(case.pk)
            case_ids.append(case.pk)
            data_for_creation.pop(allure_history_id, None)


        cases_for_creation = [self.create_case_model(data, project.pk) for data in data_for_creation.values()]

        bulk_create_with_history(cases_for_creation, TestCase, default_user=user, batch_size=500)
        bulk_update_with_history(
            cases_for_update,
            TestCase,
            updated_fields,
            default_user=user,
            batch_size=500,
        )
        for case in cases_for_creation:
            case_ids.append(case.pk)
        ct = ContentType.objects.get_for_model(TestCase)
        LabeledItem.objects.filter(
            content_type=ct,
            object_id__in=case_ids,
        ).exclude(
            content_type=ct,
            object_id__in=case_ids_for_not_update,
        ).hard_delete()
        labeled_items_to_create = []
        history_model = get_history_model_for_model(TestCase)
        subq = history_model.objects.filter(id=OuterRef('pk')).order_by('-history_id').values('history_id')[:1]
        cases = TestCase.objects.filter(pk__in=case_ids).annotate(version=subq)
        versions_mapping = {}
        for label in labels:
            for case in cases:
                if case.pk not in versions_mapping:
                    versions_mapping[case.pk] = case.version
                if case.pk in case_ids_for_not_update:
                    continue
                li = LabeledItem(
                    label=label,
                    content_type=ct,
                    object_id=case.pk,
                    content_object_history_id=case.version,
                )
                labeled_items_to_create.append(li)
        bulk_create_with_history(labeled_items_to_create, LabeledItem, batch_size=500)
        tests_mapping = self.create_tests(case_ids, plan)

        results_to_create = []
        for case_data in all_history_data.values():
            if case_data['test_status'] == 'unknown':
                continue
            test = tests_mapping[case_data['allure_history_id']]
            result_instance = self.create_result_model(
                case_data,
                test,
                project,
                user,
                additional_parameters,
            )
            result_instance.test_case_version = versions_mapping.get(test.case_id, 0)
            results_to_create.append(result_instance)
        logger.info('Started bulk creation of test results')
        TestResultService.result_bulk_create(results_to_create, user)

    @classmethod
    def get_or_create_hierarchy_suites(
        cls,
        suite_hierarchy: list[str],
        project: Project,
        auto_suite_name: str,
    ):
        parent = None
        for suite_name in suite_hierarchy:
            parent = cls.get_or_create_suite(name=suite_name, project=project, parent=parent, is_deleted=False)
        if auto_suite_name:
            parent = cls.get_or_create_suite(name=auto_suite_name, project=project, parent=parent, is_deleted=False)
        return parent

    @classmethod
    def get_or_create_suite(cls, **kwargs):
        suite = TestSuite.objects.filter(**kwargs).first()
        if not suite:
            return TestSuite.objects.create(**kwargs)
        return suite

    @classmethod
    def prepare_case_data(
        cls,
        case: dict[str, Any],
        project: Project,
        user_id: int,
    ) -> dict[str, Any]:
        """
        Find case if exists.

        Find case if it exists.
        If status of allure case is unknown case will not be processed.

        Args:
            case: case info from parsed allure report.
            suite_id: id of a testy TestSuite
            project: testy Project instance
            labels: list of labels to add for found test_case
            user_id: integer user id

        Returns:
            True and id if element exists. False and None if case not exists.
        """
        if case['test_status'] == 'skipped':
            name_list = case['test_name'].split(':')
            case['test_name'] = ''.join(name_list[1:]) if len(name_list) > 1 else case['test_name']
        case.update(
            {
                'user_id': user_id,
                'description': case['params_str'],
                'project_id': project.pk,
            }
        )
        return case

    @classmethod
    def create_case_model(
        cls,
        case: dict[str, Any],
        project_id: int,
    ) -> TestCase:
        """
        Create testy TestCase from parsed info from allure report.

        Args:
            case: case info from parsed allure report.
            project_id: testy Project id
            labels: list of labels to add for creation
            user_id: user_id of executing action

        Returns:
            TestCase instance
        """
        scenario = case['custom_steps'] if case.get('custom_steps') else 'Scenario was not provided'
        if case['test_status'] == 'skipped':
            name_list = case['test_name'].split(':')
            case['test_name'] = ''.join(name_list[1:]) if len(name_list) > 1 else case['test_name']
        case['attributes']['allure_history_id'] = case['allure_history_id']
        case_data = {
            'name': case['test_name'],
            'scenario': scenario,
            'project_id': project_id,
            'description': case['params_str'],
            'attributes': case['attributes'],
            'suite_id': case['suite_id'],
            'setup': case['setup'] if case.get('setup') else ''
        }

        return TestCase.model_create(
            data=case_data,
            fields=TestCaseService.case_non_side_effect_fields + ['project_id', 'suite_id'],
            commit=False
        )


class UploaderFSTEK(UploaderV2):
    def find_existing_elements(
        self,
        suites_to_cases: dict[str, dict[str, Any]],
        project: Project,
        auto_suite_name: str,
        labels: list[str],
        user_id: int,
        **kwargs,
    ) -> dict[str, dict[str, Any]]:
        self.progress_recorder.progress_step('Discovering already existing cases and suites')
        for suite_name, suite_info in suites_to_cases.items():
            found_suite = self.find_suite(suite_name, project, auto_suite_name)
            if not found_suite:
                suite_info['suite_id'] = None
                continue
            suite_info['suite_id'] = found_suite.id
            for case_info in suite_info['cases']:
                case_info.case_id = self.find_case(case_info, found_suite.id, project, labels, user_id)
        for suite_info in suites_to_cases.values():
            suite_info['cases'] = [asdict(case) for case in suite_info['cases']]
        return suites_to_cases

    @classmethod
    def find_case(
        cls,
        case: ParsedCase,
        suite_id: int,
        project: Project,
        labels: list[str],
        user_id: int,
    ) -> int | None:
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
            steps = case.steps or []
            for step in steps:
                step_instance = TestCaseStep.objects.filter(test_case=testy_case, name=step['name']).first()
                if step_instance:
                    step['id'] = step_instance.id
            data = {
                'attributes': case.attributes,
                'is_steps': True,
                'user': User.objects.get(pk=user_id),
                'steps': steps,
            }
            if labels:
                data['labels'] = labels
            TestCaseService().case_with_steps_update(testy_case, data=data)
            return testy_case.id
        return None

    def create_result_instances(
        self,
        suite_name: str,
        suite_info: dict[str, Any],
        config: UploaderConfigV2,
        user: User,
        plan: TestPlan,
        allure_source: str | None,
    ) -> list[TestResult]:
        labels = [{'name': label_name} for label_name in config.labels]
        suite_id = suite_info.get('suite_id')
        results_for_create = []
        step_results_for_create = []

        if suite_id is None and config.skip_creating_case:
            return []
        elif suite_id is None:
            suite_id = self.create_suite(suite_name, config.project, config.auto_suite_name).id

        for case in suite_info['cases']:
            if case['test_status'] == 'unknown':
                continue
            case_id = case.get('case_id')
            if not case_id and config.skip_creating_case:
                continue
            elif not case_id:
                case_id = self.create_case(case, suite_id, config.project, labels=labels, user=user).id
            test = self.find_or_create_test(case_id, plan, config.project)

            additional_params = config.additional_parameters
            if config.add_allure_source:
                additional_params['ALLURE_SOURCE'] = allure_source if allure_source else 'File provided as allure source'

            result_instance = self.create_result_model(
                case,
                test,
                config.project,
                user,
                additional_params,
            )
            result_instance.attachment_ids = case['attachments']
            steps_results = self.create_step_result_model(
                case,
                result_instance,
                config.project,
                user,
            )
            result_instance.test_case_version = TestCaseSelector().case_version(test.case)
            results_for_create.append(result_instance)
            step_results_for_create.extend(steps_results)
        return results_for_create, step_results_for_create

    def create_step_result_model(
        self,
        case: dict[str, Any],
        test_result: TestResult,
        project: Project,
        user: User,
    ):
        step_results = []
        for step in case['steps']:
            data = {
                'test_result': test_result,
                'project': project,
                'status': self.mapped_statuses.get(step['status']),
                'step_id': step['id'],
            }
            step_results.append(TestStepResult(**data))
        return step_results

    @classmethod
    def create_case(
        cls,
        case: dict[str, str],
        suite_id: int,
        project: Project,
        labels: list[dict[str, str]] | None = None,
        user: User = None,
    ) -> TestCase:
        if case['test_status'] == 'skipped':
            name_list = case['test_name'].split(':')
            case['test_name'] = ''.join(name_list[1:]) if len(name_list) > 1 else case['test_name']
        case_data = {
            'name': case['test_name'],
            'setup': case['custom_steps'],
            'suite': TestSuite.objects.get(pk=suite_id),
            'project': project,
            'description': case['params_str'],
            'user': user,
            'attributes': case['attributes'],
            'is_steps': True,
        }

        if labels:
            case_data['labels'] = labels

        test_case = TestCaseService().case_create(data=case_data)
        for step in case['steps']:
            step_instance = TestCaseService().step_create(
                data={
                    'project': project,
                    'test_case': test_case,
                    **step,
                }
            )
            step['id'] = step_instance.id
        return test_case
