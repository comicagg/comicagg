# Build the app image
docker build . -t nublar.azurecr.io/comicagg/app:development

# Tag the image as stable and push both images to the registry
docker tag nublar.azurecr.io/comicagg/app:development nublar.azurecr.io/comicagg/app:stable
docker push nublar.azurecr.io/comicagg/app:development
docker push nublar.azurecr.io/comicagg/app:stable

# Run the GH action on a different branch
gh workflow run ci --ref 39-cookie-consent-not-showing-correctly-on-dev
