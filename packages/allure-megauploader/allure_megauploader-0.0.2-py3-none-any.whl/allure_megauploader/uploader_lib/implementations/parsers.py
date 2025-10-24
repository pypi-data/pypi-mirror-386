
import json
import os
import mimetypes
from collections import defaultdict
from io import TextIOWrapper
from typing import Any
from uuid import uuid4

import orjson

from allure_megauploader.uploader_lib.parser import ParsedCase, ParserBase
from allure_megauploader.uploader_lib.utils import matched_dict
from testy.core.models import Attachment
from django.core.files import File

MAX_NAME_LENGTH = 254


class ParserV2(ParserBase):
    def parse_cases(self) -> dict[str, dict[str, Any]]:
        self.progress_recorder.progress_step('Parsing test cases')
        case_uids = []
        env_vars = self._get_env_vars()
        with open(f'{self.report_dir}/data/suites.json') as json_file:
            suites_info = json.load(json_file)
            suites = suites_info.get('children')
            for suite in suites:
                case_uids.extend(self.get_cases_from_allure(suite))
        suites_to_cases: dict[str, dict[str, Any]] = defaultdict(lambda: defaultdict(list))
        for case_uid in case_uids:
            with open(f'{self.report_dir}/data/test-cases/{case_uid}.json') as json_file:
                parsed_case = self._parse_test_case_info(
                    test_info=json.load(json_file),
                    session_id=str(uuid4().hex),
                    env_vars=env_vars,
                )
                suites_to_cases[parsed_case.suite]['cases'].append(parsed_case)
        return suites_to_cases

    def parse_suite(self, test_info: dict[str, Any]) -> str:
        conditional_values = ['feature', 'parentSuite', 'subSuite', 'suite']
        labels = test_info.get('labels', [])
        for conditional_value in conditional_values:
            if group_by_value := matched_dict(labels, 'name', conditional_value):
                return str(group_by_value.get('value', ''))
        return 'could_not_be_parsed'


class ParserDataServices(ParserBase):
    def parse_cases(self) -> dict[str, dict[str, Any]]:
        case_uids = []
        env_vars = self._get_env_vars()
        with open(f'{self.report_dir}/data/suites.json') as json_file:
            suites_info = json.load(json_file)
            suites = suites_info.get('children')
            for suite in suites:
                case_uids.extend(self.get_cases_from_allure(suite))

        suites_to_cases: dict[str, dict[str, Any]] = defaultdict(lambda: defaultdict(list))

        for case_uid in case_uids:
            with open(f'{self.report_dir}/data/test-cases/{case_uid}.json') as json_file:
                parsed_case = self._parse_test_case_info(
                    test_info=json.load(json_file),
                    session_id=str(uuid4().hex),
                    env_vars=env_vars,
                )
                suites_to_cases[parsed_case.suite]['cases'].append(parsed_case)

        return suites_to_cases

    def parse_suite(self, test_info: dict[str, Any]) -> str:
        suite_keys = ['parentSuite', 'suite', 'subSuite']
        labels = test_info.get('labels', [])
        result = []
        for suite_key in suite_keys:
            if group_by_value := matched_dict(labels, 'name', suite_key):
                if value := group_by_value.get('value', None):
                    result.append(value)
        return '::'.join(result)


