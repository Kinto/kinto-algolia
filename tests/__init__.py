# -*- coding: utf-8 -*-
import os
import configparser

from kinto import main as kinto_main
from kinto.core.testing import get_user_headers, BaseWebTest as CoreWebTest


here = os.path.abspath(os.path.dirname(__file__))


class BaseWebTest(CoreWebTest):
    api_prefix = "v1"
    entry_point = kinto_main
    config = 'config.ini'

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.headers.update(get_user_headers('mat'))
        cls.indexer = cls.app.app.registry.indexer

    def tearDown(self):
        super().tearDown()
        self.indexer.join()
        self.indexer.flush()

    @classmethod
    def ini_path(cls):
        ini_local_path = os.path.join(here, 'config_local.ini')
        ini_path = os.path.join(here, 'config.ini')
        if os.path.exists(ini_local_path):
            ini_path = ini_local_path
        return ini_path

    @classmethod
    def get_app_settings(cls, extras=None):
        config = configparser.ConfigParser()
        config.read(cls.ini_path())
        settings = dict(config.items('app:main'))
        if extras:
            settings.update(extras)
        return settings
