Kinto Algolia
#############

.. image:: https://img.shields.io/travis/Kinto/kinto-algolia.svg
        :target: https://travis-ci.org/Kinto/kinto-algolia

.. image:: https://img.shields.io/pypi/v/kinto-algolia.svg
        :target: https://pypi.python.org/pypi/kinto-algolia

.. image:: https://coveralls.io/repos/Kinto/kinto-algolia/badge.svg?branch=master
        :target: https://coveralls.io/r/Kinto/kinto-algolia

**kinto-algolia** forwards the records to Algolia and provides a ``/search``
endpoint to query the indexed data.


Install
=======

::

    pip install kinto-algolia


Setup
=====

In the `Kinto <http://kinto.readthedocs.io/>`_ settings:

.. code-block :: ini

    kinto.includes = kinto_algolia
    kinto.algolia.application_id = YourApplicationID
    kinto.algolia.api_key = YourAPIKey

By default, indices names are prefixed with ``kinto-``. You change this with:

.. code-block :: ini

    kinto.algolia.index_prefix = myprefix


Usage
=====

Create a new record:

::

    $ echo '{"data":
        {"title": "kinto",
         "description": "A database for the web",
         "_geoloc": {"lng": -73.778925, "lat": 40.639751}}' | \
        http POST http://localhost:8888/v1/buckets/example/collections/notes/records \
            --auth token:alice-token


It should now be possible to search for it using the `Algolia API <https://www.elastic.co/guide/en/algolia/reference/current/index.html>`_.

For example, using a quick querystring search:

::

    $ http "http://localhost:8888/v1/buckets/example/collections/notes/search?query=kinto+database" \
        --auth token:alice-token


Or an advanced search using request body:

::

    $ echo '{"insideBoundingBox": "46.650828100116044,7.123046875,45.17210966999772,1.009765625"}' | \
        http POST http://localhost:8888/v1/buckets/example/collections/notes/search \
            --auth token:alice-token

.. code-block:: http

    HTTP/1.1 200 OK
    Access-Control-Expose-Headers: Retry-After, Content-Length, Alert, Backoff
    Content-Length: 333
    Content-Type: application/json; charset=UTF-8
    Date: Wed, 20 Jan 2016 12:02:05 GMT
    Server: waitress

    {
      "hits": [
        {
           "_geoloc": {
               "lat": 40.639751,
               "lng": -73.778925
           },
           "_highlightResult": {
               "title": {
                   "matchLevel": "none",
                   "matchedWords": [],
                   "value": "Kinto"
               }
           },
           "last_modified": 1523349594783,
           "title": "Kinto",
           "description": "A database for the web",
           "objectID": "1008855320"
        }
      ],
      "hitsPerPage": 1000,
      "nbHits": 1,
      "nbPages": 1,
      "page": 0,
      "params": "insideBoundingBox=42.124710287101955%2C9.335632324218752%2C41.47360232634395%2C14.403076171875002&hitsPerPage=10000&query=",
      "processingTimeMS": 2,
      "query": ""
    }


Custom index settings
---------------------

By default, Algolia infers the data types from the indexed records.

But it's possible to define the index mappings (ie. schema) from the collection metadata,
in the ``index:settings`` property:

.. code-block:: bash

    $ echo '{
      "attributesToIndex": ["title", "description"]
    }' | http PATCH "http://localhost:8888/v1/buckets/blog/collections/builds" \
        --auth token:admin-token --verbose

Refer to [Algolia official documentation](https://www.algolia.com/doc/api-reference/api-methods/get-settings/?language=python#response) for more information about settings.


Running the tests
=================

::

  $ make tests
