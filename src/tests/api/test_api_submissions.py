import json

import pytest
from django_scopes import scope

from pretalx.api.serializers.submission import (
    SubmissionOrgaSerializer,
    SubmissionSerializer,
    SubmissionTypeSerializer,
    TagSerializer,
    TrackSerializer,
)


@pytest.mark.django_db
def test_submission_slot_serializer(slot):
    with scope(event=slot.submission.event):
        data = SubmissionSerializer(
            slot.submission, context={"event": slot.submission.event}
        ).data
        assert set(data.keys()) == {
            "code",
            "speakers",
            "title",
            "submission_type",
            "submission_type_id",
            "state",
            "abstract",
            "description",
            "duration",
            "slot_count",
            "do_not_record",
            "is_featured",
            "content_locale",
            "slot",
            "image",
            "track",
            "track_id",
            "resources",
            "answers",
        }
        assert set(data["slot"].keys()) == {"start", "end", "room", "room_id"}
        assert data["slot"]["room"] == slot.room.name


@pytest.mark.django_db
def test_tag_serializer(tag):
    with scope(event=tag.event):
        data = TagSerializer(tag, context={"event": tag.event}).data
        assert set(data.keys()) == {
            "id",
            "tag",
            "description",
            "color",
            "is_public",
        }


@pytest.mark.django_db
def test_track_serializer(track):
    with scope(event=track.event):
        data = TrackSerializer(track, context={"event": track.event}).data
        assert set(data.keys()) == {
            "id",
            "name",
            "description",
            "color",
            "position",
            "requires_access_code",
        }


@pytest.mark.django_db
def test_submission_serializer_for_organiser(submission, orga_user, resource, tag):
    with scope(event=submission.event):
        submission.tags.add(tag)
        submission.favourite_count = 3
        data = SubmissionOrgaSerializer(
            submission,
            event=submission.event,
            can_view_speakers=True,
        ).data
        assert set(data.keys()) == {
            "code",
            "speakers",
            "title",
            "submission_type",
            "submission_type_id",
            "state",
            "pending_state",
            "abstract",
            "description",
            "duration",
            "slot_count",
            "do_not_record",
            "is_featured",
            "content_locale",
            "slot",
            "image",
            "answers",
            "track",
            "track_id",
            "notes",
            "internal_notes",
            "created",
            "resources",
            "tags",
            "tag_ids",
            "favourite_count",
        }
        assert isinstance(data["speakers"], list)
        assert data["speakers"][0] == {
            "name": submission.speakers.first().name,
            "code": submission.speakers.first().code,
            "email": submission.speakers.first().email,
            "biography": submission.speakers.first()
            .event_profile(submission.event)
            .biography,
            "avatar": None,
            "avatar_source": None,
            "avatar_license": None,
        }
        assert data["tags"] == [tag.tag]
        assert data["tag_ids"] == [tag.id]
        assert data["submission_type"] == str(submission.submission_type.name)
        assert data["slot"] is None
        assert (
            data["created"]
            == submission.created.astimezone(submission.event.tz).isoformat()
        )
        assert data["resources"] == [
            {
                "resource": "http://testserver" + resource.resource.url,
                "description": resource.description,
            }
        ]


@pytest.mark.django_db
def test_submission_serializer(submission, resource):
    with scope(event=submission.event):
        data = SubmissionSerializer(
            submission, context={"event": submission.event}
        ).data
        assert set(data.keys()) == {
            "code",
            "speakers",
            "title",
            "submission_type",
            "submission_type_id",
            "state",
            "abstract",
            "description",
            "duration",
            "slot_count",
            "do_not_record",
            "is_featured",
            "content_locale",
            "slot",
            "image",
            "track",
            "track_id",
            "resources",
            "answers",
        }
        assert isinstance(data["speakers"], list)
        assert data["speakers"] == []
        assert data["submission_type"] == str(submission.submission_type.name)
        assert data["slot"] is None
        assert data["resources"] == [
            {
                "resource": "http://testserver" + resource.resource.url,
                "description": resource.description,
            }
        ]


