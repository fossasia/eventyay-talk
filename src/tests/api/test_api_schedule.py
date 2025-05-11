import json

import pytest
from django_scopes import scope


@pytest.fixture
def schedule_v2(event):
    return event.schedules.create(version="v2.0")


@pytest.fixture
def invisible_slot(slot):
    slot.is_visible = False
    slot.pk = None
    slot.save()
    return slot


@pytest.mark.django_db
def test_user_can_see_schedule(client, slot, event):
    with scope(event=event):
        assert slot.submission.event.schedules.count() == 2
    response = client.get(slot.submission.event.api_urls.schedules, follow=True)
    content = json.loads(response.content.decode())

    assert response.status_code == 200
    assert content["count"] == 1


@pytest.mark.django_db
def test_user_cannot_see_wip_schedule(client, slot, event):
    with scope(event=event):
        assert slot.submission.event.schedules.count() == 2
    response = client.get(slot.submission.event.api_urls.schedules + "wip", follow=True)
    json.loads(response.content.decode())
    assert response.status_code == 404


@pytest.mark.django_db
def test_user_cannot_see_schedule_if_not_public(client, slot, event):
    slot.submission.event.feature_flags["show_schedule"] = False
    slot.submission.event.save()
    with scope(event=event):
        assert slot.submission.event.schedules.count() == 2
    response = client.get(slot.submission.event.api_urls.schedules, follow=True)
    content = json.loads(response.content.decode())

    assert response.status_code == 200
    assert content["count"] == 0


@pytest.mark.django_db
def test_orga_can_see_schedule(client, orga_user_token, slot, event):
    with scope(event=event):
        assert slot.submission.event.schedules.count() == 2
    response = client.get(
        slot.submission.event.api_urls.schedules,
        follow=True,
        headers={"Authorization": f"Token {orga_user_token.token}"},
    )
    content = json.loads(response.content.decode())

    assert response.status_code == 200
    assert content["count"] == 2


@pytest.mark.django_db
def test_orga_can_see_wip_schedule(client, orga_user_token, slot, event):
    with scope(event=event):
        assert slot.submission.event.schedules.count() == 2
    response = client.get(
        slot.submission.event.api_urls.schedules + "wip",
        follow=True,
        headers={"Authorization": f"Token {orga_user_token.token}"},
    )
    json.loads(response.content.decode())
    assert response.status_code == 200


@pytest.mark.django_db
def test_orga_can_see_current_schedule(client, orga_user_token, slot, event):
    with scope(event=event):
        assert slot.submission.event.schedules.count() == 2
    response = client.get(
        slot.submission.event.api_urls.schedules + "latest",
        follow=True,
        headers={"Authorization": f"Token {orga_user_token.token}"},
    )
    json.loads(response.content.decode())
    assert response.status_code == 200
    with scope(event=event):
        assert slot.submission.title in response.content.decode()


@pytest.mark.django_db
def test_orga_cannot_see_schedule_even_if_not_public(
    client, orga_user_token, slot, event
):
    slot.submission.event.feature_flags["show_schedule"] = False
    slot.submission.event.save()
    with scope(event=event):
        assert slot.submission.event.schedules.count() == 2
    response = client.get(
        slot.submission.event.api_urls.schedules,
        follow=True,
        headers={"Authorization": f"Token {orga_user_token.token}"},
    )
    content = json.loads(response.content.decode())

    assert response.status_code == 200
    assert content["count"] == 2


@pytest.mark.django_db
def test_user_can_download_slot_ical(client, slot, event):
    url = event.api_urls.slots + f"{slot.pk}/ical/"
    response = client.get(url, follow=True)

    assert response.status_code == 200
    assert response.headers["Content-Type"] == "text/calendar"
    expected_filename = (
        f'attachment; filename="{event.slug}-{slot.submission.code}.ics"'
    )
    assert response.headers["Content-Disposition"] == expected_filename
    content = response.content.decode()
    assert "BEGIN:VCALENDAR" in content
    assert f"{slot.submission.code}" in content


@pytest.mark.django_db
def test_user_cannot_download_slot_ical_if_slot_not_visible(client, slot, event):
    with scope(event=event):
        slot.is_visible = False
        slot.save()

    url = event.api_urls.slots + f"{slot.pk}/ical/"
    response = client.get(url, follow=True)
    assert response.status_code == 404


@pytest.mark.django_db
def test_user_cannot_download_slot_ical_if_schedule_not_public(client, slot, event):
    event = slot.submission.event
    with scope(event=event):
        event.is_public = True
        event.feature_flags["show_schedule"] = False
        event.save()

    url = event.api_urls.slots + f"{slot.pk}/ical/"
    response = client.get(url, follow=True)
    assert response.status_code == 401


