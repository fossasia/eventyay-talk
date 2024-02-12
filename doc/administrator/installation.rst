.. _installation:

Installation
============

This guide will help you to install eventyay on Linux. This setup is suitable
to support events in usual sizes, but the guide does not go into performance
tuning or customisation options beyond the standard settings.

.. warning:: While we try to make it straightforward to run eventyay, it still
             requires some Linux experience to get it right, particularly to
             make sure that standard security practices are followed. If
             you're not feeling comfortable managing a Linux server, check
             out our hosting and service offers at `eventyay.com`_.

For the more automation-savvy, we also provide an `Ansible role`_ that follows
this guide. If you prefer a docker setup, there is a `docker-compose setup`_.
Please note that the docker setup is community provided and not officially
supported.

Step 0: Prerequisites
---------------------

Please set up the following systems beforehand. We can't go into their use
and configuration here, but please have a look at the linked pages.

* **Python 3.9 or newer** and a ``pip`` to match. You can use ``python -V`` and
  ``pip3 -V`` to check.
* An SMTP server to send out mails
* An HTTP reverse proxy, e.g. `nginx`_ or Apache to allow HTTPS connections
* A database server: `MySQL`_ 8+ or MariaDB 10.4+ or `PostgreSQL`_ 12+.
  You can use SQLite, but we strongly recommend not to run SQLite in
  production. Given the choice, we'd recommend to use PostgreSQL.
* A `redis`_ server, if you want to use eventyay with an asynchronous task
  runner or improved caching.
* If you are installing eventyay from source rather than from a pre-built
  wheel on PyPI, you will also need `nodejs`_.

We assume that you also have the usual security measures in place, such as a
firewall. If you're new to Linux and firewalls, we recommend that you start
with `ufw`_.

Please ensure that the environment used to run eventyay is configured to work
with non-ASCII file names. You can check this by running::

    python -c "import sys; print(sys.getfilesystemencoding())"

This should output ``"utf-8"``.

.. note:: Please do not run eventyay without HTTPS encryption. You'll handle user data and thanks
          to `Let's Encrypt`_, SSL certificates are free these days. We also *do not* provide
          support for HTTP-exclusive installations except for evaluation purposes.

Step 1: Unix user
-----------------

.. hint:: All code lines prepended with a ``#`` symbol are commands that you
          need to execute on your server as ``root`` user (e.g. using
          ``sudo``); you should run all lines prepended with a ``$`` symbol as
          the unprivileged user.

As we do not want to run eventyay as root, we first create a new unprivileged user::

    # adduser eventyay --disabled-password --home /var/eventyay


Step 2: Database setup
----------------------

Having the database server installed, we still need a database and a database
user. We recommend using PostgreSQL. eventyay also works (and runs tests
against) MariaDB and SQLite. If you do not use PostgreSQL, please refer to the
appropriate documentation on how to set up a database. For PostgreSQL, run
these commands::

  # sudo -u postgres createuser eventyay -P
  # sudo -u postgres createdb -O eventyay eventyay

Make sure that your database encoding is UTF-8. You can check with this command::

  # sudo -u postgres psql -c 'SHOW SERVER_ENCODING'

When using MySQL, make sure you set the character set of the database to ``utf8mb4``, e.g. like this::

    mysql > CREATE DATABASE eventyay DEFAULT CHARACTER SET utf8mb4 DEFAULT COLLATE utf8mb4_unicode_ci



Step 3: Package dependencies
----------------------------

Besides the packages above, you might need local system packages to build and
run eventyay. We cannot maintain an up-to-date dependency list for all Linux
flavours, but we can offer you a list for Ubuntu. You should be able to find
the appropriate packages on your system from there:

On Ubuntu-like systems, you will need packages like:

- ``build-essential``
- ``libssl-dev``
- ``python3-dev``
- ``gettext``
- ``libmysqlclient-dev`` if you use MariaDB

eventyay requires Python 3.6+. If you cannot find one of these versions for your
system, you can build it from source.

.. note:: You may need to replace all following mentions of ``pip`` with ``pip3``.


Step 4: Configuration
---------------------

Now we'll create a configuration directory and configuration file for eventyay::

    # mkdir /etc/eventyay
    # touch /etc/eventyay/eventyay.cfg
    # chown -R eventyay:eventyay /etc/eventyay/
    # chmod 0600 /etc/eventyay/eventyay.cfg

Fill the configuration file ``/etc/eventyay/eventyay.cfg`` with the following
content. But don't forget to adjust it to your environment!

.. literalinclude:: ../../src/eventyay.example.cfg
   :language: ini

Check out :ref:`configure` for details on the available configuration options.
There are more options available than we're showing you here!

Step 5: Installation
--------------------

Please execute the following steps as the ``eventyay`` user. This isolates the
eventyay environment from your global Python versions and binaries::

    $ pip install --user -U pip setuptools wheel gunicorn

eventyay works with your choice of database backends – we recommend using
PostgreSQL, but MySQL and SQLite work as well. Use this command to install the
database driver (unless you use SQLite, which has its driver built in):

+-----------------+-------------------------------------------+
| Database        | pip package                               |
+=================+===========================================+
| PostgreSQL      | ``pip install --user -U psycopg2-binary`` |
+-----------------+-------------------------------------------+
| MySQL / MariaDB | ``pip install --user -U mysqlclient``     |
+-----------------+-------------------------------------------+

Now we will install eventyay itself:

