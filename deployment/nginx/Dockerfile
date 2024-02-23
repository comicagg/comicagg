FROM nginx:alpine

RUN rm /etc/nginx/conf.d/default.conf
COPY comicagg.conf /etc/nginx/conf.d

COPY --chown=nginx:nginx ./static /web/static
