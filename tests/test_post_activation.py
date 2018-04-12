import unittest

from . import BaseWebTest


class PostActivation(BaseWebTest, unittest.TestCase):

    def setUp(self):
        app = self.make_app(settings={"kinto.includes": ""})
        capabilities = app.get("/").json["capabilities"]
        assert "algolia" not in capabilities

        app.put("/buckets/bid", headers=self.headers)
        app.put("/buckets/bid/collections/cid", headers=self.headers)
        app.post_json("/buckets/bid/collections/cid/records",
                      {"data": {"before": "indexing"}},
                      headers=self.headers)

    def test_search_does_not_fail(self):
        resp = self.app.get("/buckets/bid/collections/cid/records",
                            headers=self.headers)
        assert len(resp.json["data"]) == 1

        resp = self.app.get("/buckets/bid/collections/cid/search",
                            headers=self.headers)
        results = resp.json
        assert len(results["hits"]) == 0

    def test_record_creation_does_not_fail(self):
        self.app.post_json("/buckets/bid/collections/cid/records",
                           {"data": {"after": "indexing"}},
                           headers=self.headers)
        self.indexer.join()
        resp = self.app.get("/buckets/bid/collections/cid/search",
                            headers=self.headers)
        results = resp.json
        assert len(results["hits"]) == 1
        assert results["hits"][0]["after"] == "indexing"
