
from rest_framework import serializers
from rest_framework.serializers import Serializer


class TestPlanPreviewSerializer(Serializer):
    id = serializers.IntegerField()
    title = serializers.CharField()
    parent_title = serializers.CharField()


class UploaderUserSerializer(Serializer):
    id = serializers.IntegerField()
    username = serializers.CharField()
