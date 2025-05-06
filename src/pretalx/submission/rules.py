import rules
from django.db.models import Exists, OuterRef, Subquery

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
    if (
        not user.is_anonymous
        and user.get_permissions_for_event(event) == {"is_reviewer"}
        and can_view_speaker_names(user, event)
    ):
        return event.questions(manager="all_objects").filter(
            Q(is_visible_to_reviewers=True) | Q(target=QuestionTarget.REVIEWER),
            active=True,
        )
    if user.has_perm(Question.get_perm("orga_list"), event):
        # Other team members can either view all active questions
        # or only questions open to reviewers
        return event.questions(manager="all_objects").all()

    # Now we are left with anonymous users or users with very limited permissions.
    # They can see all public (non-reviewer) questions if they are already publicly
    # visible in the schedule. Otherwise, nothing.
    if user.has_perm(Question.get_perm("list"), event):
        return event.questions.all().filter(is_public=True)
    return event.questions.none()


def annotate_assigned(queryset, event, user):
    assigned = user.assigned_reviews.filter(event=event, pk=OuterRef("pk"))
    return queryset.annotate(is_assigned=Exists(Subquery(assigned)))


def get_reviewer_tracks(event, user):
    teams = event.teams.filter(
        members__in=[user], limit_tracks__isnull=False
    ).prefetch_related("limit_tracks", "limit_tracks__event")
    tracks = set()
    for team in teams:
        tracks.update(team.limit_tracks.filter(event=event))
    return tracks


def limit_for_reviewers(queryset, event, user, reviewer_tracks=None):
    if not (phase := event.active_review_phase):
        return event.submissions.none()
    if phase.proposal_visibility == "assigned":
        queryset = annotate_assigned(queryset, event, user)
        return queryset.filter(is_assigned__gte=1)
    if reviewer_tracks is None:
        reviewer_tracks = get_reviewer_tracks(event, user)
    if reviewer_tracks:
        return queryset.filter(track__in=reviewer_tracks)
    return queryset


def submissions_for_user(event, user):
    if user.is_anonymous:
        if user.has_perm("agenda.view_schedule", event):
            return event.current_schedule.slots
        return event.submissions.none()

    if user.get_permissions_for_event(event) == {"is_reviewer"}:
        return limit_for_reviewers(event.submissions.all(), event, user)

    if user.has_perm("orga.view_submissions", event):
        return event.submissions.all()
    return event.submissions.none()


def speaker_profiles_for_user(event, user, submissions=None):
    submissions = submissions or submissions_for_user(event, user)
    from pretalx.person.models import SpeakerProfile, User

    return SpeakerProfile.objects.filter(
        event=event, user__in=User.objects.filter(submissions__in=submissions)
    )