@pytest.mark.django_db
def test_can_only_see_public_submissions(
    client, slot, accepted_submission, rejected_submission, submission
):
    response = client.get(submission.event.api_urls.submissions, follow=True)
    content = json.loads(response.content.decode())

    assert response.status_code == 200
    assert content["count"] == 1
    assert content["results"][0]["title"] == slot.submission.title


@pytest.mark.django_db
def test_can_only_see_public_submissions_if_public_schedule(
    client, slot, accepted_submission, rejected_submission, submission, answer
):
    submission.event.feature_flags["show_schedule"] = False
    submission.event.save()
    response = client.get(submission.event.api_urls.submissions, follow=True)
    content = json.loads(response.content.decode())

    assert response.status_code == 200
    assert content["count"] == 0
    assert all(submission["answers"] == [] for submission in content["results"])


@pytest.mark.django_db
def test_orga_can_see_all_submissions(
    orga_client, slot, accepted_submission, rejected_submission, submission, answer
):
    response = orga_client.get(
        submission.event.api_urls.submissions + "?questions=all", follow=True
    )
    content = json.loads(response.content.decode())

    assert response.status_code == 200
    assert content["count"] == 4
    assert content["results"][0]["title"] == slot.submission.title
    assert len(
        [submission for submission in content["results"] if submission["answers"] == []]
    )
    assert len(
        [submission for submission in content["results"] if submission["answers"] != []]
    )


@pytest.mark.django_db
def test_orga_can_see_all_submissions_wrong_question(
    orga_client, slot, accepted_submission, rejected_submission, submission, answer
):
    response = orga_client.get(
        submission.event.api_urls.submissions + "?questions=1212112", follow=True
    )
    content = json.loads(response.content.decode())

    assert response.status_code == 200
    assert content["count"] == 4
    assert content["results"][0]["title"] == slot.submission.title
    assert not len(
        [submission for submission in content["results"] if submission["answers"] != []]
    )


@pytest.mark.django_db
@pytest.mark.parametrize(
    "is_visible_to_reviewers,is_reviewer,length",
    (
        (True, True, 1),
        (False, True, 0),
        (True, False, 1),
        (False, False, 1),
    ),
)
def test_answer_is_visible_to_reviewers(
    orga_client,
    review_user,
    submission,
    answer,
    event,
    is_visible_to_reviewers,
    is_reviewer,
    length,
):
    if is_reviewer:
        orga_client.force_login(review_user)

    with scope(event=event):
        question = answer.question
        question.is_visible_to_reviewers = is_visible_to_reviewers
        question.save()

    response = orga_client.get(
        submission.event.api_urls.submissions + f"?questions={answer.question_id}",
        follow=True,
    )
    content = json.loads(response.content.decode())

    assert response.status_code == 200
    assert content["count"] == 1
    assert content["results"][0]["title"] == submission.title
    assert len(content["results"][0]["answers"]) == length


@pytest.mark.django_db
def test_orga_can_see_all_submissions_even_nonpublic(
    orga_client, slot, accepted_submission, rejected_submission, submission
):
    submission.event.feature_flags["show_schedule"] = False
    submission.event.save()
    response = orga_client.get(submission.event.api_urls.submissions, follow=True)
    content = json.loads(response.content.decode())

    assert response.status_code == 200
    assert content["count"] == 4
    assert content["results"][0]["title"] == slot.submission.title


@pytest.mark.django_db
def test_only_see_talks_when_a_release_exists(
    orga_client, confirmed_submission, rejected_submission, submission
):
    response = orga_client.get(submission.event.api_urls.talks, follow=True)
    content = json.loads(response.content.decode())
    assert response.status_code == 200
    assert content["count"] == 0


@pytest.mark.django_db
def test_can_only_see_public_talks(
    event, client, slot, accepted_submission, rejected_submission, submission
):
    response = client.get(submission.event.api_urls.talks, follow=True)
    content = json.loads(response.content.decode())

    assert response.status_code == 200
    assert content["count"] == 1
    assert content["results"][0]["title"] == slot.submission.title
    with scope(event=event):
        speaker = slot.submission.speakers.first()
        assert content["results"][0]["speakers"][0]["name"] == speaker.name
        assert (
            content["results"][0]["speakers"][0]["biography"]
            == speaker.event_profile(event).biography
        )


