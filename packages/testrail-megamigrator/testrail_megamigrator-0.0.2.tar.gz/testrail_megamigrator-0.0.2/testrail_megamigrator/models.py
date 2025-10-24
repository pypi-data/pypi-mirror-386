
from django.contrib.auth import get_user_model
from django.db import models

UserModel = get_user_model()


def default_custom_fields():
    return {
        'custom_description': 'description',
        'custom_steps': 'scenario',
        'custom_preconds': 'setup'
    }


class TestrailSettings(models.Model):
    verbose_name = models.CharField(max_length=255)
    testrail_api_url = models.CharField(max_length=255)
    testy_attachments_url = models.CharField(max_length=255)
    custom_fields_matcher = models.JSONField(default=default_custom_fields)

    def __str__(self) -> str:
        return self.verbose_name


class TestrailBackup(models.Model):
    name = models.CharField(max_length=255)
    filepath = models.CharField(max_length=255)

    def __str__(self) -> str:
        return self.name
