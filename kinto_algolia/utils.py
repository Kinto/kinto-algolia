from pyramid.settings import aslist

from kinto.core import utils as core_utils


def is_monitoring_collection(registry, bucket_id, collection_id=None):
    resources_uri = aslist(registry.settings.get("algolia.resources", ""))

    for resource_uri in resources_uri:
        resource_name, matchdict = core_utils.view_lookup_registry(
            registry, resource_uri
        )
        if (resource_name == "bucket" and bucket_id == matchdict["id"]) or (
            collection_id is None and bucket_id == matchdict["bucket_id"]
        ):
            return True

        is_matching_collection = (
            resource_name == "collection"
            and bucket_id == matchdict["bucket_id"]
            and collection_id == matchdict["id"]
        )
        if is_matching_collection:
            return True
