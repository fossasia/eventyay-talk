import datetime as dt

import rules
from django.utils.timezone import now

from pretalx.person.permissions import is_administrator
from pretalx.person.rules import can_change_event_settings, is_reviewer
from pretalx.submission.permissions import (
    can_be_reviewed,
    can_view_all_reviews,
    can_view_reviews,
    is_review_author,
    reviewer_can_change_submissions,
)
from pretalx.submission.rules import orga_can_change_submissions


@rules.predicate
def can_change_organiser_settings(user, obj):
    event = getattr(obj, "event", None)
    if event:
        obj = event.organiser
    return (
        user.is_administrator
        or user.teams.filter(organiser=obj, can_change_organiser_settings=True).exists()
    )


@rules.predicate
def is_orga_member(user, obj):
    return not user.is_anonymous and (
        user.is_administrator or user.teams.filter(organiser=obj).exists()
    )


@rules.predicate
def can_change_any_organiser_settings(user, obj):
    return not user.is_anonymous and (
        user.is_administrator
        or user.teams.filter(can_change_organiser_settings=True).exists()
    )


@rules.predicate
def is_any_organiser(user, obj):
    return not user.is_anonymous and (
        user.is_administrator or user.teams.all().exists()
    )


@rules.predicate
def can_create_events(user, obj):
    return user.is_administrator or user.teams.filter(can_create_events=True).exists()


@rules.predicate
def can_change_teams(user, obj):
    from pretalx.event.models import Organiser, Team

    if isinstance(obj, Team):
        obj = obj.organiser
    if isinstance(obj, Organiser):
        return user.teams.filter(organiser=obj, can_change_teams=True).exists()
    event = getattr(obj, "event", None)
    if not user or user.is_anonymous or not obj or not event:
        return False
    if user.is_administrator:
        return True
    return event.teams.filter(members__in=[user], can_change_teams=True).exists()


@rules.predicate
def reviews_are_open(user, obj):
    event = obj.event
    return bool(event.active_review_phase and event.active_review_phase.can_review)


@rules.predicate
def can_edit_mail(user, obj):
    return getattr(obj, "sent", False) is None


@rules.predicate
def can_mark_speakers_arrived(user, obj):
    event = obj.event
    return (event.date_from - dt.timedelta(days=1)) <= now().date() <= event.date_to


@rules.predicate
def can_view_speaker_names(user, obj):
    """ONLY in use with users who don't have change permissions."""
    event = obj.event
    reviewer_teams = obj.event.teams.filter(members__in=[user], is_reviewer=True)
    if reviewer_teams and all(team.force_hide_speaker_names for team in reviewer_teams):
        return False
    return bool(
        event.active_review_phase and event.active_review_phase.can_see_speaker_names
    )


@rules.predicate
def can_view_reviewer_names(user, obj):
    event = obj.event
    return bool(
        event.active_review_phase and event.active_review_phase.can_see_reviewer_names
    )


rules.add_perm(
    "orga.view_orga_area",
    orga_can_change_submissions | can_change_event_settings | is_reviewer,
)
rules.add_perm("orga.change_settings", can_change_event_settings)
rules.add_perm("orga.change_organiser_settings", can_change_organiser_settings)
rules.add_perm("orga.view_organisers", can_change_any_organiser_settings)
rules.add_perm("orga.change_teams", is_administrator | can_change_teams)
rules.add_perm("orga.view_submission_cards", orga_can_change_submissions)
rules.add_perm("orga.edit_cfp", can_change_event_settings)
rules.add_perm("orga.view_question", orga_can_change_submissions)
rules.add_perm("orga.edit_question", can_change_event_settings)
rules.add_perm("orga.remove_question", can_change_event_settings)
rules.add_perm("orga.view_submission_type", orga_can_change_submissions)
rules.add_perm("orga.edit_submission_type", can_change_event_settings)
rules.add_perm("orga.remove_submission_type", can_change_event_settings)
rules.add_perm("orga.remove_track", can_change_event_settings)
rules.add_perm("orga.view_access_codes", orga_can_change_submissions)
rules.add_perm("orga.view_access_code", orga_can_change_submissions)
rules.add_perm("orga.edit_access_code", can_change_event_settings)
rules.add_perm("orga.remove_access_code", can_change_event_settings)
rules.add_perm("orga.view_mails", orga_can_change_submissions)
rules.add_perm("orga.send_mails", orga_can_change_submissions)
rules.add_perm("orga.send_reviewer_mails", can_change_teams)
rules.add_perm("orga.edit_mails", orga_can_change_submissions & can_edit_mail)
rules.add_perm("orga.purge_mails", orga_can_change_submissions)
rules.add_perm("orga.view_mail_templates", orga_can_change_submissions)
rules.add_perm("orga.edit_mail_templates", orga_can_change_submissions)
rules.add_perm("orga.view_review_dashboard", orga_can_change_submissions | is_reviewer)
rules.add_perm(
    "orga.view_reviews", orga_can_change_submissions | (is_reviewer & can_view_reviews)
)
rules.add_perm(
    "orga.view_all_reviews",
    orga_can_change_submissions | (is_reviewer & can_view_all_reviews),
)
rules.add_perm("orga.perform_reviews", is_reviewer & reviews_are_open)
rules.add_perm(
    "orga.remove_review", is_administrator | (is_review_author & can_be_reviewed)
)
rules.add_perm(
    "orga.view_schedule",
    orga_can_change_submissions | (is_reviewer & can_view_speaker_names),
)
rules.add_perm("orga.release_schedule", orga_can_change_submissions)
rules.add_perm("orga.edit_schedule", orga_can_change_submissions)
rules.add_perm("orga.schedule_talk", orga_can_change_submissions)
rules.add_perm("orga.view_room", orga_can_change_submissions)
rules.add_perm("orga.edit_room", orga_can_change_submissions)
rules.add_perm(
    "orga.view_speakers",
    orga_can_change_submissions | (is_reviewer & can_view_speaker_names),
)
rules.add_perm(
    "orga.view_speakers_in_review_context", is_reviewer & can_view_speaker_names
)
rules.add_perm("orga.view_organiser_speakers", is_orga_member)
rules.add_perm("orga.view_organiser_events", is_orga_member)
rules.add_perm("orga.view_organiser_lists", is_any_organiser)
rules.add_perm(
    "orga.view_speaker",
    orga_can_change_submissions | (is_reviewer & can_view_speaker_names),
)
rules.add_perm(
    "orga.view_reviewer_names",
    orga_can_change_submissions | (is_reviewer & can_view_reviewer_names),
)
rules.add_perm("orga.change_speaker", orga_can_change_submissions)
rules.add_perm("orga.view_submissions", orga_can_change_submissions | is_reviewer)
rules.add_perm("orga.create_submission", orga_can_change_submissions)
rules.add_perm("orga.change_submissions", orga_can_change_submissions)
rules.add_perm(
    "orga.change_submission_state",
    orga_can_change_submissions | (is_reviewer & reviewer_can_change_submissions),
)
rules.add_perm("orga.view_information", orga_can_change_submissions)
rules.add_perm("orga.change_information", can_change_event_settings)
rules.add_perm("orga.create_events", can_create_events)
rules.add_perm("orga.change_plugins", can_change_event_settings)
rules.add_perm(
    "orga.mark_speakers_arrived",
    orga_can_change_submissions & can_mark_speakers_arrived,
)
rules.add_perm("orga.see_speakers_arrival", orga_can_change_submissions)