@pytest.mark.django_db
def test_user_cannot_download_slot_ical_if_event_not_public(client, slot):
    event = slot.submission.event
    with scope(event=event):
        event.is_public = False
        event.save()

    url = event.api_urls.slots + f"{slot.pk}/ical/"
    response = client.get(url, follow=True)
    assert response.status_code == 401


@pytest.mark.django_db
def test_download_slot_ical_slot_without_submission(client, event, room, slot):
    with scope(event=event):
        slot.submission = None
        slot.save()
    url = event.api_urls.slots + f"{slot.pk}/ical/"
    response = client.get(url, follow=True)
    assert response.status_code == 401


@pytest.mark.django_db
def test_list_slots_anonymous_event_not_public(client, event, slot):
    event.is_public = False
    event.save()
    response = client.get(event.api_urls.slots, follow=True)
    assert response.status_code == 401


@pytest.mark.django_db
def test_list_slots_anonymous_schedule_not_public(client, event, slot):
    event.is_public = True
    event.feature_flags["show_schedule"] = False
    event.save()
    response = client.get(event.api_urls.slots, follow=True)
    assert response.status_code == 401


@pytest.mark.django_db
def test_list_slots_anonymous_schedule_public_current_schedule_only(
    client, event, slot
):
    with scope(event=event):
        code = slot.submission.code
    response = client.get(event.api_urls.slots, follow=True)
    content = json.loads(response.content.decode())
    assert response.status_code == 200
    assert content["count"] == 1
    assert content["results"][0]["id"] == slot.pk
    assert "is_visible" not in content["results"][0]
    assert content["results"][0]["submission"] == code


@pytest.mark.django_db
def test_list_slots_anonymous_schedule_public_only_visible(
    client, event, slot, invisible_slot
):
    with scope(event=event):
        pk = event.current_schedule.talks.filter(submission=slot.submission).first().pk
    response = client.get(event.api_urls.slots, follow=True)
    content = json.loads(response.content.decode())
    assert response.status_code == 200
    assert content["count"] == 1
    assert content["results"][0]["id"] == pk


@pytest.mark.django_db
def test_list_slots_orga_sees_slots_in_current_schedule_by_default(
    client, orga_user_token, event, slot, invisible_slot
):
    with scope(event=event):
        wip_pk = event.wip_schedule.talks.filter(submission=slot.submission).first().pk
    response = client.get(
        event.api_urls.slots,
        follow=True,
        headers={"Authorization": f"Token {orga_user_token.token}"},
    )
    content = json.loads(response.content.decode())
    assert response.status_code == 200
    assert content["count"] == 2
    slot_ids = {r["id"] for r in content["results"]}
    assert slot.pk in slot_ids
    assert invisible_slot.pk in slot_ids
    assert wip_pk not in slot_ids


@pytest.mark.django_db
def test_list_slots_orga_can_filter_by_schedule_pk(
    client, orga_user_token, event, slot
):
    with scope(event=event):
        event.wip_schedule.freeze("v2323")
        code = slot.submission.code
    response = client.get(
        f"{event.api_urls.slots}?schedule={slot.schedule_id}",
        follow=True,
        headers={"Authorization": f"Token {orga_user_token.token}"},
    )
    content = json.loads(response.content.decode())
    assert response.status_code == 200, content
    assert content["count"] == 1
    assert content["results"][0]["id"] == slot.pk
    response = client.get(
        f"{event.api_urls.slots}?submission={code}",
        follow=True,
        headers={"Authorization": f"Token {orga_user_token.token}"},
    )
    content = json.loads(response.content.decode())
    assert response.status_code == 200
    assert content["count"] == 3


# Retrieve Tests
@pytest.mark.django_db
def test_retrieve_slot_anonymous_not_visible(client, event, invisible_slot):
    response = client.get(event.api_urls.slots + f"{invisible_slot.pk}/", follow=True)
    assert response.status_code == 404


@pytest.mark.django_db
def test_retrieve_slot_anonymous_visible_schedule_public(client, event, slot):
    with scope(event=event):
        code = slot.submission.code
    response = client.get(event.api_urls.slots + f"{slot.pk}/", follow=True)
    assert response.status_code == 200
    content = json.loads(response.content.decode())
    assert content["id"] == slot.pk
    assert "is_visible" not in content
    assert content["submission"] == code


@pytest.mark.django_db
def test_retrieve_slot_anonymous_schedule_not_public(client, event, slot):
    event.is_public = True
    event.feature_flags["show_schedule"] = False
    event.save()
    slot.is_visible = True
    slot.save()
    response = client.get(event.api_urls.slots + f"{slot.pk}/", follow=True)
    assert response.status_code == 401


@pytest.mark.django_db
def test_retrieve_slot_orga_can_see_invisible_slot(
    client, orga_user_token, event, invisible_slot
):
    response = client.get(
        event.api_urls.slots + f"{invisible_slot.pk}/",
        follow=True,
        headers={"Authorization": f"Token {orga_user_token.token}"},
    )
    assert response.status_code == 200
    content = json.loads(response.content.decode())
    assert content["id"] == invisible_slot.pk


