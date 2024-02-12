FROM python:3.10-bookworm

RUN apt-get update && \
    apt-get install -y git gettext libmariadb-dev libpq-dev locales libmemcached-dev build-essential \
            supervisor \
            sudo \
            locales \
            --no-install-recommends && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/* && \
    dpkg-reconfigure locales && \
    locale-gen C.UTF-8 && \
    /usr/sbin/update-locale LANG=C.UTF-8 && \
    mkdir /etc/eventyay && \
    mkdir /data && \
    mkdir /public && \
    groupadd -g 999 eventyayuser && \
    useradd -r -u 999 -g eventyayuser -d /eventyay -ms /bin/bash eventyayuser && \
    echo 'eventyayuser ALL=(ALL) NOPASSWD: /usr/bin/supervisord' >> /etc/sudoers

ENV LC_ALL=C.UTF-8


COPY pyproject.toml /eventyay
COPY src /eventyay/src
COPY deployment/docker/eventyay.bash /usr/local/bin/eventyay
COPY deployment/docker/supervisord.conf /etc/supervisord.conf

RUN pip3 install -U pip setuptools wheel typing && \
    pip3 install -e /eventyay/[mysql,postgres,redis] && \
    pip3 install pylibmc && \
    pip3 install gunicorn


RUN python3 -m eventyay makemigrations
RUN python3 -m eventyay migrate

RUN apt-get update && \
    apt-get install -y nodejs npm && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/* && \
    python3 -m eventyay rebuild

RUN chmod +x /usr/local/bin/eventyay && \
    cd /eventyay/src && \
    rm -f eventyay.cfg && \
    chown -R eventyayuser:eventyayuser /eventyay /data /public && \
    rm -f /eventyay/src/data/.secret

USER eventyayuser
VOLUME ["/etc/eventyay", "/data", "/public"]
EXPOSE 80
ENTRYPOINT ["eventyay"]
CMD ["all"]
