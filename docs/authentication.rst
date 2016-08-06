Authenticating requests
=======================

The REST API uses OAuth2 for authentication.
Once the user has allowed your app to access the API,
you will get an ``access_token`` to authenticate every request
you do to the API.

To authenticate the requests, you must send the ``access_token``
in the ``Authorization`` HTTP header with the following format:

.. code-block:: http

   GET /api HTTP/1.0
   Authorization: bearer access_token

You will get a success response if the token is valid.
Otherwise, you will get a ``401`` response to indicate
that authentication has failed.

You may use the authentication cookie from the web to authenticate
API requests for the moment, but this behaviour will likely change
in the future and the API will only support OAuth access tokens.

API Permissions
---------------

Also called scopes.

- Read
- Write
