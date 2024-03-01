# Deployment

## Compose files

### compose.yml

Default compose file with service depencencies, etc. Does not map ports or loads environment files but are commented out so it's easier to remember they are needed. These, and possibly the image tag, are meant to be overriden.

### compose.dev.yml

Demonstrates how to use the compose file with overrides for a named environment.

It uses the override file `compose.override.dev.yml` to set another image, .env files and ports.

This file is meant to be used with `docker compose`. Maybe like this:

```shell
docker compose -f compose.dev.yml up -d --pull always
```

The file also includes an `IMAGE_TAG` variable to be able to specify another tag. If not specified, it will default to `development`. This is useful to test a PR image.

```PowerShell
$env:IMAGE_TAG="44-missing-static-files"; docker compose -f compose.dev.yml up -d --pull always
```

## env files

### example.env

This file includes all the possible environment variables that the app supports and the minimum required for the other components.

### {app,db,pgadmin}.env

`compose.override.dev.yml` uses separated env files for each container.

## Deploy from scratch

These are the tasks needed to get an environment up and running:

1. Start the database container:

   ```shell
   docker compose up -d db pgadmin
   ```

2. Prepare the database:

   ```shell
   docker compose up -d app
   docker compose exec app python manage.py migrate
   ```

3. Start the rest of the containers:

   ```shell
   docker compose up -d
   ```

4. Create tasks:

   ```shell
   docker compose exec app python manage.py ensure_tasks
   ```

5. Add default list of comics

   ```shell
   docker compose exec app python manage.py loaddata comics.Comic.json
   ```

## From a running database (pre Django 4.2)

These are the tasks needed to get an environment running and migrate the current data:

1. Start the database container:

   ```shell
   docker compose up -d db pgadmin
   ```

2. Prepare the database:

   ```shell
   docker compose create app
   docker compose exec app python manage.py migrate contenttypes
   docker compose exec app python manage.py migrate auth
   docker compose exec app python manage.py migrate accounts
   docker compose exec app python manage.py migrate admin
   docker compose exec app python manage.py migrate blog
   docker compose exec app python manage.py migrate comics 0008_comic_rename_referer
   docker compose exec app python manage.py migrate django_celery_beat
   docker compose exec app python manage.py migrate django_celery_results
   docker compose exec app python manage.py migrate mailer
   docker compose exec app python manage.py migrate sessions
   ```

   At this point, [migrate old data](/deployment/db_migration.md) into the database. And then apply the rest of migrations:

   ```shell
   docker compose exec app python manage.py migrate comics
   ```

3. Start the rest of the containers:

   ```shell
   docker compose up -d
   ```

4. Create tasks:

   ```shell
   docker compose exec app python manage.py ensure_tasks
   ```

## Generate a random secret key

```shell
docker compose exec app python -c "import secrets; allowed_chars = [chr(i) for i in range(0x21, 0x7F)]; key_length = 60; key = ''.join(secrets.choice(allowed_chars) for i in range(key_length)); print(key)"
```
