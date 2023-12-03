# Fixtures

Files created with Django's dumpdata:

```shell
python manage.py dumpdata --format json -o comics.Comic.json comics.Comic
```

They can be imported with load data:

```shell
python manage.py loaddata comics.Comic.json
```
