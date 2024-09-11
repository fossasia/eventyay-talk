import logging

from celery import shared_task
from django.core.exceptions import ValidationError
from django.http import Http404
from django.shortcuts import get_object_or_404

from pretalx.event.forms import TeamForm
from pretalx.event.models import Organiser, Team

logger = logging.getLogger(__name__)


class Action:
    CREATE = "create"
    UPDATE = "update"
    DELETE = "delete"


@shared_task
def process_create_organiser_webhook(organiser_data):
    try:
        action = organiser_data.get("action")
        if action == Action.CREATE:
            organiser = Organiser(
                name=organiser_data.get("name"), slug=organiser_data.get("slug")
            )
            organiser.full_clean()
            organiser.save()
            logger.info(f"Organiser {organiser.name} created successfully.")
            # Create an Administrator team for new organiser
            team = TeamForm(
                organiser=organiser,
                data={
                    "name": "Administrators",
                    "all_events": True,
                    "can_create_events": True,
                    "can_change_teams": True,
                    "can_change_organiser_settings": True,
                    "can_change_event_settings": True,
                    "can_change_submissions": True,
                },
            )
            if team.is_valid():
                team.save()
                logger.info(
                    f"Administrator team for organiser {organiser.name} created "
                    f"successfully."
                )
            else:
                logger.error(
                    f"Error creating Administrator team for organiser {organiser.name}: {team.errors}"
                )

        elif action == Action.UPDATE:
            organiser = Organiser.objects.get(slug=organiser_data.get("slug"))
            organiser.name = organiser_data.get("name")
            organiser.full_clean()
            organiser.save()
            logger.info(f"Organiser {organiser.name} updated successfully.")

        elif action == Action.DELETE:
            # Implement delete logic here
            logger.info(f"Organiser delete not implemented yet.")
            pass

        else:
            logger.error(f"Unknown action: {action}")
    except ValidationError as e:
        logger.error("Validation error:", e.message_dict)
    except Exception as e:
        logger.error("Error saving organiser:", e)


@shared_task
def process_create_team_webhook(team_data):
    try:
        action = team_data.get("action")
        organiser = get_object_or_404(Organiser, slug=team_data.get("organiser_slug"))
        if action == Action.CREATE:
            team = TeamForm(organiser=organiser, data=team_data)
            if team.is_valid():
                team.save()
                logger.info(
                    f"Team for organiser {organiser.name} created successfully."
                )
            else:
                logger.error(
                    f"Error creating Administrator team for organiser {organiser.name}: {team.errors}"
                )

        elif action == Action.UPDATE:
            team = Team.objects.filter(
                organiser=organiser, name=team_data.get("old_name")
            ).first()
            if not team:
                raise Http404("No Team matches the given query.")
            # Update the team object with new data from team_data
            for field, value in team_data.items():
                setattr(team, field, value)
            team.save()
            logger.info(f"Team for organiser {organiser.name} created successfully.")

        elif action == Action.DELETE:
            team = Team.objects.filter(
                organiser=organiser, name=team_data.get("name")
            ).first()
            if not team:
                raise Http404("No Team matches the given query.")
            team.delete()
            logger.info(f"Team for organiser {organiser.name} deleted successfully.")

        else:
            logger.error(f"Unknown action: {action}")
    except ValidationError as e:
        logger.error("Validation error:", e.message_dict)
    except Exception as e:
        logger.error("Error saving organiser:", e)
