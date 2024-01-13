# Deployment checklist

## From scratch

These are the tasks needed to get an environment up and running:

1. Start the database container:

   ```shell
   docker compose up -d db pgadmin
   ```

2. Prepare the database:

   ```shell
   docker compose create app
   docker compose exec app python manage.py migrate
   ```

3. Start the proxy container and collect the static files:

   ```shell
   docker compose up -d proxy
   docker compose exec app python manage.py collectstatic --no-input --clear
   ```

4. Start the rest of the containers:

   ```shell
   docker compose up -d
   ```

5. Create tasks:

   ```shell
   docker compose exec app python manage.py ensure_tasks
   ```

6. Add default list of comics

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

3. Start the proxy container and collect the static files:

   ```shell
   docker compose up -d proxy
   docker compose exec app python manage.py collectstatic --no-input --clear
   ```

4. Start the rest of the containers:

   ```shell
   docker compose up -d
   ```

5. Create tasks:

   ```shell
   docker compose exec app python manage.py ensure_tasks
   ```
