FROM nginx:alpine

ARG STATIC_DIR=./static

RUN rm /etc/nginx/conf.d/default.conf
COPY comicagg.conf /etc/nginx/conf.d

COPY ${STATIC_DIR} /web/static
