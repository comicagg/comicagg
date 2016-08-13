API Endpoints
=============

The following table illustrates the operations that can be done with each object.

+----------------+-----+------+-----+--------+
| Resource       | GET | POST | PUT | DELETE |
+================+=====+======+=====+========+
| Comics         |     |      |     |        |
+----------------+-----+------+-----+--------+
| Subscriptions  |     |      |     |        |
+----------------+-----+------+-----+--------+
| Unread comics  |     |      |     |        |
+----------------+-----+------+-----+--------+
| User           |     |      |     |        |
+----------------+-----+------+-----+--------+


API endpoints can only be accessed via *https* and the base url is
*https://www.comicagg.com/api*.
An access token is always needed to get a successful API response.

Structure
---------

API responses are wrapped in a JSON object that contains metadata about the
response itself.

.. code-block:: json

    {
        "meta": {
            "status": 200,
            "text": "OK"
        },
        "pagination" : {},
        "response" : {}
    }

Pagination
----------

.. code-block:: json

    {
        "pagination": {
            "next_max_id": 1234567,
            "next_url": "https://www.comicagg.com/api/comics?max_id=1234567"
        }
    }

Errors
------

.. code-block:: json

    {
        "error": {
            "error_type": "BadRequest",
            "error_message": "You are not subscribed to this comic"
        }
    }
