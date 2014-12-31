How to install?
===============

Step 1
------

```
$ mkdir tellterms
$ cd tellterms
$ git clone --recursive git@bitbucket.org:mahendrakalkura/tellterms.git .
$ cp settings.py.sample settings.py # edit as required
```

Step 2
------

```
$ cd tellterms
$ psql -d postgres -c 'CREATE DATABASE tellterms'
$ psql -d tellterms -c 'CREATE EXTENSION postgis'
$ psql -d tellterms -c 'CREATE EXTENSION postgis_topology'
$ psql -d tellterms -c 'CREATE EXTENSION fuzzystrmatch'
$ psql -d tellterms -c 'CREATE EXTENSION postgis_tiger_geocoder'
```

Step 3
------

```
$ cd tellterms
$ mkvirtualenv tellterms
$ pip install -r requirements.txt
$ python manage.py syncdb
$ python manage.py migrate
```

How to run?
===========

```
$ cd tellterms
$ workon tellterms
$ python manage.py runserver 0.0.0.0:8000
```
