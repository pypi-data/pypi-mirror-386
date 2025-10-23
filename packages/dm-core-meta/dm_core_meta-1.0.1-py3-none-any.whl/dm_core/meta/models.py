from django.db import models


class AppConfigModel(models.Model):

    key = models.CharField(primary_key=True, max_length=255)
    value = models.JSONField(null=False)

    class Meta:
        db_table = 'dm_core_meta_appconfig'