+-----------------+------------------------------------------------------------------------+
| Database        | Command                                                                |
+=================+========================================================================+
| SQLite          | ``pip install --user --upgrade-strategy eager -U eventyay``             |
+-----------------+------------------------------------------------------------------------+
| PostgreSQL      | ``pip install --user --upgrade-strategy eager -U "eventyay[postgres]"`` |
+-----------------+------------------------------------------------------------------------+
| MySQL / MariaDB | ``pip install --user --upgrade-strategy eager -U "eventyay[mysql]"``    |
+-----------------+------------------------------------------------------------------------+

If you intend to run eventyay with asynchronous task runners or with redis as
cache server, you can add ``[redis]`` to the installation command, which will
pull in the appropriate dependencies. Please note that you should also use
``eventyay[redis]`` when you upgrade eventyay in this case.

We also need to create a data directory::

    $ mkdir -p /var/eventyay/data/media

We compile static files and translation data and create the database structure::

    $ python -m eventyay migrate
    $ python -m eventyay rebuild

Now, create a user with administrator rights, an organiser and a team by running::

    $ python -m eventyay init

Step 6: Starting eventyay as a service
-------------------------------------

We recommend starting eventyay using systemd to make sure it starts up after a reboot. Create a file
named ``/etc/systemd/system/eventyay-web.service`` with the following content::

    [Unit]
    Description=eventyay web service
    After=network.target

    [Service]
    User=eventyay
    Group=eventyay
    WorkingDirectory=/var/eventyay/.local/lib/python3.8/site-packages/eventyay
    ExecStart=/var/eventyay/.local/bin/gunicorn eventyay.wsgi \
                          --name eventyay --workers 4 \
                          --max-requests 1200  --max-requests-jitter 50 \
                          --log-level=info --bind=127.0.0.1:8345
    Restart=on-failure

    [Install]
    WantedBy=multi-user.target

If you decide to use Celery (giving you asynchronous execution for long-running
tasks), you'll also need a second service
``/etc/systemd/system/eventyay-worker.service`` with the following content::

    [Unit]
    Description=eventyay background worker
    After=network.target

    [Service]
    User=eventyay
    Group=eventyay
    WorkingDirectory=/var/eventyay/.local/lib/python3.8/site-packages/eventyay
    ExecStart=/var/eventyay/.local/bin/celery -A eventyay.celery_app worker -l info
    WorkingDirectory=/var/eventyay
    Restart=on-failure

    [Install]
    WantedBy=multi-user.target

You can now run the following commands to enable and start the services::

    # systemctl daemon-reload
    # systemctl enable eventyay-web eventyay-worker
    # systemctl start eventyay-web eventyay-worker

Step 7: SSL
-----------

The following snippet is an example on how to configure an nginx proxy for eventyay::

    server {
        listen 80 default_server;
        listen [::]:80 ipv6only=on default_server;
        server_name eventyay.mydomain.com;
    }
    server {
        listen 443 default_server;
        listen [::]:443 ipv6only=on default_server;
        server_name eventyay.mydomain.com;

        ssl on;
        ssl_certificate /path/to/cert.chain.pem;
        ssl_certificate_key /path/to/key.pem;

        gzip off;
        add_header Referrer-Policy same-origin;
        add_header X-Content-Type-Options nosniff;

        location / {
            proxy_pass http://localhost:8345/;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto https;
            proxy_set_header Host $http_host;
        }

        location /media/ {
            gzip on;
            alias /var/eventyay/data/media/;
            add_header Content-Disposition 'attachment; filename="$1"';
            expires 7d;
            access_log off;
        }

        location /static/ {
            gzip on;
            alias /path/to/static.dist/;
            access_log off;
            expires 365d;
            add_header Cache-Control "public";
        }
    }

We recommend reading about setting `strong encryption settings`_ for your web server.

Step 8: Check the installation
-------------------------------

You can make sure the web interface is up and look for any issues with::

    # journalctl -u eventyay-web

If you use Celery, you can do the same for the worker processes (for example in
case the emails are not sent)::

    # journalctl -u eventyay-worker

If you're looking for errors, check the eventyay log. You can find the logging
directory in the start-up output.

Once eventyay is up and running, you can also find up to date administrator information
at https://eventyay.yourdomain.com/orga/admin/.

Step 9: Provide periodic tasks
------------------------------

There are a couple of things in eventyay that should be run periodically. It
doesn't matter how you run them, so you can go with your choice of periodic
tasks, be they systemd timers, cron, or something else entirely.

In the same environment as you ran the previous eventyay commands (e.g. the
``eventyay`` user), you should run

- ``python -m eventyay runperiodic`` somewhere every five minutes and once per hour.
- ``python -m eventyay clearsessions`` about once a month.

You could for example configure the ``eventyay`` user cron like this::

  15,45 * * * * python -m eventyay runperiodic

Next Steps
----------

You made it! You should now be able to reach eventyay at https://eventyay.yourdomain.com/orga/
Log in as the administrator you configured above, and create your first event!

Check out :ref:`configure` for details on the available configuration options.

If you want to read about updates, backups, and monitoring, head over to our
:ref:`maintenance` documentation!

.. _Ansible role: https://github.com/eventyay/ansible-eventyay
.. _nginx: https://botleg.com/stories/https-with-lets-encrypt-and-nginx/
.. _Let's Encrypt: https://letsencrypt.org/
.. _MySQL: https://dev.mysql.com/doc/refman/5.7/en/linux-installation-apt-repo.html
.. _PostgreSQL: https://www.postgresql.org/docs/
.. _redis: https://redis.io/documentation
.. _ufw: https://en.wikipedia.org/wiki/Uncomplicated_Firewall
.. _strong encryption settings: https://mozilla.github.io/server-side-tls/ssl-config-generator/
.. _docker-compose setup: https://github.com/eventyay/eventyay-docker
.. _eventyay.com: https://eventyay.com
.. _nodejs: https://github.com/nodesource/distributions/blob/master/README.md
