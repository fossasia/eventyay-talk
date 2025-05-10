import rules

from pretalx.agenda.rules import (
    are_featured_submissions_visible,
    can_view_schedule,
    is_agenda_submission_visible,
    is_agenda_visible,
    is_speaker_viewable,
)
from pretalx.submission.rules import orga_can_change_submissions


@rules.predicate
def is_widget_always_visible(user, event):
    return event.get_feature_flag("show_widget_if_not_public")


@rules.predicate
def is_feedback_ready(user, submission):
    return bool(
        submission
        and is_agenda_submission_visible(user, submission)
        and submission.does_accept_feedback
    )


@rules.predicate
def event_uses_feedback(user, event):
    event = getattr(event, "event", event)
    return event and event.get_feature_flag("use_feedback")


rules.add_perm("agenda.view_schedule", can_view_schedule)
rules.add_perm(
    "agenda.view_featured_submissions",
    are_featured_submissions_visible | orga_can_change_submissions,
)
rules.add_perm(
    "agenda.view_submission", is_agenda_submission_visible | orga_can_change_submissions
)
rules.add_perm("agenda.view_speaker", is_speaker_viewable | orga_can_change_submissions)
rules.add_perm("agenda.give_feedback", is_feedback_ready)
rules.add_perm(
    "agenda.view_feedback_page", event_uses_feedback & is_agenda_submission_visible
)
rules.add_perm(
    "agenda.view_widget",
    is_agenda_visible | is_widget_always_visible | orga_can_change_submissions,
)
