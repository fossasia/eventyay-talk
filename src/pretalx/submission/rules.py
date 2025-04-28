import rules

from pretalx.person.rules import is_reviewer


@rules.predicate
def reviewer_can_create_tags(user, obj):
    event = obj.event
    return bool(
        event.active_review_phase
        and event.active_review_phase.can_tag_submissions == "create_tags"
    )


@rules.predicate
def reviewer_can_change_tags(user, obj):
    event = obj.event
    return bool(
        event.active_review_phase
        and event.active_review_phase.can_tag_submissions == "use_tags"
    )


@rules.predicate
def orga_can_change_submissions(user, obj):
    event = getattr(obj, "event", None)
    if not user or user.is_anonymous or not obj or not event:
        return False
    if user.is_administrator:
        return True
    return event.teams.filter(members__in=[user], can_change_submissions=True).exists()


orga_can_view_submissions = orga_can_change_submissions | is_reviewer


@rules.predicate
def is_cfp_open(user, obj):
    event = getattr(obj, "event", None)
    return event and event.is_public and event.cfp.is_open
