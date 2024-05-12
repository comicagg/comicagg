$tag = "development"
# Build the python image
docker build . -f python.Dockerfile -t nublar.azurecr.io/comicagg/python:$tag
# Build the app image
docker build . -t nublar.azurecr.io/comicagg/app:$tag

# Tag the image as stable and push both images to the registry
docker tag nublar.azurecr.io/comicagg/app:development nublar.azurecr.io/comicagg/app:stable
docker push nublar.azurecr.io/comicagg/app:development
docker push nublar.azurecr.io/comicagg/app:stable

# Run the GH action on a different branch
gh workflow run ci --ref 39-cookie-consent-not-showing-correctly-on-dev