class ParserUnique(ParserV2):

    def _parse_test_case_info(
        self,
        test_info: dict,
        session_id: str,
        env_vars: dict[str, str],
    ) -> ParsedCase:
        """
        Parse info received from json file from allure.

        Args:
            test_info: dict parsed from json file.
            session_id: identification of allure report parsed from created timestamp
            env_vars: environment variables as string

        Returns:
            Parsed test case info.
        """
        test_status = test_info.get('status')
        allure_statuses = ['passed', 'failed', 'skipped', 'broken']
        if test_status not in allure_statuses:
            test_status = 'unknown'
        test_params = test_info.get('parameters', {})
        name = test_info.get('name', '')
        params_str = self._parse_params(test_params)
        suite = self.parse_suite(test_info)
        refs = self._parse_reference_from_link(test_info.get('links', []))
        case = ParsedCase(
            suite=suite,
            test_name=name[:MAX_NAME_LENGTH] if len(name) > 255 else name,
            params=test_info.get('parameters', {}),
            params_str=params_str,
            test_status=test_status,
            session_id=session_id,
            real_test_name=self._parse_real_test_name(test_info.get('fullName', '')),
            custom_steps=self._parse_steps(test_info.get('testStage', {})),
            env_vars=env_vars,
            refs=refs,
            comment=test_info.get('statusMessage', ''),
            suite_id=None,
            case_id=None,
            attributes=self._parse_custom_attributes(test_info.get('labels', [])),
            allure_history_id=test_info.get('historyId'),
        )

        return case

    def _parse_steps(self, test_stage: dict[str, Any]) -> str:
        if not test_stage:
            return ''
        if 'description' in test_stage:
            return str(test_stage['description'].strip())
        steps = list(self._flatten_recursive(test_stage.get('steps', [])))
        return '\n'.join(steps)

    def _flatten_recursive(self, steps: list[dict[str, Any]], *, depth: int = 0):
        for idx, step in enumerate(steps, start=1):
            yield '{0}{1}. {2}'.format('\t' * depth, idx, step.get("name"))
            yield from self._flatten_recursive(step.get('steps', []), depth=depth + 1)


class TestyParser(ParserBase):
    def parse_cases(self) -> dict[str, dict[str, Any]]:
        case_uids = []
        env_vars = self._get_env_vars()
        with open(f'{self.report_dir}/data/suites.json') as json_file:
            suites_info = json.load(json_file)
            suites = suites_info.get('children')
            for suite in suites:
                case_uids.extend(self.get_cases_from_allure(suite))

        suites_to_cases: dict[str, dict[str, Any]] = defaultdict(lambda: defaultdict(list))

        for case_uid in case_uids:
            with open(f'{self.report_dir}/data/test-cases/{case_uid}.json') as json_file:
                parsed_case = self._parse_test_case_info(
                    test_info=json.load(json_file),
                    session_id=str(uuid4().hex),
                    env_vars=env_vars,
                )
                suites_to_cases[parsed_case.suite]['cases'].append(parsed_case)

        return suites_to_cases

    def parse_suite(self, test_info: dict[str, Any]) -> str:
        suite_keys = ['parentSuite', 'suite', 'subSuite']
        labels = test_info.get('labels', [])
        result = []
        for suite_key in suite_keys:
            if group_by_value := matched_dict(labels, 'name', suite_key):
                if value := group_by_value.get('value', None):
                    result.append(value)
        return '::'.join(result)

    def _parse_test_case_info(
        self,
        test_info: dict,
        session_id: str,
        env_vars: dict[str, str],
    ) -> ParsedCase:
        """
        Parse info received from json file from allure.

        Args:
            test_info: dict parsed from json file.
            session_id: identification of allure report parsed from created timestamp
            env_vars: environment variables as string

        Returns:
            Parsed test case info.
        """
        test_status = test_info.get('status', 'unknown')
        allure_statuses = ['passed', 'failed', 'skipped', 'broken']
        if test_status not in allure_statuses:
            test_status = 'unknown'
        test_params = test_info.get('parameters', {})
        name = test_info.get('name', '')
        params_str = self._parse_params(test_params)
        suite = self.parse_suite(test_info)
        refs = self._parse_reference_from_link(test_info.get('links', []))
        case = ParsedCase(
            suite=suite,
            test_name=name[:MAX_NAME_LENGTH] if len(name) > 255 else name,
            params=test_info.get('parameters', {}),
            params_str=params_str,
            test_status=test_status,
            session_id=session_id,
            real_test_name=self._parse_real_test_name(test_info.get('fullName', '')),
            custom_steps=self._parse_steps(test_info.get('testStage', {})),
            env_vars=env_vars,
            refs=refs,
            comment=test_info.get('statusMessage', ''),
            suite_id=None,
            case_id=None,
            attributes=self._parse_custom_attributes(test_info.get('labels', [])),
            allure_history_id=test_info.get('historyId'),
        )

        return case

    def _parse_steps(self, test_stage: dict[str, Any]) -> str:
        if not test_stage:
            return ''
        if 'description' in test_stage:
            return str(test_stage['description'].strip())
        steps = list(self._flatten_recursive(test_stage.get('steps', [])))
        return '\n'.join(steps)

    def _flatten_recursive(self, steps: list[dict[str, Any]], *, depth: int = 0):
        for idx, step in enumerate(steps, start=1):
            yield '{0}{1}. {2}'.format('\t' * depth, idx, step.get("name"))
            yield from self._flatten_recursive(step.get('steps', []), depth=depth + 1)