@pytest.mark.django_db
def test_can_only_see_public_talks_if_public_schedule(
    client, slot, accepted_submission, rejected_submission, submission
):
    submission.event.feature_flags["show_schedule"] = False
    submission.event.save()
    response = client.get(submission.event.api_urls.talks, follow=True)
    content = json.loads(response.content.decode())

    assert response.status_code == 200
    assert content["count"] == 0


@pytest.mark.django_db
def test_orga_can_see_all_talks(
    orga_client, slot, accepted_submission, rejected_submission, submission
):
    response = orga_client.get(submission.event.api_urls.talks, follow=True)
    content = json.loads(response.content.decode())

    assert response.status_code == 200
    assert content["count"] == 1
    assert content["results"][0]["title"] == slot.submission.title


@pytest.mark.django_db
def test_orga_can_see_all_talks_even_nonpublic(
    orga_client, slot, accepted_submission, rejected_submission, submission
):
    submission.event.feature_flags["show_schedule"] = False
    submission.event.save()
    response = orga_client.get(submission.event.api_urls.talks, follow=True)
    content = json.loads(response.content.decode())

    assert response.status_code == 200
    assert content["count"] == 1
    assert content["results"][0]["title"] == slot.submission.title


@pytest.mark.django_db
def test_reviewer_cannot_see_speakers_and_anonymised_content(
    orga_client,
    review_user,
    submission,
    event,
):
    with scope(event=event):
        submission.event.active_review_phase.can_see_speaker_names = False
        submission.event.active_review_phase.save()
        submission.anonymised_data = json.dumps({"description": "CENSORED!"})
        submission.save()
    response = orga_client.get(submission.event.api_urls.submissions, follow=True)
    assert response.status_code == 200
    content = json.loads(response.content.decode())
    content = content["results"][0]
    assert len(content["speakers"]) == 1
    assert content["description"] != "CENSORED!"
    assert content["abstract"] == submission.abstract

    orga_client.force_login(review_user)

    response = orga_client.get(submission.event.api_urls.submissions, follow=True)
    assert response.status_code == 200
    content = json.loads(response.content.decode())
    content = content["results"][0]
    assert content["speakers"] == []
    assert content["description"] == "CENSORED!"
    assert content["abstract"] == submission.abstract


@pytest.mark.django_db
def test_cannot_see_tags(client, tag):
    response = client.get(tag.event.api_urls.tags, follow=True)
    assert response.status_code == 401


@pytest.mark.django_db
def test_orga_can_see_tags(client, orga_user_token, tag):
    response = client.get(
        tag.event.api_urls.tags,
        follow=True,
        headers={"Authorization": f"Token {orga_user_token.token}"},
    )
    content = json.loads(response.content.decode())

    assert response.status_code == 200
    assert content["count"] == 1
    assert content["results"][0]["tag"] == tag.tag


@pytest.mark.django_db
def test_orga_can_see_single_tag(client, orga_user_token, tag):
    response = client.get(
        tag.event.api_urls.tags + f"{tag.pk}/",
        follow=True,
        headers={"Authorization": f"Token {orga_user_token.token}"},
    )
    content = json.loads(response.content.decode())

    assert response.status_code == 200
    assert content["tag"] == tag.tag
    assert "is_public" in content
    assert isinstance(content["description"], dict)


@pytest.mark.django_db
def test_orga_can_see_single_tag_locale_override(client, orga_user_token, tag):
    response = client.get(
        tag.event.api_urls.tags + f"{tag.pk}/?locale=en",
        follow=True,
        headers={"Authorization": f"Token {orga_user_token.token}"},
    )
    content = json.loads(response.content.decode())

    assert response.status_code == 200
    assert content["tag"] == tag.tag
    assert "is_public" in content
    assert isinstance(content["description"], str)


