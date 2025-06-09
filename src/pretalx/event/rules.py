import rules


@rules.predicate
def can_change_teams(user, obj):
    if not user or user.is_anonymous:
        return False
    if getattr(user, "is_administrator", False):
        return True
    if event := getattr(obj, "event", None):
        return event.teams.filter(members__in=[user], can_change_teams=True).exists()
    obj = obj.organiser
    return user.teams.filter(organiser=obj, can_change_teams=True).exists()
