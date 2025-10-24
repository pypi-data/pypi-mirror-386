
import copy
from logging import getLogger
from typing import Any

from celery_progress.backend import ProgressRecorder
from django.db.models import Subquery, fields

logger = getLogger('uploader-utils')


def matched_dict(list_of_dicts: list[dict], conditional_key: str, conditional_val: Any) -> dict[str, Any]:
    """
    Find and return the dictionary from the list of dictionaries that matched the condition.

    key == value

    Args:
        list_of_dicts: the list of dictionaries:  list[dict]
        conditional_key: the key
        conditional_val: the expected value

    Returns:
        the dictionary or None
    """
    if conditional_key.endswith('id'):
        conditional_val = int(conditional_val)
    for dict_item in list_of_dicts:
        if isinstance(dict_item, dict) and dict_item.get(conditional_key) == conditional_val:
            return copy.deepcopy(dict_item)
    return {}


def get_title(plan_name, parameters):
    if not parameters:
        return plan_name
    return '{0} [{1}]'.format(
        plan_name, ', '.join(parameter.data for parameter in parameters)
    )


class ConcatSubquery(Subquery):
    template = 'ARRAY_TO_STRING(ARRAY(%(subquery)s), %(separator)s)'
    output_field = fields.CharField()

    def __init__(self, *args, separator=', ', **kwargs):
        self.separator = separator
        super().__init__(*args, **kwargs)

    def as_sql(self, compiler, connection, template=None, **extra_context):
        extra_context['separator'] = '%s'
        sql, sql_params = super().as_sql(compiler, connection, template, **extra_context)
        sql_params = sql_params + (self.separator,)
        return sql, sql_params


class ProgressRecorderContext(ProgressRecorder):
    def __init__(self, task, total, debug=False, description='Task started'):
        self.debug = debug
        self.current = 0
        self.total = total
        if self.debug:
            return
        super().__init__(task)
        self.set_progress(current=self.current, total=total, description=description)

    def progress_step(self, description: str):
        logger.info(description)
        if self.debug:
            return
        self.current += 1
        self.set_progress(self.current, self.total, description)

    def clear_progress(self):
        self.current = 0
