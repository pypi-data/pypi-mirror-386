
from django import forms
from django.contrib.postgres.forms import SimpleArrayField

from testrail_megamigrator.models import TestrailBackup, TestrailSettings


class MigratorDownloadBaseForm(forms.Form):
    project_id = forms.IntegerField(
        required=True,
        widget=forms.NumberInput(attrs={'class': 'form-control'})
    )
    download_attachments = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
    testrail_config = forms.ModelChoiceField(
        TestrailSettings.objects.all(),
        required=True,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    backup_filename = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Tatlin'})
    )
    testrail_login = forms.CharField(
        widget=forms.TextInput(
            attrs={'class': 'form-control', 'placeholder': 'i.ivanov'})
    )
    testrail_password = forms.CharField(
        widget=forms.PasswordInput(
            attrs={'class': 'form-control', 'placeholder': 'Start typing'})
    )


class MigratorUploadBaseForm(forms.Form):
    testrail_config = forms.ModelChoiceField(
        TestrailSettings.objects.all(),
        required=True,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    testrail_backup = forms.ModelChoiceField(
        TestrailBackup.objects.all(),
        required=True,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    testrail_login = forms.CharField(
        widget=forms.TextInput(
            attrs={'class': 'form-control', 'placeholder': 'i.ivanov'})
    )
    testrail_password = forms.CharField(
        widget=forms.PasswordInput(
            attrs={'class': 'form-control', 'placeholder': 'Start typing'})
    )


class MigratorSuiteDownloadForm(MigratorDownloadBaseForm):
    testrail_suite_ids = SimpleArrayField(
        forms.IntegerField(),
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )


class MigratorSuiteUploadForm(MigratorUploadBaseForm):
    testy_project_id = forms.IntegerField(
        required=True,
        widget=forms.NumberInput(attrs={'class': 'form-control'})
    )


class MigratorProjectDownloadForm(MigratorDownloadBaseForm):
    ignore_completed = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )


class MigratorProjectUploadForm(MigratorUploadBaseForm):
    upload_root_runs = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )


class MigratorMilestoneDownloadForm(MigratorDownloadBaseForm):
    testrail_milestone_ids = SimpleArrayField(
        forms.IntegerField(),
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    ignore_completed = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )


class MigratorMilestoneUploadForm(MigratorUploadBaseForm):
    testy_project_id = forms.IntegerField(
        required=True,
        widget=forms.NumberInput(attrs={'class': 'form-control'})
    )
    upload_root_runs = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )


class MigratorPlanRunDownloadForm(MigratorDownloadBaseForm):
    testrail_plan_ids = SimpleArrayField(
        forms.IntegerField(),
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    testrail_run_ids = SimpleArrayField(
        forms.IntegerField(),
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )


class MigratorPlanRunUploadForm(MigratorUploadBaseForm):
    testy_project_id = forms.IntegerField(
        required=True,
        widget=forms.NumberInput(attrs={'class': 'form-control'})
    )
    testy_plan_id = forms.IntegerField(
        required=False,
        widget=forms.NumberInput(attrs={'class': 'form-control'})
    )


class TestrailSettingsForm(forms.ModelForm):
    field_order = (
        'verbose_name', 'testrail_api_url', 'testy_attachments_url', 'custom_fields_matcher'
    )

    class Meta:
        model = TestrailSettings
        fields = (
            'verbose_name', 'testrail_api_url', 'testy_attachments_url', 'custom_fields_matcher'
        )
        widgets = {
            'verbose_name': forms.TextInput(attrs={'class': 'form-control'}),
            'testrail_api_url': forms.TextInput(attrs={'class': 'form-control'}),
            'testy_attachments_url': forms.TextInput(attrs={'class': 'form-control'}),
            'custom_fields_matcher': forms.Textarea(attrs={'class': 'form-control'})
        }
