import os
import traceback

from django.apps import AppConfig

from .classes.app_mixins.auto_migration_mixin import AutoMigrationMixin
from .classes.app_mixins.auto_urlpatterns_mixin import AutoUrlPatternsMixin


class ValarConfig(AutoMigrationMixin, AutoUrlPatternsMixin, AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = __package__

    def ready(self):
        if os.environ.get('RUN_MAIN') == 'true':
            try:
                from .dao.frame import MetaFrame
                # getattr(super(), 'set_url', None)()
                # getattr(super(), 'auto_migrate', None)()
                MetaFrame()
            except Exception as e:
                traceback.print_exc()
                print('ERROR', e)
