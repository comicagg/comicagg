.. toctree::
   :maxdepth: 2

Doing requests
==============

When doing a request and if a body is needed, for example in a POST request,
the request must include a ``Content-Type: application/x-www-form-urlencoded``
header and the body must be send url encoded.
In case that the request does not need to send a body,
you should use a header ``Content-Length: 0``.

When a response includes a body, it will be JSON-formatted
and the content type in the headers will be ``application/json``.

Return codes
------------

This is a table that represents the expected return codes for general requests.
Detailed return codes and error codes will be provided in each operation:

+-----------+--------+-----------------------------+---------------------------+
| HTTP Verb | CRUD   | Entire collection           | Specific item             |
|           |        | (eg. /comics)               | (eg. /comics/id)          |
+===========+========+=============================+===========================+
| POST      | Create | | 201 (Created)             | | 201 (Created)           |
|           |        | | 400 (Bad Request)         | | 400 (Bad Request)       |
+-----------+--------+-----------------------------+---------------------------+
| GET       | Read   | 200 (OK)                    | 200 (OK)                  |
+-----------+--------+-----------------------------+---------------------------+
| PUT       | Update | | 204 (No Content)          | | 204 (No Content)        |
|           |        | | 400 (Bad Request)         | | 400 (Bad Request)       |
+-----------+--------+-----------------------------+---------------------------+
| DELETE    | Delete | | 200 (OK)                  | | 200 (OK)                |
|           |        | | 204 (No Content)          | | 204 (No Content)        |
|           |        | | 400 (Bad Request)         | | 400 (Bad Request)       |
+-----------+--------+-----------------------------+---------------------------+
