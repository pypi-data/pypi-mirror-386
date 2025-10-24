
from rest_framework.exceptions import ValidationError
from rest_framework.fields import CharField
from rest_framework.serializers import FileField, ModelSerializer, PrimaryKeyRelatedField, Serializer

from allure_megauploader.models import UploaderConfigV2, UserTask


class AllureUploaderSerializerV2(Serializer):
    allure_url = CharField(required=False)
    allure_file = FileField(required=False)
    plans_hierarchy = CharField(required=False)
    hierarchy_separator = CharField(required=False, default='->')
    config = PrimaryKeyRelatedField(queryset=UploaderConfigV2.objects.all(), many=False, required=True)

    def validate(self, attrs):
        if not attrs.get('allure_url') and not attrs.get('allure_file'):
            raise ValidationError('Allure report source was not provided')
        return attrs


class APITaskResponseSerializerV2(Serializer):
    task_id = CharField()


class AllureUploaderConfigV2Serializer(ModelSerializer):
    class Meta:
        model = UploaderConfigV2
        exclude = ['is_deleted', 'deleted_at', 'created_at', 'updated_at']


class UserTaskSerializer(ModelSerializer):
    class Meta:
        model = UserTask
        fields = '__all__'
