import json
import logging

from algoliasearch.helpers import AlgoliaException
from kinto.core import authorization
from kinto.core import Service
from kinto.core import utils
from kinto.core.errors import http_error, ERRORS, raise_invalid
from pyramid import httpexceptions


logger = logging.getLogger(__name__)


class RouteFactory(authorization.RouteFactory):
    def __init__(self, request):
        super().__init__(request)
        records_plural = utils.strip_uri_prefix(request.path.replace("/search", "/records"))
        self.permission_object_id = records_plural
        self.required_permission = "read"


search = Service(name="search",
                 path='/buckets/{bucket_id}/collections/{collection_id}/search',
                 description="Search",
                 factory=RouteFactory)


def search_view(request, **kwargs):
    bucket_id = request.matchdict['bucket_id']
    collection_id = request.matchdict['collection_id']

    # Limit the number of results to return, based on existing Kinto settings.
    paginate_by = request.registry.settings.get("paginate_by")
    max_fetch_size = request.registry.settings["storage_max_fetch_size"]
    if paginate_by is None or paginate_by <= 0:
        paginate_by = max_fetch_size
    configured = min(paginate_by, max_fetch_size)
    # If the size is specified in query, ignore it if larger than setting.
    specified = None
    if "size" in kwargs:
        specified = kwargs.get("hitsPerPage")

    if specified is None or specified > configured:
        kwargs.setdefault("hitsPerPage", configured)

    # Access indexer from views using registry.
    indexer = request.registry.indexer
    try:
        results = indexer.search(bucket_id, collection_id, **kwargs)
    except AlgoliaException as e:
        logger.exception("Index query failed.")
        if 'HTTP Code: 404' in str(e):
            # If plugin was enabled after the creation of the collection.
            indexer.create_index(bucket_id, collection_id)
            results = indexer.search(bucket_id, collection_id, **kwargs)
        else:
            response = http_error(httpexceptions.HTTPBadRequest(),
                                  errno=ERRORS.INVALID_PARAMETERS,
                                  message=str(e))
            raise response

    return results


@search.post(permission=authorization.DYNAMIC)
def post_search(request):
    try:
        body = json.loads(request.body.decode("utf-8"))
    except json.decoder.JSONDecodeError:
        error_details = {
            'name': 'JSONDecodeError',
            'description': 'Please make sure your request body is a valid JSON payload.',
        }
        raise_invalid(request, **error_details)

    return search_view(request, **body)


@search.get(permission=authorization.DYNAMIC)
def get_search(request):
    q = request.GET.get("query")
    return search_view(request, query=q)
