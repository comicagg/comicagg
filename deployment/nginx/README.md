# Building the proxy/frontend Nginx image

The Dockerfile expects a `static` folder in the root of the build context that
includes all the static files needed to be published by nginx.

The idea is to:

1. Run `collecstatic` Django command to build the static files directory.
2. Copy that directory to the build context of the Docker image.
3. Build the image

The build Github Action does this process to build the image.