@pytest.mark.django_db
def test_orga_can_see_single_legacy_tag(client, orga_user_token, tag):
    from pretalx.api.versions import LEGACY

    response = client.get(
        tag.event.api_urls.tags + f"{tag.pk}/",
        follow=True,
        headers={
            "Authorization": f"Token {orga_user_token.token}",
            "Pretalx-Version": LEGACY,
        },
    )
    content = json.loads(response.content.decode())

    assert response.status_code == 200, response.content.decode()
    assert content["tag"] == tag.tag
    assert "is_public" not in content
    orga_user_token.refresh_from_db()
    assert orga_user_token.version == "LEGACY"

    # now that the token version is saved, we should see the same result without the
    # header
    response = client.get(
        tag.event.api_urls.tags + f"{tag.pk}/",
        follow=True,
        headers={
            "Authorization": f"Token {orga_user_token.token}",
        },
    )
    content = json.loads(response.content.decode())
    assert response.status_code == 200, response.content.decode()
    assert content["tag"] == tag.tag
    assert "is_public" not in content


@pytest.mark.django_db
def test_orga_can_create_tags(client, orga_user_write_token, event):
    response = client.post(
        event.api_urls.tags,
        follow=True,
        data={"tag": "newtesttag", "color": "#00ff00"},
        content_type="application/json",
        headers={
            "Authorization": f"Token {orga_user_write_token.token}",
        },
    )
    assert response.status_code == 201
    with scope(event=event):
        tag = event.tags.get(tag="newtesttag")
        assert tag.logged_actions().filter(action_type="pretalx.tag.create").exists()


@pytest.mark.django_db
def test_orga_cannot_create_tags_readonly_token(client, orga_user_token, event):
    response = client.post(
        event.api_urls.tags,
        follow=True,
        data={"tag": "newtesttag"},
        content_type="application/json",
        headers={
            "Authorization": f"Token {orga_user_token.token}",
            "Content-Type": "application/json",
        },
    )
    assert response.status_code == 403
    with scope(event=event):
        assert not event.tags.filter(tag="newtesttag").exists()
        assert (
            not event.logged_actions().filter(action_type="pretalx.tag.create").exists()
        )


@pytest.mark.django_db
def test_orga_can_update_tags(client, orga_user_write_token, event, tag):
    assert tag.tag != "newtesttag"
    response = client.patch(
        event.api_urls.tags + f"{tag.pk}/",
        follow=True,
        data=json.dumps({"tag": "newtesttag"}),
        headers={
            "Authorization": f"Token {orga_user_write_token.token}",
            "Content-Type": "application/json",
        },
    )
    assert response.status_code == 200
    with scope(event=tag.event):
        tag.refresh_from_db()
        assert tag.tag == "newtesttag"
        assert tag.logged_actions().filter(action_type="pretalx.tag.update").exists()


@pytest.mark.django_db
def test_orga_cannot_update_tags_readonly_token(client, orga_user_token, tag):
    response = client.patch(
        tag.event.api_urls.tags + f"{tag.pk}/",
        follow=True,
        data=json.dumps({"tag": "newtesttag"}),
        headers={
            "Authorization": f"Token {orga_user_token.token}",
            "Content-Type": "application/json",
        },
    )
    assert response.status_code == 403
    with scope(event=tag.event):
        tag.refresh_from_db()
        assert tag.tag != "newtesttag"
        assert (
            not tag.logged_actions().filter(action_type="pretalx.tag.update").exists()
        )


@pytest.mark.django_db
def test_orga_can_delete_tags(client, orga_user_write_token, event, tag):
    assert tag.tag != "newtesttag"
    response = client.delete(
        event.api_urls.tags + f"{tag.pk}/",
        follow=True,
        headers={
            "Authorization": f"Token {orga_user_write_token.token}",
        },
    )
    assert response.status_code == 204
    with scope(event=tag.event):
        assert event.tags.all().count() == 0
        assert event.logged_actions().filter(action_type="pretalx.tag.delete").exists()


@pytest.mark.django_db
def test_orga_cannot_delete_tags_readonly_token(client, orga_user_token, tag):
    response = client.delete(
        tag.event.api_urls.tags + f"{tag.pk}/",
        follow=True,
        headers={"Authorization": f"Token {orga_user_token.token}"},
    )
    assert response.status_code == 403
    with scope(event=tag.event):
        assert tag.event.tags.all().count() == 1


