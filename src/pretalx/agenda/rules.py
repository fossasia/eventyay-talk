import rules

from pretalx.submission.rules import orga_can_change_submissions


@rules.predicate
def has_agenda(user, event):
    return bool(event.current_schedule)


@rules.predicate
def is_agenda_visible(user, event):
    event = event.event
    return bool(
        event
        and event.is_public
        and event.get_feature_flag("show_schedule")
        and event.current_schedule
    )


can_view_schedule = (has_agenda & is_agenda_visible) | orga_can_change_submissions


@rules.predicate
def are_featured_submissions_visible(user, event):
    if (
        not event
        or not event.is_public
        or event.get_feature_flag("show_featured") == "never"
    ):
        return False
    if event.get_feature_flag("show_featured") == "always":
        return True
    return (not is_agenda_visible(user, event)) or (not has_agenda(user, event))


def is_submission_visible_via_featured(user, submission):
    return bool(
        submission
        and submission.is_featured
        and are_featured_submissions_visible(user, submission.event)
    )


def is_submission_visible_via_schedule(user, submission):
    return bool(
        submission
        and is_agenda_visible(user, submission.event)
        and submission.slots.filter(
            schedule=submission.event.current_schedule, is_visible=True
        ).exists()
    )


@rules.predicate
def is_agenda_submission_visible(user, submission):
    submission = getattr(submission, "submission", submission)
    if not submission:
        return False
    return is_submission_visible_via_schedule(
        user, submission
    ) or is_submission_visible_via_featured(user, submission)


@rules.predicate
def is_speaker_viewable(user, profile):
    if not profile:
        return False
    is_speaker = profile.user.submissions.filter(
        slots__schedule=profile.event.current_schedule
    ).exists()
    return is_speaker and can_view_schedule(user, profile.event)
