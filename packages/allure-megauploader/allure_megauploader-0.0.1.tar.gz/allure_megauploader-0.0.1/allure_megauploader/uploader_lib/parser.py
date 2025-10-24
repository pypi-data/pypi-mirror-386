
import json
import re
from abc import ABC, abstractmethod
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from allure_megauploader.models import UploaderConfigV2
from allure_megauploader.uploader_lib.utils import ProgressRecorderContext

REAL_TEST_NAME_PLACEHOLDER = 'could not be parsed'


@dataclass
class ParsedCase:
    suite: str
    suite_id: int | None
    case_id: int | None
    test_name: str
    params: list[dict[str, Any]]
    params_str: str
    test_status: str
    session_id: str
    real_test_name: str
    custom_steps: str
    env_vars: dict[str, str]
    refs: str
    comment: str
    attributes: dict[str, Any]
    allure_history_id: str | None = None
    setup: str | None = None
    steps: list[dict[str, Any]] | None = None
    attachments: list[int] | None = None


class ParserBase(ABC):
    """Class for parsing generated allure report."""

    def __init__(
        self,
        progress_recorder: ProgressRecorderContext,
        config: UploaderConfigV2,
        report_dir: Path | None,
        jira_projects: str | None = None,
        envs_to_parse: str | None = None,
        custom_attributes: str | None = None,
        **kwargs,
    ):
        """
        Parse config, get filenames of test result from allure folder.

        Args:
            report_dir: unzipped report directory
            jira_projects: projects short name from jira in str separated by comma ('TST-, STOR-, TMS-')
            envs_to_parse: env variables names to parse in str separated by comma ('TATLIN_IMAGE, CI, EXAMPLE')
            custom_attributes: custom attribute names to parse in str separated by comma ('Ticket, Stand, Requirements')

        Raises:
            OSError: not found json filenames
        """
        self.progress_recorder = progress_recorder
        self.config = config
        self.envs_to_parse = self._parse_string_as_list(envs_to_parse, separator='\n')
        self.jira_projects = self._parse_string_as_list(jira_projects)
        self.custom_attributes = self._parse_string_as_list(custom_attributes)
        self.report_dir = report_dir

    @abstractmethod
    def parse_cases(self) -> dict[str, dict[str, Any]]:
        return NotImplemented

    @abstractmethod
    def parse_suite(self, test_info: dict[str, Any]) -> Any:
        """
        Args:
            test_info: dictionary containing all possible info about test case from allure
        """
        return NotImplemented

    @classmethod
    def _parse_string_as_list(cls, value: str | None, separator: str = ',') -> list[str]:
        """
        Returns list of str, separated by str.

        Args:
            value: string containing data separated by comma

        Returns:
            dict of cases list to suite names.
        """
        if not value:
            return []
        return [element.strip() for element in value.split(separator)]

    @classmethod
    def _parse_real_test_name(cls, full_name: str) -> str:
        """
        Parse test name from code.

        Args:
            full_name: full name including suite name and test class from allure report

        Returns:
            Test name from source code
        """
        if not full_name:
            return REAL_TEST_NAME_PLACEHOLDER
        search = re.search('#(?P<true_name>.+)', full_name)
        if not search:
            return REAL_TEST_NAME_PLACEHOLDER
        return search.group('true_name')

    def _parse_params(self, test_params: dict) -> str:
        if not test_params:
            return ''

        params_list = []
        for test_param in test_params:
            if self._is_forbidden(test_param.get('value', '')):
                continue
            params_list.append(f'{test_param["name"]}: {test_param["value"]}')
        return 'Parameters:  \n{0}'.format('  \n'.join(params_list))

    @staticmethod
    def _is_forbidden(param_value: str) -> bool:
        forbidden_words = ['None', '[]', 'object at']
        if 'lambda' in param_value:
            return True
        return param_value in forbidden_words

    @staticmethod
    def _parse_steps(test_stage: dict[str, Any]) -> str:
        if not test_stage:
            return ''
        if 'description' in test_stage:
            return str(test_stage['description'].strip())
        steps = []
        for idx, step in enumerate(test_stage.get('steps', []), start=1):
            steps.append(
                f'{idx}. {step.get("name")}'
            )
        return '\n'.join(steps)

    def _parse_reference_from_link(self, links: list[dict[str, Any]]) -> str:
        """
        Parse issue link or issue name from links in allure.

        Args:
            links: list of dicts with links info

        Returns:
            Link to jira issue or name of issue.
        """
        if not self.jira_projects:
            return ''
        for link in links:
            link_name: str = link.get('name', '')
            for jira_project in self.jira_projects:
                if jira_project in link_name:
                    return link_name
        return ''

    def get_cases_from_allure(self, suite_info: dict[str, Any]) -> list[str]:
        return list(self.flatten_children(suite_info.get('children', [])))

    def flatten_children(self, lst: list[dict[str, Any]]) -> list[str]:
        for child in lst:
            if child.get('children') is None:
                yield child.get('uid')
            else:
                yield from self.flatten_children(child.get('children', []))

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
            test_name=name[:254] if len(name) > 255 else name,
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
            attributes=self._parse_custom_attributes(test_info.get('labels', []))
        )

        return case

    @classmethod
    def group_cases_by(cls, cases: list[dict[str, Any]], grouping_key: str) -> dict[str, Any]:
        grouped_dict = defaultdict(list)
        for case in cases:
            value_to_group_by = case.get(grouping_key)
            grouped_dict[value_to_group_by].append(case)
        return grouped_dict

    @classmethod
    def _parse_replacement_names(cls, envs_to_parse: list[str]) -> dict[str, str]:
        replacement_name = None
        parsed_names = {}
        for element in envs_to_parse:
            try:
                name, replacement_name = element.split(':')
                name = name.strip()
                replacement_name = replacement_name.strip()
            except ValueError:
                name = element.strip()
            if not replacement_name:
                replacement_name = name
            parsed_names[name] = replacement_name
            replacement_name = None
        return parsed_names

    def _get_env_vars(self) -> dict[str, str]:
        with open(f'{self.report_dir}/widgets/environment.json') as json_file:
            env_vars = json.load(json_file)
        processed_envs = {}
        if self.envs_to_parse:
            parsed_names = self._parse_replacement_names(self.envs_to_parse)
            for env_var in env_vars:
                if env_var['name'] not in parsed_names:
                    continue
                processed_envs[parsed_names.get(env_var['name'], env_var['name'])] = env_var['values'][0]
            return processed_envs
        for env_var in env_vars:
            processed_envs[env_var['name']] = env_var['values'][0]
        return processed_envs

    def _parse_custom_attributes(self, labels_to_parse: list[dict[str, Any]]) -> dict[str, Any]:
        result = {}
        allowed_attributes = set(self.custom_attributes)

        if not allowed_attributes:
            return result

        for label in labels_to_parse:
            name = label.get('name')
            value = label.get('value')
            if name in allowed_attributes:
                existing_value = result.get(name)
                if isinstance(existing_value, list):
                    result[name].append(value)
                elif existing_value:
                    result[name] = [result[name], value]
                else:
                    result[name] = value
        return result