@pytest.mark.django_db
def test_cannot_see_tracks(client, track):
    response = client.get(track.event.api_urls.tracks, follow=True)
    assert response.status_code == 401


@pytest.mark.django_db
def test_can_see_tracks_public_event(client, track, slot):
    with scope(event=track.event):
        track.event.is_public = True
        track.event.save()
    response = client.get(track.event.api_urls.tracks, follow=True)
    content = json.loads(response.content.decode())

    assert response.status_code == 200
    assert content["count"] == 1
    assert content["results"][0]["name"]["en"] == track.name


@pytest.mark.django_db
def test_orga_can_see_tracks(client, orga_user_token, track):
    response = client.get(
        track.event.api_urls.tracks,
        follow=True,
        headers={"Authorization": f"Token {orga_user_token.token}"},
    )
    content = json.loads(response.content.decode())

    assert response.status_code == 200
    assert content["count"] == 1
    assert content["results"][0]["name"]["en"] == track.name


@pytest.mark.django_db
def test_orga_can_see_single_track(client, orga_user_token, track):
    response = client.get(
        track.event.api_urls.tracks + f"{track.pk}/",
        follow=True,
        headers={"Authorization": f"Token {orga_user_token.token}"},
    )
    content = json.loads(response.content.decode())

    assert response.status_code == 200
    assert content["name"]["en"] == track.name
    assert isinstance(content["name"], dict)


@pytest.mark.django_db
def test_orga_can_see_single_track_locale_override(client, orga_user_token, track):
    response = client.get(
        track.event.api_urls.tracks + f"{track.pk}/?locale=en",
        follow=True,
        headers={"Authorization": f"Token {orga_user_token.token}"},
    )
    content = json.loads(response.content.decode())

    assert response.status_code == 200
    assert isinstance(content["name"], str)


@pytest.mark.django_db
def test_no_legacy_track_api(client, orga_user_token, track):
    from pretalx.api.versions import LEGACY

    response = client.get(
        track.event.api_urls.tracks + f"{track.pk}/",
        follow=True,
        headers={
            "Authorization": f"Token {orga_user_token.token}",
            "Pretalx-Version": LEGACY,
        },
    )
    assert response.status_code == 400, response.content.decode()
    assert response.content.decode() == '{"detail": "API version not supported."}'


@pytest.mark.django_db
def test_orga_can_create_tracks(client, orga_user_write_token, event):
    response = client.post(
        event.api_urls.tracks,
        follow=True,
        data={"name": "newtesttrack", "color": "#334455"},
        content_type="application/json",
        headers={
            "Authorization": f"Token {orga_user_write_token.token}",
        },
    )
    assert response.status_code == 201
    with scope(event=event):
        track = event.tracks.get(name="newtesttrack")
        assert (
            track.logged_actions().filter(action_type="pretalx.track.create").exists()
        )


@pytest.mark.django_db
def test_orga_cannot_create_tracks_readonly_token(client, orga_user_token, event):
    response = client.post(
        event.api_urls.tracks,
        follow=True,
        data={"name": "newtesttrack"},
        content_type="application/json",
        headers={
            "Authorization": f"Token {orga_user_token.token}",
        },
    )
    assert response.status_code == 403
    with scope(event=event):
        assert not event.tracks.filter(name="newtesttrack").exists()
        assert (
            not event.logged_actions()
            .filter(action_type="pretalx.track.create")
            .exists()
        )


@pytest.mark.django_db
def test_orga_can_update_tracks(client, orga_user_write_token, event, track):
    assert track.name != "newtesttrack"
    response = client.patch(
        event.api_urls.tracks + f"{track.pk}/",
        follow=True,
        data=json.dumps({"name": "newtesttrack"}),
        headers={
            "Authorization": f"Token {orga_user_write_token.token}",
            "Content-Type": "application/json",
        },
    )
    assert response.status_code == 200
    with scope(event=track.event):
        track.refresh_from_db()
        assert track.name == "newtesttrack"
        assert (
            track.logged_actions().filter(action_type="pretalx.track.update").exists()
        )


