import json
import logging

from algoliasearch.exceptions import AlgoliaException
from kinto.core import authorization
from kinto.core import Service
from kinto.core import utils
from kinto.core.errors import raise_invalid


logger = logging.getLogger(__name__)


class RouteFactory(authorization.RouteFactory):
    def __init__(self, request):
        super().__init__(request)
        records_plural = utils.strip_uri_prefix(
            request.path.replace("/search", "/records")
        )
        self.permission_object_id = records_plural
        self.required_permission = "read"


search = Service(
    name="search",
    path="/buckets/{bucket_id}/collections/{collection_id}/search",
    description="Search",
    factory=RouteFactory,
)


def search_view(request, **kwargs):
    bucket_id = request.matchdict["bucket_id"]
    collection_id = request.matchdict["collection_id"]

    # algoliasearch doesn't support pagination
    # https://github.com/algolia/algoliasearch-client-python/issues/365
    #
    # Limit the number of results to return, based on existing Kinto settings.
    # paginate_by = request.registry.settings.get("paginate_by")
    # max_fetch_size = request.registry.settings["storage_max_fetch_size"]
    # if paginate_by is None or paginate_by <= 0:
    #     paginate_by = max_fetch_size
    # configured = min(paginate_by, max_fetch_size)
    # # If the size is specified in query, ignore it if larger than setting.
    # specified = None
    # if "size" in kwargs:
    #     specified = kwargs.get("hitsPerPage")
    #
    # if specified is None or specified > configured:
    #     kwargs.setdefault("hitsPerPage", configured)

    # Access indexer from views using registry.
    indexer = request.registry.indexer
    try:
        indexer.set_extra_headers(
            {"Referer": request.headers.get("Referer", request.route_url("hello"))}
        )
        results = indexer.search(bucket_id, collection_id, **kwargs)
    except AlgoliaException as e:
        logger.exception("Index query failed.")
        message = str(e)
        if "does not exist" in message:
            # If plugin was enabled after the creation of the collection.
            indexer.create_index(bucket_id, collection_id, wait_for_creation=True)
            return search_view(request, **kwargs)
        else:
            error_details = {"name": "Algolia error", "description": message}
            return raise_invalid(request, **error_details)

    return results


@search.post(permission=authorization.DYNAMIC)
def post_search(request):
    try:
        body = json.loads(request.body.decode("utf-8"))
    except json.decoder.JSONDecodeError:
        if not request.body:
            body = {}
        else:
            error_details = {
                "name": "JSONDecodeError",
                "description": "Please make sure your request body is a valid JSON payload.",
            }
            raise_invalid(request, **error_details)

    return search_view(request, **body)


@search.get(permission=authorization.DYNAMIC)
def get_search(request):
    kwargs = dict(**request.GET)
    return search_view(request, **kwargs)
