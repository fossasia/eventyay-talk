import rules


@rules.predicate
def is_reviewer(user, obj):
    event = getattr(obj, "event", None)
    if not user or user.is_anonymous or not obj or not event:
        return False
    return user in event.reviewers


@rules.predicate
def can_change_event_settings(user, obj):
    event = getattr(obj, "event", None)
    if not event or not obj or not user or user.is_anonymous:
        return False
    if user.is_administrator:
        return True
    return event.teams.filter(
        members__in=[user], can_change_event_settings=True
    ).exists()