class TestyParserOptimised(TestyParser):
    def parse_cases(self) -> dict[str, dict[str, Any]]:
        case_uids = []

        env_vars = self._get_env_vars()
        with open(f'{self.report_dir}/data/suites.json', 'rb') as json_file:
            suites_info = orjson.loads(json_file.read())
            suites = suites_info.get('children')
            for suite in suites:
                case_uids.extend(self.get_cases_from_allure(suite))

        yield len(case_uids)

        for case_uid in case_uids:
            with open(f'{self.report_dir}/data/test-cases/{case_uid}.json', 'rb') as json_file:
                yield self._parse_test_case_info(
                    test_info=orjson.loads(json_file.read()),
                    session_id=str(uuid4().hex),
                    env_vars=env_vars,
                )

    def _parse_test_case_info(
        self,
        test_info: dict,
        session_id: str,
        env_vars: dict[str, str],
    ) -> dict:
        """
        Parse info received from json file from allure.

        Args:
            test_info: dict parsed from json file.
            session_id: identification of allure report parsed from created timestamp
            env_vars: environment variables as string

        Returns:
            Parsed test case info.
        """
        test_status = test_info.get('status', 'unknown')
        allure_statuses = ['passed', 'failed', 'skipped', 'broken']
        if test_status not in allure_statuses:
            test_status = 'unknown'
        test_params = test_info.get('parameters', {})
        name = test_info.get('name', '')
        params_str = self._parse_params(test_params)
        suite = self.parse_suite(test_info)
        refs = self._parse_reference_from_link(test_info.get('links', []))
        return {
            "suite": suite,
            "test_name": name[:MAX_NAME_LENGTH] if len(name) > 255 else name,
            "params": test_info.get('parameters', {}),
            "params_str": params_str,
            "test_status": test_status,
            "session_id": session_id,
            "real_test_name": self._parse_real_test_name(test_info.get('fullName', '')),
            "custom_steps": self._parse_steps(test_info.get('testStage', {})),
            "scenario": self._parse_steps(test_info.get('testStage', {})),
            "env_vars": env_vars,
            "refs": refs,
            "comment": test_info.get('statusMessage', ''),
            "suite_id": None,
            "case_id": None,
            "attributes": self._parse_custom_attributes(test_info.get('labels', [])),
            "allure_history_id": test_info.get('historyId'),
            # TODO: We can use before stages to create meaningful setup "setup": test_info.get('beforeStages')
        }


