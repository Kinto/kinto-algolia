import logging

from algoliasearch.exceptions import AlgoliaException
from kinto.core.events import ACTIONS
from .utils import is_monitoring_collection


logger = logging.getLogger(__name__)


def on_collection_created(event):
    registry = event.request.registry
    indexer = registry.indexer
    bucket_id = event.payload["bucket_id"]
    for created in event.impacted_records:
        collection_id = created["new"]["id"]
        if is_monitoring_collection(registry, bucket_id, collection_id):
            settings = created["new"].get("algolia:settings")
            indexer.create_index(bucket_id, collection_id, settings=settings)


def on_collection_updated(event):
    registry = event.request.registry
    indexer = registry.indexer
    bucket_id = event.payload["bucket_id"]
    for updated in event.impacted_records:
        collection_id = updated["new"]["id"]

        if is_monitoring_collection(registry, bucket_id, collection_id):
            old_settings = updated["old"].get("algolia:settings")
            new_settings = updated["new"].get("algolia:settings")
            # Create if there was no index before.
            if old_settings != new_settings:
                indexer.update_index(bucket_id, collection_id, settings=new_settings)


def on_collection_deleted(event):
    registry = event.request.registry
    indexer = registry.indexer
    bucket_id = event.payload["bucket_id"]
    for deleted in event.impacted_records:
        collection_id = deleted["old"]["id"]
        if is_monitoring_collection(registry, bucket_id, collection_id):
            indexer.delete_index(bucket_id, collection_id)


def on_bucket_deleted(event):
    registry = event.request.registry
    indexer = registry.indexer
    for deleted in event.impacted_records:
        bucket_id = deleted["old"]["id"]
        if is_monitoring_collection(registry, bucket_id):
            indexer.delete_index(bucket_id)


def on_record_changed(event):
    registry = event.request.registry
    indexer = registry.indexer

    bucket_id = event.payload["bucket_id"]
    collection_id = event.payload["collection_id"]

    if is_monitoring_collection(registry, bucket_id, collection_id):
        action = event.payload["action"]
        try:
            with indexer.bulk() as bulk:
                for change in event.impacted_records:
                    if action == ACTIONS.DELETE.value:
                        bulk.unindex_record(
                            bucket_id, collection_id, record=change["old"]
                        )
                    else:
                        bulk.index_record(
                            bucket_id, collection_id, record=change["new"]
                        )
        except AlgoliaException:
            logger.exception("Failed to index record")


def on_server_flushed(event):
    indexer = event.request.registry.indexer
    indexer.flush()
