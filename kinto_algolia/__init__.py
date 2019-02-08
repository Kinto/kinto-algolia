import pkg_resources

from pyramid.settings import aslist
from kinto.events import ServerFlushed
from kinto.core.events import AfterResourceChanged

from . import indexer
from . import listener


#: Module version, as defined in PEP-0396.
__version__ = pkg_resources.get_distribution(__package__).version


def includeme(config):
    settings = config.get_settings()
    collections = settings.get("algolia.resources", [])
    # Register a global indexer object
    config.registry.indexer = indexer.load_from_config(config)

    # Register heartbeat to check algolia integration.
    config.registry.heartbeats["algolia"] = indexer.heartbeat

    # Activate end-points.
    config.scan("kinto_algolia.views")

    on_record_changed_listener = listener.on_record_changed

    # If StatsD is enabled, monitor execution time of listener.
    if config.registry.statsd:
        statsd_client = config.registry.statsd
        key = "plugins.algolia.index"
        on_record_changed_listener = statsd_client.timer(key)(
            on_record_changed_listener
        )

    config.add_subscriber(
        on_record_changed_listener, AfterResourceChanged, for_resources=("record",)
    )

    config.add_subscriber(listener.on_server_flushed, ServerFlushed)
    config.add_subscriber(
        listener.on_collection_created,
        AfterResourceChanged,
        for_resources=("collection",),
        for_actions=("create",),
    )
    config.add_subscriber(
        listener.on_collection_updated,
        AfterResourceChanged,
        for_resources=("collection",),
        for_actions=("update",),
    )
    config.add_subscriber(
        listener.on_collection_deleted,
        AfterResourceChanged,
        for_resources=("collection",),
        for_actions=("delete",),
    )
    config.add_subscriber(
        listener.on_bucket_deleted,
        AfterResourceChanged,
        for_resources=("bucket",),
        for_actions=("delete",),
    )

    config.add_api_capability(
        "algolia",
        description="Index and search records using Algolia.",
        url="https://github.com/Kinto/kinto-algolia",
        version=__version__,
        collections=aslist(collections),
    )
