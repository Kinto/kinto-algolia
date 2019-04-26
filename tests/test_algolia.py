import unittest
from unittest import mock

from algoliasearch.exceptions import AlgoliaException

from . import BaseWebTest


class RecordIndexing(BaseWebTest, unittest.TestCase):

    def setUp(self):
        self.app.put("/buckets/bid", headers=self.headers)
        self.app.put("/buckets/bid/collections/cid", headers=self.headers)
        resp = self.app.post_json("/buckets/bid/collections/cid/records",
                                  {"data": {"hello": "world"}},
                                  headers=self.headers)
        self.record = resp.json["data"]
        self.indexer.join()

    def test_new_index_settings_are_updated(self):
        self.app.put_json("/buckets/bid/collections/cid",
                          {"data": {"algolia:settings": {}}},
                          headers=self.headers)

    def test_new_records_are_indexed(self):
        resp = self.app.post("/buckets/bid/collections/cid/search",
                             headers=self.headers)
        result = resp.json
        assert len(result["hits"]) == 1
        hit = result["hits"][0]
        del hit['_highlightResult']
        hit['id'] = hit.pop('objectID')
        assert hit == self.record

    def test_deleted_records_are_unindexed(self):
        rid = self.record["id"]
        self.app.delete("/buckets/bid/collections/cid/records/{}".format(rid),
                        headers=self.headers)
        self.indexer.join()

        resp = self.app.post("/buckets/bid/collections/cid/search",
                             headers=self.headers)
        result = resp.json
        assert len(result["hits"]) == 0

    def test_response_is_served_if_indexer_fails(self):
        with mock.patch.object(self.app.app.registry.indexer, "client") as client:
            client.init_index.return_value.batch.side_effect = AlgoliaException
            r = self.app.post_json("/buckets/bid/collections/cid/records",
                                   {"data": {"hola": "mundo"}},
                                   headers=self.headers)
            assert r.status_code == 201

    def test_a_statsd_timer_is_used_if_configured(self):
        statsd_client = self.app.app.registry.statsd._client
        with mock.patch.object(statsd_client, 'timing') as mocked:
            self.app.post_json("/buckets/bid/collections/cid/records",
                               {"data": {"hola": "mundo"}},
                               headers=self.headers)
            timers = set(c[0][0] for c in mocked.call_args_list)
            assert 'plugins.algolia.index' in timers
