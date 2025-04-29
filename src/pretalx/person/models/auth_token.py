import string

from django.db import models
from django.db.models import Q
from django.utils.crypto import get_random_string
from django.utils.timezone import now
from django.utils.translation import gettext_lazy as _

from pretalx.common.models.mixins import PretalxModel


def generate_api_token():
    return get_random_string(
        length=64, allowed_chars=string.ascii_lowercase + string.digits
    )


READ_PERMISSIONS = ("list", "retrieve")
WRITE_PERMISSIONS = READ_PERMISSIONS + ("create", "update", "destroy", "actions")
PERMISSION_CHOICES = (
    ("list", _("Read list")),
    ("retrieve", _("Read details")),
    ("create", _("Create")),
    ("update", _("Update")),
    ("destroy", _("Delete")),
    ("actions", _("Additional actions")),
)
ENDPOINTS = (
    "events",
    "submissions",
    "speakers",
    "reviews",
    "rooms",
    "questions",
    "answers",
    "tags",
    "tracks",
    "schedules",
    "submission-types",
)


def default_endpoint_permissions():
    return {endpoint: READ_PERMISSIONS for endpoint in ENDPOINTS}


class UserApiTokenManager(models.Manager):

    def active(self):
        return self.get_queryset().filter(
            Q(expires__isnull=True) | Q(expires__gt=now())
        )


class UserApiToken(PretalxModel):
    name = models.CharField(max_length=190, verbose_name=_("Name"))
    token = models.CharField(default=generate_api_token, max_length=64)
    user = models.ForeignKey(
        to="person.User",
        related_name="api_tokens",
        on_delete=models.CASCADE,
    )
    # TODO: make sure the token is deactivated if the user is removed from the team
    # TODO: show that users have active tokens in team list
    team = models.ForeignKey(
        to="event.Team",
        related_name="api_tokens",
        on_delete=models.CASCADE,
        verbose_name=_("Team"),
    )
    # TODO: make sure we check token.expires before allowing access
    expires = models.DateTimeField(null=True, blank=True, verbose_name=_("Expiry date"))
    # TODO document field structure
    endpoints = models.JSONField(default=default_endpoint_permissions, blank=True)
    version = models.CharField(
        max_length=12, null=True, blank=True, verbose_name=_("API version")
    )
    last_used = models.DateTimeField(null=True, blank=True)

    objects = UserApiTokenManager()

    def has_endpoint_permission(self, endpoint, method):
        if method == "partial_update":
            # We don't track separate permissions for partial updates
            method = "update"
        perms = self.endpoints.get(
            endpoint, default_endpoint_permissions().get(endpoint, [])
        )
        return method in perms

    @property
    def is_active(self):
        return not self.expires or self.expires > now()

    def serialize(self):
        return {
            "name": self.name,
            "token": self.token,
            "team": self.team_id,
            "expires": self.expires.isoformat() if self.expires else None,
            "endpoints": self.endpoints,
            "version": self.version,
        }