@pytest.mark.django_db
def test_orga_cannot_update_tracks_readonly_token(client, orga_user_token, track):
    response = client.patch(
        track.event.api_urls.tracks + f"{track.pk}/",
        follow=True,
        data=json.dumps({"name": "newtesttrack"}),
        headers={
            "Authorization": f"Token {orga_user_token.token}",
            "Content-Type": "application/json",
        },
    )
    assert response.status_code == 403
    with scope(event=track.event):
        track.refresh_from_db()
        assert track.name != "newtesttrack"
        assert (
            not track.logged_actions()
            .filter(action_type="pretalx.track.update")
            .exists()
        )


@pytest.mark.django_db
def test_orga_can_delete_tracks(client, orga_user_write_token, event, track):
    response = client.delete(
        event.api_urls.tracks + f"{track.pk}/",
        follow=True,
        headers={
            "Authorization": f"Token {orga_user_write_token.token}",
        },
    )
    assert response.status_code == 204
    with scope(event=track.event):
        assert event.tracks.all().count() == 0
        assert (
            event.logged_actions().filter(action_type="pretalx.track.delete").exists()
        )


@pytest.mark.django_db
def test_orga_cannot_delete_tracks_readonly_token(client, orga_user_token, track):
    response = client.delete(
        track.event.api_urls.tracks + f"{track.pk}/",
        follow=True,
        headers={"Authorization": f"Token {orga_user_token.token}"},
    )
    assert response.status_code == 403
    with scope(event=track.event):
        assert track.event.tracks.all().count() == 1


@pytest.mark.django_db
def test_submission_type_serializer(submission_type):
    with scope(event=submission_type.event):
        data = SubmissionTypeSerializer(
            submission_type, context={"event": submission_type.event}
        ).data
        assert set(data.keys()) == {
            "id",
            "name",
            "default_duration",
            "deadline",
            "requires_access_code",
        }


@pytest.mark.django_db
def test_cannot_see_submission_types(client, submission_type):
    with scope(event=submission_type.event):
        submission_type.event.is_public = False
        submission_type.event.save()
    response = client.get(submission_type.event.api_urls.submission_types, follow=True)
    assert response.status_code == 401


@pytest.mark.django_db
def test_can_see_submission_types_public_event(client, submission_type, slot):
    response = client.get(submission_type.event.api_urls.submission_types, follow=True)
    content = json.loads(response.content.decode())

    assert response.status_code == 200
    assert content["count"] == 2
    assert content["results"][1]["name"]["en"] == submission_type.name


@pytest.mark.django_db
def test_orga_can_see_submission_types(client, orga_user_token, submission_type):
    response = client.get(
        submission_type.event.api_urls.submission_types,
        follow=True,
        headers={"Authorization": f"Token {orga_user_token.token}"},
    )
    content = json.loads(response.content.decode())

    assert response.status_code == 200
    assert content["count"] == 2
    assert content["results"][1]["name"]["en"] == submission_type.name


@pytest.mark.django_db
def test_orga_can_see_single_submission_type(client, orga_user_token, submission_type):
    response = client.get(
        submission_type.event.api_urls.submission_types + f"{submission_type.pk}/",
        follow=True,
        headers={"Authorization": f"Token {orga_user_token.token}"},
    )
    content = json.loads(response.content.decode())

    assert response.status_code == 200
    assert content["name"]["en"] == submission_type.name
    assert isinstance(content["name"], dict)


@pytest.mark.django_db
def test_orga_can_see_single_submission_type_locale_override(
    client, orga_user_token, submission_type
):
    response = client.get(
        submission_type.event.api_urls.submission_types
        + f"{submission_type.pk}/?locale=en",
        follow=True,
        headers={"Authorization": f"Token {orga_user_token.token}"},
    )
    content = json.loads(response.content.decode())

    assert response.status_code == 200
    assert isinstance(content["name"], str)


