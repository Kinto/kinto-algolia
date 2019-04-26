import argparse
import logging
import time
import sys

from algoliasearch.exceptions import AlgoliaException
from pyramid.paster import bootstrap

from kinto.core.storage.exceptions import RecordNotFoundError
from kinto.core.storage import Sort, Filter
from kinto.core.utils import COMPARISON


DEFAULT_CONFIG_FILE = "config/kinto.ini"

logger = logging.getLogger(__package__)


def main(cli_args=None):
    if cli_args is None:
        cli_args = sys.argv[1:]

    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--ini",
        help="Application configuration file",
        dest="ini_file",
        required=False,
        default=DEFAULT_CONFIG_FILE,
    )
    parser.add_argument("-b", "--bucket", help="Bucket name.", type=str)
    parser.add_argument("-c", "--collection", help="Collection name.", type=str)
    args = parser.parse_args(args=cli_args)

    print("Load config...")
    env = bootstrap(args.ini_file)
    registry = env["registry"]

    # Make sure that kinto-algolia is configured.
    try:
        indexer = registry.indexer
    except AttributeError:
        logger.error("kinto-algolia not available.")
        return 62

    bucket_id = args.bucket
    collection_id = args.collection

    # Get index settings from collection metadata.
    try:
        settings = get_index_settings(registry.storage, bucket_id, collection_id)
    except RecordNotFoundError:
        logger.error("No collection '%s' in bucket '%s'" % (collection_id, bucket_id))
        return 63

    recreate_index(indexer, bucket_id, collection_id, settings)
    print("Waiting for Algolia quota stats to propagate.")
    for _ in range(3):
        time.sleep(1)  # Wait a couple of seconds
        print(".", end="")
        sys.stdout.flush()
    print()
    reindex_records(indexer, registry.storage, bucket_id, collection_id)

    return 0


def get_index_settings(storage, bucket_id, collection_id):
    # Open collection metadata.
    # XXX: https://github.com/Kinto/kinto/issues/710
    metadata = storage.get(
        parent_id="/buckets/%s" % bucket_id,
        collection_id="collection",
        object_id=collection_id,
    )
    return metadata.get("algolia:settings")


def recreate_index(indexer, bucket_id, collection_id, settings):
    index_name = indexer.indexname(bucket_id, collection_id)
    # Delete existing index.
    indexer.delete_index(bucket_id, collection_id)
    print("Old index '%s' deleted." % index_name)
    # Recreate the index with the new settings.
    indexer.create_index(bucket_id, collection_id, settings=settings)
    print("New index '%s' created." % index_name)


def get_paginated_records(storage, bucket_id, collection_id, limit=5000):
    # We can reach the storage_fetch_limit, so we use pagination.
    parent_id = "/buckets/%s/collections/%s" % (bucket_id, collection_id)
    sorting = [Sort("last_modified", -1)]
    pagination_rules = []
    while "not gone through all pages":
        records, _ = storage.get_all(
            parent_id=parent_id,
            collection_id="record",
            pagination_rules=pagination_rules,
            sorting=sorting,
            limit=limit,
        )
        yield records

        if len(records) < limit:
            break  # Done.

        smallest_timestamp = records[-1]["last_modified"]
        pagination_rules = [
            [Filter("last_modified", smallest_timestamp, COMPARISON.LT)]
        ]


def reindex_records(indexer, storage, bucket_id, collection_id):
    total = 0
    for records in get_paginated_records(storage, bucket_id, collection_id):
        try:
            with indexer.bulk() as bulk:
                for record in records:
                    bulk.index_record(bucket_id, collection_id, record=record)
                print(".", end="")
                sys.stdout.flush()
            total += len(list(bulk.operations.items())[0][1])
        except AlgoliaException:
            logger.exception("Failed to index record")
            break
    print("\n%s records reindexed." % total)
