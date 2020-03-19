FROM python:3.7-alpine

RUN apk add --no-cache \
        g++ \
        git \
        libxslt-dev \
        mariadb-dev \
        jpeg-dev \
        zlib-dev

COPY requirements.txt /requirements.txt
RUN pip --no-cache-dir install -r /requirements.txt \
 && rm /requirements.txt

COPY . /app/.
WORKDIR /app
RUN rm -f .env \
 && rm -rf collected_static \
 && rm -rf media \
 && python manage.py collectstatic

CMD gunicorn factotum.wsgi -c factotum/gunicorn.py

EXPOSE 8000 8001
VOLUME /app/collected_static
VOLUME /app/media
