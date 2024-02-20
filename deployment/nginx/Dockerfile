FROM nginx:alpine

ARG STATIC_DIR=./static/*

RUN rm /etc/nginx/conf.d/default.conf
COPY comicagg.conf /etc/nginx/conf.d

COPY --chown=nginx:nginx ${STATIC_DIR} /web/static
