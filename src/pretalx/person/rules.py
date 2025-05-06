import rules


@rules.predicate
def is_administrator(user, obj):
    return getattr(user, "is_administrator", False)


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


@rules.predicate
def can_view_information(user, obj):
    from pretalx.submission.models.submission import SubmissionStates

    event = obj.event
    qs = event.submissions.filter(speakers__in=[user])
    if tracks := obj.limit_tracks.all():
        qs = qs.filter(track__in=tracks)
    if types := obj.limit_types.all():
        qs = qs.filter(submission_type__in=types)
    if obj.target_group == "submitters":
        return qs.exists()
    if obj.target_group == "confirmed":
        return qs.filter(state=SubmissionStates.CONFIRMED).exists()
    return qs.filter(state__in=SubmissionStates.accepted_states).exists()
