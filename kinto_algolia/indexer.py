import logging
from contextlib import contextmanager

from algoliasearch import algoliasearch
from algoliasearch.helpers import AlgoliaException
from pyramid.exceptions import ConfigurationError


logger = logging.getLogger(__name__)


class Indexer(object):
    def __init__(self, application_id, api_key, prefix="kinto"):
        self.client = algoliasearch.Client(application_id, api_key)
        self.prefix = prefix

    def set_extra_headers(self, headers):
        self.client.set_extra_headers(**headers)

    def indexname(self, bucket_id, collection_id):
        return "{}-{}-{}".format(self.prefix, bucket_id, collection_id)

    def create_index(self, bucket_id, collection_id, settings=None):
        self.update_index(bucket_id, collection_id, settings)

    def update_index(self, bucket_id, collection_id, settings=None):
        indexname = self.indexname(bucket_id, collection_id)
        if settings is not None:
            index = self.client.init_index(indexname)
            index.set_settings(settings, forward_to_slaves=True, forward_to_replicas=True)

    def delete_index(self, bucket_id, collection_id=None):
        if collection_id is None:
            collection_id = "*"
        indexname = self.indexname(bucket_id, collection_id)
        try:
            return self.client.delete_index(indexname)
        except AlgoliaException as e:  # pragma: no cover
            if 'HTTP Code: 404' in str(e):
                pass

    def search(self, bucket_id, collection_id, **kwargs):
        indexname = self.indexname(bucket_id, collection_id)
        index = self.client.init_index(indexname)
        query = kwargs.pop("query", "")
        return index.search(query, args=kwargs)

    def flush(self):
        response = self.client.list_indexes()
        for index in response['items']:
            indexname = index['name']
            if indexname.startswith(self.prefix):
                index = self.client.init_index(indexname)
                index.clear_index()
                self.client.delete_index(indexname)

    @contextmanager
    def bulk(self):
        bulk = BulkClient(self)
        yield bulk

        for indexname, requests in bulk.operations.items():
            index = self.client.init_index(indexname)
            index.batch(requests)


class BulkClient:
    def __init__(self, indexer):
        self.indexer = indexer
        self.operations = {}

    def index_record(self, bucket_id, collection_id, record, id_field="id"):
        indexname = self.indexer.indexname(bucket_id, collection_id)
        self.operations.setdefault(indexname, [])
        self.operations[indexname].append({'action': 'addObject', 'body': record})

    def unindex_record(self, bucket_id, collection_id, record, id_field="id"):
        indexname = self.indexer.indexname(bucket_id, collection_id)
        record_id = record[id_field]
        self.operations.setdefault(indexname, {})
        self.operations[indexname].append({'action': 'deleteObject',
                                           'body': {'objectID': record_id}})


def heartbeat(request):
    """Test that Algolia is operationnal.

    :param request: current request object
    :type request: :class:`~pyramid:pyramid.request.Request`
    :returns: ``True`` is everything is ok, ``False`` otherwise.
    :rtype: bool
    """
    indexer = request.registry.indexer
    try:
        return indexer.client.is_alive()
    except Exception as e:
        logger.exception(e)
        return False


def load_from_config(config):
    settings = config.get_settings()
    application_id = settings.get('algolia.application_id')
    api_key = settings.get('algolia.api_key')
    if application_id is None or api_key is None:
        message = ('kinto-algolia needs kinto.algolia.application_id '
                   'and kinto.algolia.api_key settings to be set.')
        raise ConfigurationError(message)

    prefix = settings.get('algolia.index_prefix', 'kinto')
    indexer = Indexer(application_id=application_id, api_key=api_key, prefix=prefix)
    return indexer
