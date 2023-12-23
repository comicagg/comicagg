# API

## Internals

Endpoint -> API View -> Comics models

If the endpoint needs to receive a body, then the view will use a Form so it can do a proper validation of the input. This is why APIView uses FormMixin.

The API speaks JSON.

The API authentication should use:

- Same authentication of the web, ie. the current user's session in case it's used in the frontend.
- OAuth2 in case we would like to integrate externally
