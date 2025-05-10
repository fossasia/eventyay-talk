import rules

from pretalx.submission.rules import (
    can_be_reviewed,
    has_reviewer_access,
    is_speaker,
    orga_can_change_submissions,
)


@rules.predicate
def has_submissions(user, obj):
    event = obj.event
    return event.submissions.filter(speakers__in=[user]).exists()


@rules.predicate
def is_review_author(user, obj):
    return obj and obj.user == user


@rules.predicate
def can_view_reviews(user, obj):
    phase = obj.event.active_review_phase
    if not phase:
        return False
    if phase.can_see_other_reviews == "always":
        return True
    if phase.can_see_other_reviews == "after_review":
        return obj.reviews.filter(user=user).exists()
    return False


@rules.predicate
def can_view_all_reviews(user, obj):
    phase = obj.event.active_review_phase
    if not phase:
        return False
    return phase.can_see_other_reviews == "always"


@rules.predicate
def is_comment_author(user, obj):
    return obj and obj.user == user


@rules.predicate
def submission_comments_active(user, obj):
    return obj.event.get_feature_flag("use_submission_comments")


rules.add_perm("submission.perform_actions", is_speaker)
rules.add_perm("submission.is_speaker", is_speaker)
rules.add_perm(
    "submission.edit_review", has_reviewer_access & can_be_reviewed & is_review_author
)
rules.add_perm(
    "submission.view_reviews", has_reviewer_access | orga_can_change_submissions
)
rules.add_perm("submission.edit_speaker_list", is_speaker | orga_can_change_submissions)
rules.add_perm(
    "submission.view_feedback",
    is_speaker | orga_can_change_submissions | has_reviewer_access,
)
rules.add_perm(
    "submission.view_submission_comments",
    submission_comments_active & (has_reviewer_access | orga_can_change_submissions),
)
rules.add_perm(
    "submission.add_submission_comments",
    submission_comments_active & (has_reviewer_access | orga_can_change_submissions),
)
rules.add_perm(
    "submission.delete_submission_comment",
    submission_comments_active
    & (has_reviewer_access | orga_can_change_submissions)
    & is_comment_author,
)
