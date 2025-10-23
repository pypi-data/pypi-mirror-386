from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class MediaflowVideoConfig(AppConfig):
    name = "mediaflowvideo"
    label = "mediaflowvideo"
    verbose_name = _("Mediaflow Video")
    default_auto_field = "django.db.models.BigAutoField"
