import unittest
from unittest import mock

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
        client.init_index.assert_called_once_with('kinto-bid-cid')
        client.init_index.return_value.delete.assert_called_once()

    def test_index_is_deleted_when_bucket_is_deleted(self):
        with mock.patch.object(self.app.app.registry.indexer, "client") as client:
            client.list_indices.return_value = {"items": [
                {"name": "kinto-foo-bar"},
                {"name": "kinto-bid-cid"}
            ]}
            self.app.delete("/buckets/bid", headers=self.headers)
        client.init_index.assert_called_once_with('kinto-bid-cid')
        client.init_index.return_value.delete.assert_called_once()
