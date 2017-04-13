How to install?
===============

Step 1
------

```
$ mkdir tellecast
$ cd tellecast
$ git clone --recursive git@github.com:mahendrakalkura/tellecast.git .
$ cp settings.py.sample settings.py # edit as required
```

Step 2
------

```
$ cd tellecast
$ psql -d postgres -c 'CREATE DATABASE tellecast'
$ psql -d tellecast -c 'CREATE EXTENSION postgis'
$ psql -d tellecast -c 'CREATE EXTENSION postgis_topology'
$ psql -d tellecast -c 'CREATE EXTENSION fuzzystrmatch'
$ psql -d tellecast -c 'CREATE EXTENSION postgis_tiger_geocoder'
```

Step 3
------

```
$ cd tellecast
$ mkvirtualenv tellecast
$ pip install -r requirements.txt
$ python manage.py syncdb --noinput
$ python manage.py migrate --noinput
$ python manage.py collectstatic --noinput
```

How to run?
===========

```
$ cd tellecast
$ workon tellecast
$ celery worker --app=api.tasks --concurrency=1 --loglevel=DEBUG --pool=prefork --queues=api.tasks.email_notifications
$ celery worker --app=api.tasks --concurrency=1 --loglevel=DEBUG --pool=prefork --queues=api.tasks.push_notifications
$ celery worker --app=api.tasks --concurrency=1 --loglevel=DEBUG --pool=prefork --queues=api.tasks.thumbnails
$ python manage.py runserver
$ python manage.py users
$ python manage.py websockets
```
