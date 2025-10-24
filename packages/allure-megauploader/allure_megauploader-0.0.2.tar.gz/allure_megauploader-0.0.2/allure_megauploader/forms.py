from django import forms
from django.contrib.auth import get_user_model
from testy.tests_representation.models import Parameter, TestPlan

from allure_megauploader.models import ServiceType, UploaderConfigV2
from allure_megauploader.uploader_lib.services import UploaderUserService

UserModel = get_user_model()


class ParsingSubmitForm(forms.Form):
    config = forms.ModelChoiceField(
        UploaderConfigV2.objects.none(),
        required=True,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    allure_url = forms.CharField(required=False,
                                 widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Start typing'}))
    allure_archive = forms.FileField(required=False, widget=forms.FileInput(attrs={'class': 'form-control'}))

    def __init__(self, request, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['config'].queryset = UploaderUserService.config_list(request.user)


class UploaderConfigForm(forms.ModelForm):
    service = forms.ModelChoiceField(
        ServiceType.objects.all(),
        required=True,
        widget=forms.Select(attrs={'class': 'form-control'})
    )

    field_order = (
        'verbose_name',
        'project', 'plan',
        'child_plan',
        'parameters',
        'auto_suite_name',
        'jira_projects',
        'custom_attributes',
        'envs_to_parse',
        'additional_parameters',
        'allowed_users',
        'owner',
        'labels',
        'add_allure_source',
    )

    class Meta:
        model = UploaderConfigV2
        fields = ('project', 'plan', 'child_plan', 'parameters', 'auto_suite_name', 'jira_projects',
                  'custom_attributes', 'envs_to_parse', 'additional_parameters', 'verbose_name', 'owner',
                  'allowed_users', 'labels', 'service', 'add_allure_source', 'skip_creating_case')
        widgets = {
            'project': forms.Select(attrs={'class': 'form-control'}),
            'plan': forms.Select(attrs={'placeholder': 'Start typing'}),
            'child_plan': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Inner test plan name'}),
            'auto_suite_name': forms.TextInput(attrs={'class': 'form-control'}),
            'jira_projects': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'TST-,TMS-,STOR-'}),
            'custom_attributes': forms.TextInput(
                attrs={'class': 'form-control', 'placeholder': 'Version,Stand,Device'}
            ),
            'envs_to_parse': forms.Textarea(
                attrs={'class': 'form-control', 'placeholder': """REAL_NAME:desired name\nPORT\n"""},
            ),
            'additional_parameters': forms.Textarea(attrs={'class': 'form-control'}),
            'verbose_name': forms.TextInput(attrs={'class': 'form-control'}),
            'labels': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'auto,release,ver 1.2.1'}),
            'owner': forms.HiddenInput(),
            'add_allure_source': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'skip_creating_case': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def __init__(self, request, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['owner'].initial = request.user
        self.fields['plan'].queryset = TestPlan.objects.none()
        if 'project' in self.data:
            try:
                project_id = int(self.data.get('project'))
                self.fields['plan'].queryset = TestPlan.objects.filter(
                    project_id=project_id,
                    is_archive=False
                ).order_by('name')
                self.fields['parameters'].queryset = Parameter.objects.filter(
                    project_id=project_id,
                ).order_by('group_name')
            except (ValueError, TypeError):
                pass
        elif self.instance.pk:
            self.fields['allowed_users'].queryset = self.instance.allowed_users
            self.fields['plan'].queryset = TestPlan.objects.filter(
                project=self.instance.project,
                is_archive=False
            ).order_by('name')
            self.fields['parameters'].queryset = Parameter.objects.filter(
                project=self.instance.project,
            ).order_by('group_name')
