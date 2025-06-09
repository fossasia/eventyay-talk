import rules


@rules.predicate
def is_agenda_visible(user, event):
    event = event.event
    return bool(
        event
        and event.is_public
        and event.get_feature_flag("show_schedule")
        and event.current_schedule
    )
