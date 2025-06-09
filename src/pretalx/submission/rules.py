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


def questions_for_user(event, user):
    """Used to retrieve synced querysets in the orga list and the API list."""
    from django.db.models import Q

    from pretalx.orga.permissions import can_view_speaker_names
    from pretalx.submission.models import Question, QuestionTarget

    if user.has_perm(Question.get_perm("update"), event):
        # Organisers with edit permissions can see everything
        return event.questions(manager="all_objects").all()
    if user.has_perm(Question.get_perm("orga_list"), event):
        # Other team members can either view all active questions
        # or only questions open to reviewers
        queryset = event.questions(manager="all_objects").all()
        if is_reviewer(user, event) and can_view_speaker_names(user, event):
            return queryset.filter(
                Q(is_visible_to_reviewers=True) | Q(target=QuestionTarget.REVIEWER),
                active=True,
            )
        return queryset

    # Now we are left with anonymous users or users with very limited permissions.
    # They can see all public (non-reviewer) questions if they are already publicly
    # visible in the schedule. Otherwise, nothing.
    if user.has_perm(Question.get_perm("list"), event):
        return event.questions.all().filter(is_public=True)
    return event.questions.none()
