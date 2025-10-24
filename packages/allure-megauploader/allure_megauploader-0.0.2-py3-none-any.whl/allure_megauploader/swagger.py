from django.utils.decorators import method_decorator
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema

tasks_list_schema = method_decorator(
    name='list',
    decorator=swagger_auto_schema(
        manual_parameters=[
            openapi.Parameter(
                'status',
                openapi.IN_QUERY,
                type=openapi.TYPE_STRING,
                description='Case insensitive filter by status',
            ),
        ],
    ),
)
