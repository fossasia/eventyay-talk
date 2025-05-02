import rules

@rules.predicate
def can_change_teams(user, obj):
    if getattr(user, "is_administrator", False):
        return True
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
