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
that authentication has failed. Along with the 401 response,
you will get a more descriptive error message that indicates the
cause of the error.

For the moment, you may use the authentication cookie from the web
to authenticate API requests, but this behaviour will likely change
in the future and the API will only support OAuth access tokens.

API Permissions
---------------

AKA the scope of the access token. When you are requesting the user
to authenticate and allow your app access to the API, you will need
to ask which permissions your app requires.

The API has the following scopes:

+----------+-------+---------------------------+
| Section  | Scope | Description               |
+==========+=======+===========================+
| Identity | Read  | Read the user's details   |
+          +-------+---------------------------+
|          | Write | Modify the user's details |
+----------+-------+---------------------------+
| Comics   | Read  | Read-only access to comics|
|          |       | , subscriptions, etc      |
+          +-------+---------------------------+
|          | Write | The above + modification  |
|          |       | of objects.               |
+----------+-------+---------------------------+

In an application that wants to log the user in and serve as comic reader,
the scopes that make most sense are Identity:Read and Comics:Write as this
will allow the application have acess to the user's name and be able to
mark the unread comics as read, etc.
