# comicagg
This is the Django code for the website at comicagg.com

Currently it supports Py3 and Django 4.2.

## Building

```shell
docker build . -t comicagg:latest
```

## Initializing

```shell
docker compose exec app python manage.py migrate
docker compose exec app python manage.py collectstatic
```
