from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter

from pretalx.mail.models import MailTemplateRoles


def build_expand_docs(*params):
    description = 'Select fields to <a href="https://docs.pretalx.org/api/fundamentals/#expansion">expand</a>.'
    return OpenApiParameter(
        name="expand",
        type=OpenApiTypes.STR,
        location=OpenApiParameter.QUERY,
        description=description,
        enum=params,
        many=True,
    )


def build_search_docs(*params, extra_description=None):
    fields = ",".join([f'`"{param}"`' for param in params])
    description = f"A search term, searching in {fields}."
    if extra_description:
        description = f"{description} {extra_description}"
    return OpenApiParameter(
        name="q",
        type=OpenApiTypes.STR,
        location=OpenApiParameter.QUERY,
        description=description,
    )


def postprocess_schema(result, generator, request, public):

    # Due to a bug with non-editable fields, the mail template role enum is not being
    # rendered, so we’re adding it manually after the fact.
    result["components"]["schemas"]["RoleEnum"] = {
        "enum": list(dict(MailTemplateRoles.choices).keys()),
        "type": "string",
        "description": "\n".join(
            [f"* `{key}` - {value}" for key, value in MailTemplateRoles.choices]
        ),
    }
    result["components"]["schemas"]["MailTemplate"]["properties"]["role"] = {
        "nullable": True,
        "$ref": "#/components/schemas/RoleEnum",
    }

    # Section headings
    result["tags"] = [
        {
            "name": "speaker-information",
            "description": "Speaker information can be used to provide important information to speakers, either to all speakers or only to accepted or confirmed speakers.",
        },
        {
            "name": "submission-types",
            "description": "Submission types define the types of proposals that can be submitted to an event, including their default duration.",
            "externalDocs": {
                "url": "https://docs.pretalx.org/user/sessions/#session-types",
                "description": "User documentation",
            },
        },
        {
            "name": "tags",
            "description": "Tags are currently only used in the organiser backend and not publicly. As such, all tag endpoints require authentication.",
            "externalDocs": {
                "url": "https://docs.pretalx.org/user/sessions/#tags",
                "description": "User documentation",
            },
        },
        {
            "name": "tracks",
            "description": "Tracks are a way to organise proposals and talks into categories, usually for thematic grouping.",
            "externalDocs": {
                "url": "https://docs.pretalx.org/user/sessions/#tracks",
                "description": "User documentation",
            },
        },
        {
            "name": "rooms",
            "description": "Rooms are part of conference schedules. Only once the conference schedule is public will the rooms API be available to unauthenticated users. Authenticated organisers will see additional fields in the API, in line with the create and update actions.",
        },
        {
            "name": "mail-templates",
            "description": "Mail templates are used to define standardized mail formats for standard situations, like acceptance or rejection mails, or to add custom email templates for your own use. Please note that the role attribute cannot be changed.",
        },
        {
            "name": "access-codes",
            "description": "Access codes can be used to grant access to restricted tracks, or to allow for proposals to be submitted past the public deadline.",
        },
        {
            "name": "speakers",
            "description": "Speakers can currently only updated, not created or deleted, as a speaker refers to a user object, and users can only be deleted by administrators. Organisers will see additional fields in the API, in line with the response to the update actions.",
        },
        {
            "name": "submissions",
            "description": "Submissions are the central component of pretalx. Note that changing the speakers and state of a submission requires you to use the individual action endpoints rather than a plain update.",
            "externalDocs": {
                "url": "https://docs.pretalx.org/user/sessions/",
                "description": "User documentation",
            },
        },
        {
            "name": "slots",
            "description": (
                "Every block in a published pretalx schedule is a talk slot. Note that there are talk slots without associalted submission (e.g. breaks). "
                "Each slot belongs to a schedule version – refer to the schedule endpoint for further documentation. "
                "Note that slots cannot be created or deleted via the API – this happens automatically when a submission’s state changes."
            ),
        },
        {
            "name": "reviews",
            "description": (
                "Reviews can be created, updated and deleted in the API depending on permissions (user, token and team), "
                "the current review phase, and so on. "
                "As with the other endpoints, this endpoint is not available to users/tokens with only reviewer permissions "
                "while an anonymised review phase is active."
            ),
        },
    ]
    return result