class ParserFSTEK(ParserV2):

    def parse_cases(self) -> dict[str, dict[str, Any]]:
        self.progress_recorder.progress_step('Parsing test cases')
        case_uids = []
        env_vars = self._get_env_vars()
        with open(f'{self.report_dir}/data/suites.json') as json_file:
            suites_info = json.load(json_file)
            suites = suites_info.get('children')
            for suite in suites:
                case_uids.extend(self.get_cases_from_allure(suite))
        suites_to_cases: dict[str, dict[str, Any]] = defaultdict(lambda: defaultdict(list))
        for case_uid in case_uids:
            with open(f'{self.report_dir}/data/test-cases/{case_uid}.json') as json_file:
                parsed_case = self._parse_test_case_info(
                    test_info=json.load(json_file),
                    session_id=str(uuid4().hex),
                    env_vars=env_vars,
                )
                suites_to_cases[parsed_case.suite]['cases'].append(parsed_case)
        return suites_to_cases

    def _create_attachment(self, attachment_name: str) -> int:
        path = f'{self.report_dir}/data/attachments/{attachment_name}'
        content_type, _ = mimetypes.guess_type(attachment_name, strict=False)
        with open(path, 'rb') as attachment_file:
            filename = attachment_file.name.split('/')[-1]
            name, _ = os.path.splitext(filename)
            django_file = File(attachment_file)
            attachment = Attachment.objects.create(
                project=self.config.project,
                name=name,
                filename=filename,
                file_extension=content_type,
                file=django_file,
                size=django_file.size,
            )
            return attachment.id

    def _parse_attachments(self, test_stage: dict[str, Any]) -> list[int]:
        if not test_stage:
            return []
        attachments = []

        for attachment in test_stage.get('attachments', []):
            name = attachment['source']
            attachments.append(self._create_attachment(name))
        return attachments

    @staticmethod
    def _parse_steps(test_stage: dict[str, Any], expected_steps: list[str] | None = None) -> list[dict]:
        if not test_stage:
            return []
        if expected_steps is None:
            expected_steps = []
        len_expected = len(expected_steps)
        steps = []
        for idx, step in enumerate(test_stage.get('steps', []), start=1):
            name = step.get('name', '')
            steps.append(
                {
                    'name': name[:MAX_NAME_LENGTH],
                    'scenario': step.get('name'),
                    'sort_order': idx,
                    'status': step.get('status'),
                    'expected': expected_steps[idx - 1] if len_expected > idx - 1 else '',
                }
            )
        return steps

    def _parse_custom_steps(self, test_info: list[dict[str, Any]]) -> str:
        pre_conditions = []
        for stage in test_info:
            for pre_step in stage.get('steps', []):
                pre_conditions.append(pre_step.get('name'))
        return ', '.join(pre_conditions)

    def _parse_expected_steps(self, test_params: list[dict[str,Any]]) -> list[str] | None:
        expected_step_results = next(
            filter(lambda param: param['name'] == 'expected', test_params), None,
        )
        if not expected_step_results:
            return None
        return json.loads(expected_step_results['value'].lstrip('\'').rstrip('\''))

    def _parse_test_case_info(
        self,
        test_info: dict,
        session_id: str,
        env_vars: dict[str, str],
    ) -> ParsedCase:
        """
        Parse info received from json file from allure.

        Args:
            test_info: dict parsed from json file.
            session_id: identification of allure report parsed from created timestamp
            env_vars: environment variables as string

        Returns:
            Parsed test case info.
        """
        test_status = test_info.get('status')
        allure_statuses = ['passed', 'failed', 'skipped', 'broken']
        if test_status not in allure_statuses:
            test_status = 'unknown'
        name = test_info.get('name', '')
        test_params = test_info.get('parameters', {})
        expected_step_results = self._parse_expected_steps(test_params)
        params_str = self._parse_params(test_params, test_info.get('description'))
        suite = self.parse_suite(test_info)
        refs = self._parse_reference_from_link(test_info.get('links', []))

        case = ParsedCase(
            suite=suite,
            test_name=name[:MAX_NAME_LENGTH] if len(name) > 255 else name,
            params=test_params,
            params_str=params_str,
            test_status=test_status,
            session_id=session_id,
            custom_steps=self._parse_custom_steps(test_info.get('beforeStages', [])),
            real_test_name=self._parse_real_test_name(test_info.get('fullName', '')),
            steps=self._parse_steps(test_info.get('testStage', {}), expected_step_results),
            attachments=self._parse_attachments(test_info.get('testStage', {})),
            env_vars=env_vars,
            refs=refs,
            comment=test_info.get('statusMessage', ''),
            suite_id=None,
            case_id=None,
            attributes=self._parse_custom_attributes(test_info.get('labels', []))
        )

        return case

    def _parse_params(self, test_params: dict, description: str | None = None) -> str:
        if not test_params and not description:
            return ''

        description = description or ''
        params_list = []
        for test_param in test_params:
            if self._is_forbidden(test_param.get('value', '')) or test_param.get('name', '') == 'expected':
                continue
            params_list.append(f'{test_param["name"]}: {test_param["value"]}')
        params_txt = 'Parameters:  \n{0}'.format('  \n'.join(params_list))
        return f'{description}\n{params_txt}'
