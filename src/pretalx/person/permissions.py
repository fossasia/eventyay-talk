import rules

from pretalx.submission.models.submission import SubmissionStates
from pretalx.submission.rules import orga_can_change_submissions


@rules.predicate
def is_administrator(user, obj):
    return getattr(user, "is_administrator", False)


@rules.predicate
def person_can_view_information(user, obj):
    event = obj.event
    qs = event.submissions.filter(speakers__in=[user])
    tracks = obj.limit_tracks.all()
    types = obj.limit_types.all()
    if tracks:
        qs = qs.filter(track__in=tracks)
    if types:
        qs = qs.filter(submission_type__in=types)
    if obj.target_group == "submitters":
        return qs.exists()
    if obj.target_group == "confirmed":
        return qs.filter(state=SubmissionStates.CONFIRMED).exists()
    return qs.filter(state__in=SubmissionStates.accepted_states).exists()


rules.add_perm("person.is_administrator", is_administrator)
rules.add_perm(
    "person.view_information", orga_can_change_submissions | person_can_view_information
)
rules.add_perm("person.change_information", orga_can_change_submissions)