@pytest.mark.django_db
def test_retrieve_slot_nonexistent(client, event, slot):
    response = client.get(event.api_urls.slots + "99999/", follow=True)
    assert response.status_code == 404


# Update Tests
@pytest.mark.django_db
def test_update_slot_anonymous(client, event, slot):
    response = client.patch(
        event.api_urls.slots + f"{slot.pk}/",
        data=json.dumps({"is_visible": False}),
        content_type="application/json",
    )
    assert response.status_code == 401


@pytest.mark.django_db
def test_update_slot_orga_readonly_token(client, event, slot, orga_user_token):
    initial_visibility = slot.is_visible
    response = client.patch(
        event.api_urls.slots + f"{slot.pk}/",
        data=json.dumps({"is_visible": not initial_visibility}),
        content_type="application/json",
        headers={"Authorization": f"Token {orga_user_token.token}"},
    )
    assert response.status_code == 403
    with scope(event=event):
        slot.refresh_from_db()
        assert slot.is_visible == initial_visibility


@pytest.mark.django_db
def test_update_slot_orga_write_token_cannot_change_visibility(
    client, event, slot, orga_user_write_token
):
    with scope(event=event):
        wip_slot = event.wip_schedule.talks.filter(submission=slot.submission).first()
    initial_visibility = wip_slot.is_visible
    response = client.patch(
        event.api_urls.slots + f"{wip_slot.pk}/",
        data=json.dumps({"is_visible": not initial_visibility}),
        content_type="application/json",
        headers={"Authorization": f"Token {orga_user_write_token.token}"},
    )
    assert response.status_code == 200
    with scope(event=event):
        wip_slot.refresh_from_db()
        assert wip_slot.is_visible == initial_visibility


@pytest.mark.django_db
def test_update_slot_orga_write_token_change_room(
    client, event, slot, orga_user_write_token, room, other_room
):
    with scope(event=event):
        wip_slot = event.wip_schedule.talks.filter(submission=slot.submission).first()
        assert wip_slot.room == room
    response = client.patch(
        event.api_urls.slots + f"{wip_slot.pk}/",
        data=json.dumps({"room": other_room.pk}),
        content_type="application/json",
        headers={"Authorization": f"Token {orga_user_write_token.token}"},
    )
    assert response.status_code == 200
    with scope(event=event):
        wip_slot.refresh_from_db()
        assert wip_slot.room == other_room


@pytest.mark.django_db
def test_update_slot_orga_write_token_clear_room(
    client, event, slot, orga_user_write_token, room
):
    with scope(event=event):
        wip_slot = event.wip_schedule.talks.filter(submission=slot.submission).first()
        assert wip_slot.room == room
    response = client.patch(
        event.api_urls.slots + f"{wip_slot.pk}/",
        data=json.dumps({"room": None}),
        content_type="application/json",
        headers={"Authorization": f"Token {orga_user_write_token.token}"},
    )
    assert response.status_code == 200
    with scope(event=event):
        wip_slot.refresh_from_db()
        assert not wip_slot.room


@pytest.mark.django_db
def test_update_slot_orga_write_token_change_room_non_wip(
    client, event, slot, other_room, orga_user_write_token
):
    assert slot.room != other_room
    response = client.patch(
        event.api_urls.slots + f"{slot.pk}/",
        data=json.dumps({"room": other_room.pk}),
        content_type="application/json",
        headers={"Authorization": f"Token {orga_user_write_token.token}"},
    )
    assert response.status_code == 403


@pytest.mark.django_db
def test_talk_slot_expand_parameters(client, orga_user_token, event, slot):
    url = event.api_urls.slots + f"{slot.pk}/"
    base_headers = {"Authorization": f"Token {orga_user_token.token}"}

    with scope(event=event):
        submission_code = slot.submission.code
        room_pk = slot.room.pk
        speaker = slot.submission.speakers.first().code

    # 1. No expand
    response = client.get(url, headers=base_headers)
    assert response.status_code == 200
    content = json.loads(response.content.decode())
    assert content["submission"] == submission_code
    assert content["room"] == room_pk
    assert content["schedule"] == slot.schedule_id

    response = client.get(
        url + "?expand=room,schedule,submission,submission.speakers",
        headers=base_headers,
    )
    assert response.status_code == 200
    content = json.loads(response.content.decode())

    assert isinstance(content["room"], dict)
    assert content["room"]["id"] == room_pk
    assert content["room"]["name"]["en"] == slot.room.name  # Example of expanded field

    assert isinstance(content["submission"], dict)
    assert content["submission"]["code"] == submission_code
    assert isinstance(content["submission"]["speakers"], list)

    assert isinstance(content["submission"]["speakers"], list)
    speaker_data = content["submission"]["speakers"][0]
    assert speaker_data["code"] == speaker
