How to install?
===============

Step 1
------

```
$ mkdir tellecast
$ cd tellecast
$ git clone --recursive git@bitbucket.org:tellterms/tellecast.git .
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
$ celery worker --app=api.tasks --concurrency=1 --loglevel=DEBUG --pool=prefork
$ python manage.py runserver 0.0.0.0:8000
```
