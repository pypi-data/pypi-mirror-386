"""
Backup/Restore application initialization.
"""

from django.apps import AppConfig


class BackupRestoreConfig(AppConfig):
    name = 'openedx_learning.apps.authoring.backup_restore'
    verbose_name = "Learning Core > Authoring > Backup Restore"
    default_auto_field = 'django.db.models.BigAutoField'
    label = "oel_backup_restore"
