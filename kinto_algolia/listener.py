import logging

from algoliasearch.helpers import AlgoliaException
from kinto.core.events import ACTIONS


logger = logging.getLogger(__name__)


def on_collection_created(event):
    indexer = event.request.registry.indexer
    bucket_id = event.payload["bucket_id"]
    for created in event.impacted_records:
        collection_id = created["new"]["id"]
        settings = created["new"].get("algolia:settings")
        indexer.create_index(bucket_id, collection_id, settings=settings)


def on_collection_updated(event):
    indexer = event.request.registry.indexer
    bucket_id = event.payload["bucket_id"]
    for updated in event.impacted_records:
        collection_id = updated["new"]["id"]
        old_schema = updated["old"].get("algolia:settings")
        new_schema = updated["new"].get("algolia:settings")
        # Create if there was no index before.
        if old_schema != new_schema:
            indexer.update_index(bucket_id, collection_id, schema=new_schema)


def on_collection_deleted(event):
    indexer = event.request.registry.indexer
    bucket_id = event.payload["bucket_id"]
    for deleted in event.impacted_records:
        collection_id = deleted["old"]["id"]
        indexer.delete_index(bucket_id, collection_id)


def on_bucket_deleted(event):
    indexer = event.request.registry.indexer
    for deleted in event.impacted_records:
        bucket_id = deleted["old"]["id"]
        indexer.delete_index(bucket_id)


def on_record_changed(event):
    indexer = event.request.registry.indexer

    bucket_id = event.payload["bucket_id"]
    collection_id = event.payload["collection_id"]
    action = event.payload["action"]
    try:
        with indexer.bulk() as bulk:
            for change in event.impacted_records:
                if action == ACTIONS.DELETE.value:
                    bulk.unindex_record(bucket_id,
                                        collection_id,
                                        record=change["old"])
                else:
                    bulk.index_record(bucket_id,
                                      collection_id,
                                      record=change["new"])
    except AlgoliaException:
        logger.exception("Failed to index record")


def on_server_flushed(event):
    indexer = event.request.registry.indexer
    indexer.flush()
