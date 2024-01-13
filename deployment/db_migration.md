# Database migration from v1

## 1. Get a database backup

```shell
# Get the backup
sudo -u postgres pg_dump comicagg | gzip > comicagg-20240107.sql.gz
```

## 2. Migrate the database

1. Create a new schema called "old" in the new database:

   ```SQL
   CREATE SCHEMA old AUTHORIZATION comicagg;
   ```

2. Update the contents of the backup:

   ```shell
   sed -i -e 's/SET search_path = public, pg_catalog;/SET search_path = old, pg_catalog;/' comicagg-20240107.sql
   sed -i -e 's/TABLE public./TABLE old./g' comicagg-20240107.sql
   ```

3. Upload the backup to the new database:

   ```shell
   # Upload the backup to the database
   docker exec -i db psql -U comicagg -d comicagg < comicagg-20240107.sql
   ```

4. Run the following SQL to dump data from the old schema to the public schema:

   ```SQL
   -- accounts_userprofile -> accounts_userprofile

   INSERT INTO public.accounts_userprofile
      (id, last_read_access, user_id)
   SELECT id, last_read_access, user_id
      FROM old.accounts_userprofile;

   SELECT pg_catalog.setval('public.accounts_userprofile_id_seq', (select 1 + max(id) from public.accounts_userprofile), true);

   -- auth_user -> auth_user

   INSERT INTO public.auth_user
      (id, username, email, first_name, last_name, password, is_staff, is_active, is_superuser, last_login, date_joined)
   SELECT
      id, username, email, first_name, last_name, password, is_staff, is_active, is_superuser, last_login, date_joined
   FROM old.auth_user;

   SELECT pg_catalog.setval('public.auth_user_id_seq', (select 1 + max(id) from public.auth_user), true);

   -- blog_newblog -> blog_newblog

   INSERT INTO public.blog_newblog
      (id, user_id, post_id)
   SELECT id, user_id, post_id
      FROM old.blog_newblog;

   SELECT pg_catalog.setval('public.blog_newblog_id_seq', (select 1 + max(id) from public.blog_newblog), true);

   -- blog_post -> blog_post

   INSERT INTO public.blog_post
      (id, title, text, date, html, user_id)
   SELECT id, title, text, date, html, user_id
      FROM old.blog_post;

   SELECT pg_catalog.setval('public.blog_post_id_seq', (select 1 + max(id) from public.blog_post), true);

   -- aggregator_comic -> comics_comic

   INSERT INTO public.comics_comic
      (id, name, website, active, notify, ended, no_images, custom_func,
      re1_url, re1_base, re1_re, re1_backwards,
      re2_url, re2_base, re2_re, re2_backwards,
      referrer,
      last_update, last_image, last_image_alt_text,
      positive_votes, total_votes, add_date)
   SELECT id, name, website, activo, notify, ended, noimages, custom_func,
      url, base_img, regexp, backwards,
      url2, base2, regexp2, backwards2,
      referer,
      last_check, last_image, last_image_alt_text,
      rating, votes, add_date
      FROM old.agregator_comic;

   SELECT pg_catalog.setval('public.comics_comic_id_seq', (select 1 + max(id) from public.comics_comic), true);

   -- aggregator_comichistory -> comics_comichistory

   INSERT INTO public.comics_comichistory
      (id, date, url, alt_text, comic_id)
   SELECT id, date, url, alt_text, comic_id
      FROM old.agregator_comichistory;

   SELECT pg_catalog.setval('public.comics_comichistory_id_seq', (select 1 + max(id) from public.comics_comichistory), true);

   -- aggregator_newcomic -> comics_newcomic

   INSERT INTO public.comics_newcomic
      (id, comic_id, user_id)
   SELECT id, comic_id, user_id
      FROM old.agregator_newcomic;

   SELECT pg_catalog.setval('public.comics_newcomic_id_seq', (select 1 + max(id) from public.comics_newcomic), true);

   -- aggregator_request -> comics_request

   INSERT INTO public.comics_request
      (id, url, comment, admin_comment, done, rejected, user_id)
   SELECT id, url, comment, admin_comment, done, rejected, user_id
      FROM old.agregator_request;

   SELECT pg_catalog.setval('public.comics_request_id_seq', (select 1 + max(id) from public.comics_request), true);

   -- aggregator_subscription -> comics_subscription

   INSERT INTO public.comics_subscription
      (id, "position", comic_id, user_id)
   SELECT id, "position", comic_id, user_id
      FROM old.agregator_subscription;

   SELECT pg_catalog.setval('public.comics_subscription_id_seq', (select 1 + max(id) from public.comics_subscription), true);

   -- aggregator_tag -> comics_tag

   INSERT INTO public.comics_tag
      (id, name, comic_id, user_id)
   SELECT id, name, comic_id, user_id
      FROM old.agregator_tag;

   SELECT pg_catalog.setval('public.comics_tag_id_seq', (select 1 + max(id) from public.comics_tag), true);

   -- aggregator_unreadcomic -> comics_unreadcomic

   INSERT INTO public.comics_unreadcomic
      (id, comic_id, history_id, user_id)
   SELECT id, comic_id, history_id, user_id
      FROM old.agregator_unreadcomic;

   SELECT pg_catalog.setval('public.comics_unreadcomic_id_seq', (select 1 + max(id) from public.comics_unreadcomic), true);
   ```
