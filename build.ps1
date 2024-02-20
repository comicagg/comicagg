docker build . -t nublar.azurecr.io/comicagg/app:latest
docker tag nublar.azurecr.io/comicagg/app:latest nublar.azurecr.io/comicagg/app:stable
docker push nublar.azurecr.io/comicagg/app:latest
docker push nublar.azurecr.io/comicagg/app:stable


gh workflow run "Build Django image" --ref 39-cookie-consent-not-showing-correctly-on-dev
