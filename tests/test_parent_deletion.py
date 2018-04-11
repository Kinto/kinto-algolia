import mock
import unittest

from . import BaseWebTest


class ParentDeletion(BaseWebTest, unittest.TestCase):

    def setUp(self):
        self.app.put("/buckets/bid", headers=self.headers)
        self.app.put("/buckets/bid/collections/cid", headers=self.headers)
        self.app.post_json("/buckets/bid/collections/cid/records",
                           {"data": {"hello": "world"}},
                           headers=self.headers)

    def test_index_is_deleted_when_collection_is_deleted(self):
        with mock.patch.object(self.app.app.registry.indexer, "client") as client:
            self.app.delete("/buckets/bid/collections/cid", headers=self.headers)
        client.delete_index.assert_called_with('kinto-bid-cid')

    def test_index_is_deleted_when_bucket_is_deleted(self):
        with mock.patch.object(self.app.app.registry.indexer, "client") as client:
            client.list_indexes.return_value = {"items": [
                {"name": "kinto-foo-bar"},
                {"name": "kinto-bid-cid"}
            ]}
            self.app.delete("/buckets/bid", headers=self.headers)
        client.delete_index.assert_called_with('kinto-bid-cid')