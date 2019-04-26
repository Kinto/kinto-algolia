import unittest
from unittest import mock

from algoliasearch.exceptions import AlgoliaException
from pyramid import testing
from pyramid.exceptions import ConfigurationError

import kinto.core

from kinto_algolia import __version__ as algolia_version, includeme
from . import BaseWebTest
from kinto import main


class PluginSetup(BaseWebTest, unittest.TestCase):

    def test_algolia_capability_exposed(self):
        resp = self.app.get('/')
        capabilities = resp.json['capabilities']
        self.assertIn('algolia', capabilities)
        expected = {
            "version": algolia_version,
            "description": "Index and search records using Algolia.",
            "url": "https://github.com/Kinto/kinto-algolia",
            "collections": ["/buckets/bid/collections/cid"],
        }
        assert expected == capabilities['algolia']

    def test_indexer_flush(self):
        with mock.patch("kinto_algolia.indexer.Indexer.flush") as flush:
            self.app.post("/__flush__", status=202)
            assert flush.called

    def test_present_in_heartbeat(self):
        resp = self.app.get("/__heartbeat__")
        assert "algolia" in resp.json

    def test_returns_false_if_connection_fails(self):
        with mock.patch.object(self.app.app.registry.indexer, "client") as client:
            client._transporter.read.side_effect = AlgoliaException
            resp = self.app.get("/__heartbeat__", status=503)
            assert not resp.json["algolia"]

    def test_include_fails_if_missing_config(self):
        config = testing.setUp()
        settings = config.get_settings()
        kinto.core.initialize(config, '0.0.1')
        with self.assertRaises(ConfigurationError) as e:
            config.include(includeme)
            main({}, None, **settings)
        assert str(e.exception) == ('kinto-algolia needs kinto.algolia.application_id '
                                    'and kinto.algolia.api_key settings to be set.')
