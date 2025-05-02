from django.urls import include, path
from rest_framework import routers
from rest_framework.authtoken.views import obtain_auth_token

from pretalx.api.views import (
    access_code,
    event,
    mail,
    question,
    review,
    room,
    speaker,
    speaker_information,
    submission,
    upload,
    user,
)

default_router = routers.DefaultRouter()
default_router.register("events", event.EventViewSet, basename="event")

event_router = routers.DefaultRouter()
event_router.register(
    "submissions", submission.SubmissionViewSet, basename="submission"
)
event_router.register("talks", submission.SubmissionViewSet, basename="talks")
event_router.register("schedules", submission.ScheduleViewSet, basename="schedule")
event_router.register("tags", submission.TagViewSet, basename="tag")
event_router.register(
    "submission-types", submission.SubmissionTypeViewSet, basename="submission_type"
)
event_router.register("tracks", submission.TrackViewSet, basename="track")
event_router.register(
    "mail-templates", mail.MailTemplateViewSet, basename="mail_template"
)
event_router.register(
    "access-codes", access_code.SubmitterAccessCodeViewSet, basename="access_code"
)
event_router.register("speakers", speaker.SpeakerViewSet, basename="speaker")
event_router.register("reviews", review.ReviewViewSet, basename="review")
event_router.register("rooms", room.RoomViewSet, basename="room")
event_router.register("questions", question.QuestionViewSet, basename="question")
event_router.register("answers", question.AnswerViewSet, basename="answer")
event_router.register(
    "question-options", question.AnswerOptionViewSet, basename="question_option"
)
event_router.register(
    "speaker-information",
    speaker_information.SpeakerInformationViewSet,
    basename="speaker_information",
)

app_name = "api"
urlpatterns = [
    path("", include(default_router.urls)),
    path("me", user.MeView.as_view(), name="user.me"),
    path("auth/", obtain_auth_token),
    path("upload/", upload.UploadView.as_view(), name="upload"),
    path("events/<slug:event>/", include(event_router.urls)),
]
