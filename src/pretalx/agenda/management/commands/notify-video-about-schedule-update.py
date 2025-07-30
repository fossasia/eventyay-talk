import logging
from argparse import ArgumentParser
from urllib.parse import urljoin, urlparse

import requests
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from pretalx.event.models import Event


# The name of the Video container
VIDEO_CONTAINER_NAME = 'eventyay-video'
logger = logging.getLogger(__name__)


def replace_hostname(url: str) -> str:
    '''
    Replace the hostname of the URL with the name of the Video container.
    '''
    parsed_url = urlparse(url)
    parsed_url = parsed_url._replace(netloc=VIDEO_CONTAINER_NAME, scheme='http')
    return parsed_url.geturl()


def push_to_video_site(event: Event):
    url = urljoin(event.venueless_settings.url, 'schedule_update')
    logger.info('Saved video API URL: %s', url)
    # In development with Docker, we use fake domain, so the URL can not reach the video site,
    # we need to replace the hostname.
    url = replace_hostname(url)
    # I haven't found the page to retrieve this token.
    # In development, I get it from ShortToken model in Video container.
    token = event.venueless_settings.token
    logger.info('To push schedule to rewritten video API URL instead: %s', url)
    post_data = {
        'domain': event.custom_domain or settings.SITE_URL,
        'event': event.slug,
    }
    logger.info('With post data: %s', post_data)
    logger.info('Authenticated with token: %s', token)
    response = requests.post(
        url,
        json=post_data,
        headers={
            'Authorization': f'Bearer {token}',
        },
    )
    if not response.ok:
        logger.error('Failed to push schedule to video site: %s', response.text)
        raise CommandError(f'Failed to push schedule to video site: {response.text}')
    logger.info('Response: %s', response.content)
    logger.info('Schedule pushed to video site successfully.')


class Command(BaseCommand):
    '''
    Inform the video site that the schedule has been updated.
    '''
    def add_arguments(self, parser: ArgumentParser):
        parser.add_argument('event_slug', type=str)

    def handle(self, event_slug: str, **options):
        event = Event.objects.get(slug=event_slug)
        push_to_video_site(event)

