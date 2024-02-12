from django.dispatch import receiver
from django.utils.translation import gettext_lazy as _

from eventyay.common.models.log import ActivityLog
from eventyay.common.signals import activitylog_display
from eventyay.event.models.event import Event

LOG_NAMES = {
    "eventyay.cfp.update": _("The CfP has been modified."),
    "eventyay.event.create": _("The event has been added."),
    "eventyay.event.update": _("The event was modified."),
    "eventyay.event.activate": _("The event was made public."),
    "eventyay.event.deactivate": _("The event was deactivated."),
    "eventyay.event.plugins.enabled": _("A plugin was enabled."),
    "eventyay.event.plugins.disabled": _("A plugin was disabled."),
    "eventyay.invite.orga.accept": _("The invitation to the event orga was accepted."),
    "eventyay.invite.orga.retract": _("An invitation to the event orga was retracted."),
    "eventyay.invite.orga.send": _("An invitation to the event orga was sent."),
    "eventyay.invite.reviewer.retract": _(
        "The invitation to the review team was retracted."
    ),
    "eventyay.invite.reviewer.send": _("The invitation to the review team was sent."),
    "eventyay.event.invite.orga.accept": _(
        "The invitation to the event orga was accepted."
    ),  # compat
    "eventyay.event.invite.orga.retract": _(
        "An invitation to the event orga was retracted."
    ),  # compat
    "eventyay.event.invite.orga.send": _(
        "An invitation to the event orga was sent."
    ),  # compat
    "eventyay.event.invite.reviewer.retract": _(
        "The invitation to the review team was retracted."
    ),  # compat
    "eventyay.event.invite.reviewer.send": _(
        "The invitation to the review team was sent."
    ),  # compat
    "eventyay.mail.create": _("An email was modified."),
    "eventyay.mail.delete": _("A pending email was deleted."),
    "eventyay.mail.delete_all": _("All pending emails were deleted."),
    "eventyay.mail.sent": _("An email was sent."),
    "eventyay.mail.update": _("An email was modified."),
    "eventyay.mail_template.create": _("A mail template was added."),
    "eventyay.mail_template.delete": _("A mail template was deleted."),
    "eventyay.mail_template.update": _("A mail template was modified."),
    "eventyay.question.create": _("A question was added."),
    "eventyay.question.delete": _("A question was deleted."),
    "eventyay.question.update": _("A question was modified."),
    "eventyay.question.option.create": _("A question option was added."),
    "eventyay.question.option.delete": _("A question option was deleted."),
    "eventyay.question.option.update": _("A question option was modified."),
    "eventyay.tag.create": _("A tag was added."),
    "eventyay.tag.delete": _("A tag was deleted."),
    "eventyay.tag.update": _("A tag was modified."),
    "eventyay.room.create": _("A new room was added."),
    "eventyay.schedule.release": _("A new schedule version was released."),
    "eventyay.submission.accept": _("The proposal was accepted."),
    "eventyay.submission.cancel": _("The proposal was cancelled."),
    "eventyay.submission.confirm": _("The proposal was confirmed."),
    "eventyay.submission.confirmation": _("The proposal was confirmed."),  # Legacy
    "eventyay.submission.create": _("The proposal was added."),
    "eventyay.submission.deleted": _("The proposal was deleted."),
    "eventyay.submission.reject": _("The proposal was rejected."),
    "eventyay.submission.resource.create": _("A proposal resource was added."),
    "eventyay.submission.resource.delete": _("A proposal resource was deleted."),
    "eventyay.submission.resource.update": _("A proposal resource was modified."),
    "eventyay.submission.speakers.add": _("A speaker was added to the proposal."),
    "eventyay.submission.speakers.invite": _("A speaker was invited to the proposal."),
    "eventyay.submission.speakers.remove": _("A speaker was removed from the proposal."),
    "eventyay.submission.unconfirm": _("The proposal was unconfirmed."),
    "eventyay.submission.update": _("The proposal was modified."),
    "eventyay.submission.withdraw": _("The proposal was withdrawn."),
    "eventyay.submission.answer.update": _("A proposal answer was modified."),  # Legacy
    "eventyay.submission.answerupdate": _("A proposal answer was modified."),  # Legacy
    "eventyay.submission.answer.create": _("A proposal answer was added."),  # Legacy
    "eventyay.submission.answercreate": _("A proposal answer was added."),  # Legacy
    "eventyay.submission_type.create": _("A session type was added."),
    "eventyay.submission_type.delete": _("A session type was deleted."),
    "eventyay.submission_type.make_default": _("The session type was made default."),
    "eventyay.submission_type.update": _("A session type was modified."),
    "eventyay.access_code.create": _("An access code was added."),
    "eventyay.access_code.send": _("An access code was sent."),
    "eventyay.access_code.update": _("An access code was modified."),
    "eventyay.access_code.delete": _("An access code was deleted."),
    "eventyay.track.create": _("A track was added."),
    "eventyay.track.delete": _("A track was deleted."),
    "eventyay.track.update": _("A track was modified."),
    "eventyay.speaker.arrived": _("A speaker has been marked as arrived."),
    "eventyay.speaker.unarrived": _("A speaker has been marked as not arrived."),
    "eventyay.user.token.reset": _("The API token was reset."),
    "eventyay.user.password.reset": _("The password was reset."),
    "eventyay.user.password.update": _("The password was modified."),
    "eventyay.user.profile.update": _("The profile was modified."),
}


@receiver(activitylog_display)
def default_activitylog_display(sender: Event, activitylog: ActivityLog, **kwargs):
    return LOG_NAMES.get(activitylog.action_type)
