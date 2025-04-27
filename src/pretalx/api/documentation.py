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


def build_search_docs(*params):
    fields = ",".join([f'`"{param}"`' for param in params])
    description = f"A search term, searching in {fields}."
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
    ]
    return result
