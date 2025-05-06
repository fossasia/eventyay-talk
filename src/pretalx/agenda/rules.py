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
def is_speaker_viewable(user, profile):
    if not profile:
        return False
    is_speaker = profile.user.submissions.filter(
        slots__schedule=profile.event.current_schedule
    ).exists()
    return is_speaker and can_view_schedule(user, profile.event)