@pytest.mark.django_db
def test_no_legacy_submission_type_api(client, orga_user_token, submission_type):
    from pretalx.api.versions import LEGACY

    response = client.get(
        submission_type.event.api_urls.submission_types + f"{submission_type.pk}/",
        follow=True,
        headers={
            "Authorization": f"Token {orga_user_token.token}",
            "Pretalx-Version": LEGACY,
        },
    )
    assert response.status_code == 400, response.content.decode()
    assert response.content.decode() == '{"detail": "API version not supported."}'


@pytest.mark.django_db
def test_orga_can_create_submission_types(client, orga_user_write_token, event):
    response = client.post(
        event.api_urls.submission_types,
        follow=True,
        data={"name": "newtesttype", "default_duration": 45},
        content_type="application/json",
        headers={
            "Authorization": f"Token {orga_user_write_token.token}",
        },
    )
    assert response.status_code == 201
    with scope(event=event):
        submission_type = event.submission_types.get(name="newtesttype")
        assert (
            submission_type.logged_actions()
            .filter(action_type="pretalx.submission_type.create")
            .exists()
        )


@pytest.mark.django_db
def test_orga_cannot_create_submission_types_readonly_token(
    client, orga_user_token, event
):
    response = client.post(
        event.api_urls.submission_types,
        follow=True,
        data={"name": "newtesttype"},
        content_type="application/json",
        headers={
            "Authorization": f"Token {orga_user_token.token}",
        },
    )
    assert response.status_code == 403
    with scope(event=event):
        assert not event.submission_types.filter(name="newtesttype").exists()
        assert (
            not event.logged_actions()
            .filter(action_type="pretalx.submission_type.create")
            .exists()
        )


@pytest.mark.django_db
def test_orga_can_update_submission_types(
    client, orga_user_write_token, event, submission_type
):
    assert submission_type.name != "newtesttype"
    response = client.patch(
        event.api_urls.submission_types + f"{submission_type.pk}/",
        follow=True,
        data=json.dumps({"name": "newtesttype"}),
        headers={
            "Authorization": f"Token {orga_user_write_token.token}",
            "Content-Type": "application/json",
        },
    )
    assert response.status_code == 200
    with scope(event=submission_type.event):
        submission_type.refresh_from_db()
        assert submission_type.name == "newtesttype"
        assert (
            submission_type.logged_actions()
            .filter(action_type="pretalx.submission_type.update")
            .exists()
        )


@pytest.mark.django_db
def test_orga_cannot_update_submission_types_readonly_token(
    client, orga_user_token, submission_type
):
    response = client.patch(
        submission_type.event.api_urls.submission_types + f"{submission_type.pk}/",
        follow=True,
        data=json.dumps({"name": "newtesttype"}),
        headers={
            "Authorization": f"Token {orga_user_token.token}",
            "Content-Type": "application/json",
        },
    )
    assert response.status_code == 403
    with scope(event=submission_type.event):
        submission_type.refresh_from_db()
        assert submission_type.name != "newtesttype"
        assert (
            not submission_type.logged_actions()
            .filter(action_type="pretalx.submission_type.update")
            .exists()
        )


@pytest.mark.django_db
def test_orga_can_delete_submission_types(
    client, orga_user_write_token, event, submission_type
):
    # Create a new submission type because the default one can't be deleted (it's used by the CfP)
    response = client.delete(
        event.api_urls.submission_types + f"{submission_type.pk}/",
        follow=True,
        headers={
            "Authorization": f"Token {orga_user_write_token.token}",
        },
    )
    assert response.status_code == 204
    with scope(event=event):
        assert not event.submission_types.filter(pk=submission_type.pk).exists()
        assert (
            event.logged_actions()
            .filter(action_type="pretalx.submission_type.delete")
            .exists()
        )


@pytest.mark.django_db
def test_orga_cannot_delete_submission_types_readonly_token(
    client, orga_user_token, event, submission_type
):
    # Create a new submission type because the default one can't be deleted (it's used by the CfP)
    response = client.delete(
        event.api_urls.submission_types + f"{submission_type.pk}/",
        follow=True,
        headers={"Authorization": f"Token {orga_user_token.token}"},
    )
    assert response.status_code == 403
    with scope(event=event):
        assert event.submission_types.filter(pk=submission_type.pk).exists()
