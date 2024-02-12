Data models
===========

The following are all of the relevant eventyay database models, including their
interfaces. All non-documented methods and properties should be considered
private and unstable. All methods and properties documented here may change
between releases, but any change will be mentioned in the release notes
starting with the 1.0 release.

All event related objects have an ``event`` property. It always returns the
event this object belongs to, to ease permission checks and reduce the need for
duplicate lookups.

Events and organisers
---------------------

.. autoclass:: eventyay.event.models.event.Event(*args, **kwargs)
   :members: cache,locales,is_multilingual,named_locales,plugin_list,enable_plugin,disable_plugin,pending_mails,wip_schedule,current_schedule,teams,datetime_from,datetime_to,talks,speakers,submitters,get_date_range_display,release_schedule,shred

.. autoclass:: eventyay.event.models.organiser.Organiser(*args, **kwargs)
   :members: shred

.. autoclass:: eventyay.event.models.organiser.Team(*args, **kwargs)
   :members: permission_set

.. autoclass:: eventyay.submission.models.cfp.CfP(*args, **kwargs)
   :members: max_deadline,is_open

.. autoclass:: eventyay.submission.models.review.ReviewPhase(*args, **kwargs)
   :members: activate

Users and profiles
------------------

.. autoclass:: eventyay.person.models.user.User(*args, **kwargs)
   :members: get_display_name,event_profile,log_action,get_events_with_any_permission,get_events_for_permission,get_permissions_for_event

.. autoclass:: eventyay.person.models.profile.SpeakerProfile(*args, **kwargs)
   :members: submissions,talks,answers

.. autoclass:: eventyay.person.models.information.SpeakerInformation(*args, **kwargs)
   :members: id

Submissions
-----------

Submissions are the most central model to eventyay, and everything else is
connected to submissions.

.. autoclass:: eventyay.submission.models.submission.Submission(*args, **kwargs)
   :members: get_duration,update_duration,update_talk_slots,make_submitted,confirm,accept,reject,cancel,withdraw,delete,uuid,public_slots,slot,display_speaker_names,median_score,availabilities

.. autoclass:: eventyay.submission.models.review.Review(*args, **kwargs)
   :members: find_missing_reviews, display_score

.. autoclass:: eventyay.submission.models.feedback.Feedback(*args, **kwargs)
   :members: id

.. autoclass:: eventyay.submission.models.track.Track(*args, **kwargs)
   :members: slug

.. autoclass:: eventyay.submission.models.type.SubmissionType(*args, **kwargs)
   :members: slug,update_duration

.. autoclass:: eventyay.submission.models.resource.Resource(*args, **kwargs)
   :members: id

Questions and answers
---------------------

.. autoclass:: eventyay.submission.models.question.Question(*args, **kwargs)
   :members: missing_answers

.. autoclass:: eventyay.submission.models.question.AnswerOption(*args, **kwargs)
   :members: id

.. autoclass:: eventyay.submission.models.question.Answer(*args, **kwargs)
   :members: remove

Schedules and talk slots
------------------------

.. autoclass:: eventyay.schedule.models.schedule.Schedule(*args, **kwargs)
   :members: freeze,unfreeze,scheduled_talks,slots,previous_schedule,changes,warnings,speakers_concerned,notifications,notify_speakers

.. autoclass:: eventyay.schedule.models.slot.TalkSlot(*args, **kwargs)
   :members: duration,real_end,as_availability,copy_to_schedule,is_same_slot

.. autoclass:: eventyay.schedule.models.availability.Availability(*args, **kwargs)
   :members: __eq__,all_day,overlaps,contains,merge_with,__or__,intersect_with,__and__,union,intersection

.. autoclass:: eventyay.schedule.models.room.Room(*args, **kwargs)
   :members: id

Emails and templates
--------------------

.. autoclass:: eventyay.mail.models.MailTemplate
   :members: to_mail

.. autoclass:: eventyay.mail.models.QueuedMail
   :members: send,copy_to_draft

Utility models
--------------

.. autoclass:: eventyay.common.models.log.ActivityLog
   :members: display,get_orga_url,get_public_url
