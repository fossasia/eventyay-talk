import configparser
import os
import sys
from pathlib import Path

from eventyay.common.settings.utils import reduce_dict

CONFIG = {
    "filesystem": {
        "base": {
            "default": Path(__file__).parent.parent.parent.parent,
        },
        "logs": {
            "default": None,
            "env": os.getenv("EVENTYAY_FILESYSTEM_LOGS"),
        },
        "media": {
            "default": None,
            "env": os.getenv("EVENTYAY_FILESYSTEM_MEDIA"),
        },
        "static": {
            "default": None,
            "env": os.getenv("EVENTYAY_FILESYSTEM_STATIC"),
        },
    },
    "site": {
        "debug": {
            "default": "runserver" in sys.argv or "devserver" in sys.argv,
            "env": os.getenv("EVENTYAY_DEBUG"),
        },
        "url": {
            "default": "http://localhost",
            "env": os.getenv("EVENTYAY_SITE_URL"),
        },
        "https": {
            "env": os.getenv("EVENTYAY_HTTPS"),
        },
        "cookie_domain": {
            "default": "",
            "env": os.getenv("EVENTYAY_COOKIE_DOMAIN"),
        },
        "core_modules": {
            "default": "",
            "env": os.getenv("EVENTYAY_CORE_MODULES"),
        },
        "media": {"default": "/media/", "env": os.getenv("EVENTYAY_SITE_MEDIA")},
        "static": {"default": "/static/", "env": os.getenv("EVENTYAY_SITE_STATIC")},
        "csp": {"default": "", "env": os.getenv("EVENTYAY_SITE_CSP")},
        "csp_script": {"default": "", "env": os.getenv("EVENTYAY_SITE_CSP_SCRIPT")},
        "csp_style": {"default": "", "env": os.getenv("EVENTYAY_SITE_CSP_STYLE")},
        "csp_img": {"default": "", "env": os.getenv("EVENTYAY_SITE_CSP_IMG")},
        "csp_form": {"default": "", "env": os.getenv("EVENTYAY_SITE_CSP_FORM")},
    },
    "database": {
        "backend": {
            "default": "sqlite3",
            "env": os.getenv("EVENTYAY_DB_TYPE"),
        },
        "name": {
            "env": os.getenv("EVENTYAY_DB_NAME"),
        },
        "user": {
            "default": "",
            "env": os.getenv("EVENTYAY_DB_USER"),
        },
        "password": {
            "default": "",
            "env": os.getenv("EVENTYAY_DB_PASS"),
        },
        "host": {
            "default": "",
            "env": os.getenv("EVENTYAY_DB_HOST"),
        },
        "port": {
            "default": "",
            "env": os.getenv("EVENTYAY_DB_PORT"),
        },
    },
    "mail": {
        "from": {
            "default": "admin@localhost",
            "env": os.getenv("EVENTYAY_MAIL_FROM"),
        },
        "host": {
            "default": "localhost",
            "env": os.getenv("EVENTYAY_MAIL_HOST"),
        },
        "port": {
            "default": "25",
            "env": os.getenv("EVENTYAY_MAIL_PORT"),
        },
        "user": {
            "default": "",
            "env": os.getenv("EVENTYAY_MAIL_USER"),
        },
        "password": {
            "default": "",
            "env": os.getenv("EVENTYAY_MAIL_PASSWORD"),
        },
        "tls": {
            "default": "False",
            "env": os.getenv("EVENTYAY_MAIL_TLS"),
        },
        "ssl": {
            "default": "False",
            "env": os.getenv("EVENTYAY_MAIL_SSL"),
        },
    },
    "redis": {
        "location": {
            "default": "False",
            "env": os.getenv("EVENTYAY_REDIS"),
        },
        "session": {
            "default": "False",
            "env": os.getenv("EVENTYAY_REDIS_SESSIONS"),
        },
    },
    "celery": {
        "broker": {
            "default": "",
            "env": os.getenv("EVENTYAY_CELERY_BROKER"),
        },
        "backend": {
            "default": "",
            "env": os.getenv("EVENTYAY_CELERY_BACKEND"),
        },
    },
    "logging": {
        "email": {
            "default": "",
            "env": os.getenv("EVENTYAY_LOGGING_EMAIL"),
        },
        "email_level": {
            "default": "",
            "env": os.getenv("EVENTYAY_LOGGING_EMAIL_LEVEL"),
        },
    },
    "locale": {
        "language_code": {
            "default": "en",
            "env": os.getenv("EVENTYAY_LANGUAGE_CODE"),
        },
        "time_zone": {
            "default": "UTC",
            "env": os.getenv("EVENTYAY_TIME_ZONE"),
        },
    },
}


def read_config_files(config):
    if "EVENTYAY_CONFIG_FILE" in os.environ:
        config_files = config.read_file(
            open(os.environ.get("EVENTYAY_CONFIG_FILE"), encoding="utf-8")
        )
    else:
        config_files = config.read(
            [
                "/etc/eventyay/eventyay.cfg",
                Path.home() / ".eventyay.cfg",
                "eventyay.cfg",
            ],
            encoding="utf-8",
        )
    return (
        config,
        config_files or [],
    )  # .read() returns None if there are no config files


def read_layer(layer_name, config):
    config_dict = reduce_dict(
        {
            section_name: {
                key: value.get(layer_name) for key, value in section_content.items()
            }
            for section_name, section_content in CONFIG.items()
        }
    )
    config.read_dict(config_dict)
    return config


def build_config():
    config = configparser.RawConfigParser()
    config = read_layer("default", config)
    config, config_files = read_config_files(config)
    config = read_layer("env", config)
    return config, config_files
