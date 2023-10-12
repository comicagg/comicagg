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

Endpoints that return lists support pagination and the response object will
include a pagination object with information of the next page. You can use
``next_url`` to retrieve the next set of objects. The parameter
``next_max_id`` can be used to understand which would be the first object in the
next page.
A parameter ``count`` can also be used to specify the number of items
to be returned.

.. code-block:: json

    {
        "pagination": {
            "next_max_id": 1234567,
            "next_url": "https://www.comicagg.com/api/comics?max_id=1234567"
        }
    }

Errors
------

Errors are returned in the ``response`` object like if were the result of the
operation. ``status`` and ``text`` in the ``meta`` object of the response
and also the HTTP status of the response will also indicate that an error
occurred.

.. code-block:: json

    {
        "response": {
            "error_type": "BadRequest",
            "error_message": "You are not subscribed to this comic"
        }
    }


.. include:: endpoints-comics.rst
.. include:: endpoints-unreads.rst
.. include:: endpoints-subscriptions.rst
.. include:: endpoints-user.rst
