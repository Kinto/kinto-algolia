import unittest
from unittest import mock

from algoliasearch.exceptions import AlgoliaException
from kinto.core.testing import get_user_headers

from . import BaseWebTest


class SearchView(BaseWebTest, unittest.TestCase):
    def setUp(self):
        self.app.put("/buckets/bid", headers=self.headers)
        self.app.put("/buckets/bid/collections/cid", headers=self.headers)

    def test_search_response_error_400_indexer_fails(self):
        with mock.patch.object(self.app.app.registry.indexer, "client") as client:
            client.init_index.return_value.search.side_effect = AlgoliaException
            self.app.post("/buckets/bid/collections/cid/search", headers=self.headers, status=400)

    def test_search_response_error_400_with_wrong_body(self):
        self.app.post("/buckets/bid/collections/cid/search", 'blah',
                      headers=self.headers, status=400)

    def test_invalid_search_query(self):
        body = {"whatever": {"wrong": "bad"}}
        resp = self.app.post_json("/buckets/bid/collections/cid/search",
                                  body,
                                  headers=self.headers,
                                  status=400)
        assert resp.json["message"] == "Algolia error in body: Unknown parameter: whatever"

    def test_search_on_empty_collection_returns_empty_list(self):
        resp = self.app.post("/buckets/bid/collections/cid/search",
                             headers=self.headers)
        result = resp.json
        assert len(result["hits"]) == 0

    def test_querystring_search_is_supported(self):
        self.app.post_json("/buckets/bid/collections/cid/records",
                           {"data": {"age": 12}}, headers=self.headers)
        self.app.post_json("/buckets/bid/collections/cid/records",
                           {"data": {"age": 21}}, headers=self.headers)
        self.indexer.join()
        resp = self.app.get("/buckets/bid/collections/cid/search?filters=age<15",
                            headers=self.headers)
        result = resp.json
        assert len(result["hits"]) == 1
        assert result["hits"][0]["age"] == 12

    def test_empty_querystring_returns_all_results(self):
        self.app.post_json("/buckets/bid/collections/cid/records",
                           {"data": {"age": 12}}, headers=self.headers)
        self.app.post_json("/buckets/bid/collections/cid/records",
                           {"data": {"age": 21}}, headers=self.headers)
        self.indexer.join()
        resp = self.app.get("/buckets/bid/collections/cid/search",
                            headers=self.headers)
        result = resp.json
        assert len(result["hits"]) == 2


# ALGOLIA SEARCH DOESN'T SUPPORT LIMITING YET
# https://github.com/algolia/algoliasearch-client-python/issues/365
# class LimitedResults(BaseWebTest, unittest.TestCase):
#     def get_app(self, settings):
#         app = self.make_app(settings=settings)
#         app.put("/buckets/bid", headers=self.headers)
#         app.put_json("/buckets/bid/collections/cid",
#                      {"data": {"algolia:settings": {}}},
#                      headers=self.headers)
#         requests = [{
#             "method": "POST",
#             "path": "/buckets/bid/collections/cid/records",
#             "body": {"data": {"age": i}}
#         } for i in range(5)]
#         app.post_json("/batch", {"requests": requests}, headers=self.headers)
#         sleep(1)  # Wait for indexing
#         return app
#
#     def test_the_number_of_responses_is_limited_by_paginate_by_setting(self):
#         app = self.get_app({"paginate_by": 2})
#         resp = app.get("/buckets/bid/collections/cid/search", headers=self.headers)
#         result = resp.json
#         assert len(result["hits"]) == 2
#
#     def test_the_number_of_responses_is_limited_by_max_fetch_size_setting(self):
#         app = self.get_app({"storage_max_fetch_size": 2})
#         resp = app.get("/buckets/bid/collections/cid/search", headers=self.headers)
#         result = resp.json
#         assert len(result["hits"]) == 2
#
#     def test_the_number_of_responses_is_limited_by_smaller_limit(self):
#         app = self.get_app({"paginate_by": 4, "storage_max_fetch_size": 2})
#         resp = app.get("/buckets/bid/collections/cid/search", headers=self.headers)
#         result = resp.json
#         assert len(result["hits"]) == 2
#
#     def test_the_number_of_responses_is_limited_by_only_defined_limit(self):
#         app = self.get_app({"paginate_by": 0, "storage_max_fetch_size": 2})
#         resp = app.get("/buckets/bid/collections/cid/search", headers=self.headers)
#         result = resp.json
#         assert len(result["hits"]) == 2
#
#     def test_size_specified_in_query_is_taken_into_account(self):
#         app = self.get_app({"paginate_by": 3})
#         query = {
#             "hitsPerPage": 2
#         }
#         resp = app.post_json("/buckets/bid/collections/cid/search", query,
#                              headers=self.headers)
#         result = resp.json
#         assert len(result["hits"]) == 2
#
#     def test_size_specified_in_query_is_caped_by_setting(self):
#         app = self.get_app({"paginate_by": 3})
#         query = {
#             "hitsPerPage": 4
#         }
#         resp = app.post_json("/buckets/bid/collections/cid/search", query,
#                              headers=self.headers)
#         result = resp.json
#         assert len(result["hits"]) == 3


class PermissionsCheck(BaseWebTest, unittest.TestCase):
    def test_search_is_allowed_if_write_on_bucket(self):
        body = {"permissions": {"write": ["system.Everyone"]}}
        self.app.put_json("/buckets/bid", body, headers=self.headers)
        self.app.put("/buckets/bid/collections/cid", headers=self.headers)

        self.app.post("/buckets/bid/collections/cid/search", status=200)

    def test_search_is_allowed_if_read_on_bucket(self):
        body = {"permissions": {"read": ["system.Everyone"]}}
        self.app.put_json("/buckets/bid", body, headers=self.headers)
        self.app.put("/buckets/bid/collections/cid", headers=self.headers)

        self.app.post("/buckets/bid/collections/cid/search", status=200)

    def test_search_is_allowed_if_write_on_collection(self):
        self.app.put("/buckets/bid", headers=self.headers)
        body = {"permissions": {"write": ["system.Everyone"]}}
        self.app.put_json("/buckets/bid/collections/cid", body, headers=self.headers)

        self.app.post("/buckets/bid/collections/cid/search", status=200)

    def test_search_is_allowed_if_read_on_collection(self):
        self.app.put("/buckets/bid", headers=self.headers)
        body = {"permissions": {"read": ["system.Everyone"]}}
        self.app.put_json("/buckets/bid/collections/cid", body, headers=self.headers)

        self.app.post("/buckets/bid/collections/cid/search", status=200)

    def test_search_is_not_allowed_by_default(self):
        self.app.put("/buckets/bid", headers=self.headers)
        self.app.put("/buckets/bid/collections/cid", headers=self.headers)

        self.app.post("/buckets/bid/collections/cid/search", status=401)
        headers = get_user_headers("cual", "quiera")
        self.app.post("/buckets/bid/collections/cid/search", status=403, headers=headers)

    def test_search_is_not_allowed_if_only_read_on_certain_records(self):
        self.app.put("/buckets/bid", headers=self.headers)
        body = {"permissions": {"record:create": ["system.Authenticated"]}}
        self.app.put_json("/buckets/bid/collections/cid", body, headers=self.headers)
        headers = get_user_headers("toto")
        self.app.post_json("/buckets/bid/collections/cid/records", {"data": {"pi": 42}},
                           headers=headers)

        self.app.post("/buckets/bid/collections/cid/search", status=403, headers=headers)
