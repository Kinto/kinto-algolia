import logging
from copy import deepcopy
from contextlib import contextmanager

from algoliasearch.http.verb import Verb
from algoliasearch.search_client import SearchClient
from algoliasearch.exceptions import AlgoliaException
from pyramid.exceptions import ConfigurationError


logger = logging.getLogger(__name__)


class Indexer(object):
    def __init__(self, application_id, api_key, prefix="kinto"):
        self.client = SearchClient.create(application_id, api_key)
        self.prefix = prefix
        self.tasks = []

    def join(self):
        for indexname, taskID in self.tasks:
            index = self.client.init_index(indexname)
            index.wait_task(taskID)
        self.tasks = []

    def set_extra_headers(self, headers):
        self.client._config.headers.update(headers)

    def indexname(self, bucket_id, collection_id):
        return "{}-{}-{}".format(self.prefix, bucket_id, collection_id)

    def create_index(
        self, bucket_id, collection_id, settings=None, wait_for_creation=False
    ):
        if settings is None:
            settings = {}
        self.update_index(
            bucket_id, collection_id, settings=settings, wait_for_task=wait_for_creation
        )

    def update_index(
        self, bucket_id, collection_id, settings=None, wait_for_task=False
    ):
        indexname = self.indexname(bucket_id, collection_id)
        if settings is not None:
            index = self.client.init_index(indexname)
            res = index.set_settings(settings, {"forwardToReplicas": True})
            if wait_for_task:
                res.wait()
            else:
                self.tasks.append((indexname, res[0]["taskID"]))

    def delete_index(self, bucket_id, collection_id=None):
        if collection_id is None:
            response = self.client.list_indices()
            index_prefix = self.indexname(bucket_id, "")
            collections = [
                i["name"]
                for i in response["items"]
                if i["name"].startswith(index_prefix)
            ]
        else:
            collections = [self.indexname(bucket_id, collection_id)]

        for indexname in collections:
            try:
                self.client.init_index(indexname).delete()
            except AlgoliaException as e:  # pragma: no cover
                if "HTTP Code: 404" not in str(e):
                    raise

    def search(self, bucket_id, collection_id, **kwargs):
        indexname = self.indexname(bucket_id, collection_id)
        index = self.client.init_index(indexname)
        query = kwargs.pop("query", "")
        return index.search(query, kwargs)

    def flush(self):
        response = self.client.list_indices()
        for index in response["items"]:
            indexname = index["name"]
            if indexname.startswith(self.prefix):
                index = self.client.init_index(indexname)
                index.clear_objects().wait()
                index.delete().wait()

    def isalive(self):
        self.client._transporter.read(Verb.GET, "1/isalive", {}, None)

    @contextmanager
    def bulk(self):
        bulk = BulkClient(self)
        yield bulk

        for indexname, requests in bulk.operations.items():
            index = self.client.init_index(indexname)
            res = index.batch(requests)
            self.tasks.append((indexname, res[0]["taskID"]))


class BulkClient:
    def __init__(self, indexer):
        self.indexer = indexer
        self.operations = {}

    def index_record(self, bucket_id, collection_id, record, id_field="id"):
        indexname = self.indexer.indexname(bucket_id, collection_id)
        self.operations.setdefault(indexname, [])
        obj = deepcopy(record)
        record_id = obj.pop(id_field)
        obj["objectID"] = record_id
        self.operations[indexname].append({"action": "addObject", "body": obj})

    def unindex_record(self, bucket_id, collection_id, record, id_field="id"):
        indexname = self.indexer.indexname(bucket_id, collection_id)
        record_id = record[id_field]
        self.operations.setdefault(indexname, [])
        self.operations[indexname].append(
            {"action": "deleteObject", "body": {"objectID": record_id}}
        )


def heartbeat(request):
    """Test that Algolia is operationnal.

    :param request: current request object
    :type request: :class:`~pyramid:pyramid.request.Request`
    :returns: ``True`` is everything is ok, ``False`` otherwise.
    :rtype: bool
    """
    indexer = request.registry.indexer
    try:
        indexer.isalive()
    except Exception as e:
        logger.exception(e)
        return False
    else:
        return True


def load_from_config(config):
    settings = config.get_settings()
    application_id = settings.get("algolia.application_id")
    api_key = settings.get("algolia.api_key")
    if application_id is None or api_key is None:
        message = (
            "kinto-algolia needs kinto.algolia.application_id "
            "and kinto.algolia.api_key settings to be set."
        )
        raise ConfigurationError(message)

    prefix = settings.get("algolia.index_prefix", "kinto")
    indexer = Indexer(application_id=application_id, api_key=api_key, prefix=prefix)
    return indexer
