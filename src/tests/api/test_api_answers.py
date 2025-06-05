import json

import pytest
from django_scopes import scope

from pretalx.submission.models import Answer


@pytest.mark.django_db
@pytest.mark.parametrize("is_public", (True, False))
def test_answers_not_visible_by_default(client, answer, schedule, is_public):
    with scope(event=answer.event):
        answer.question.is_public = is_public
        answer.question.save()
    response = client.get(answer.event.api_urls.answers, follow=True)
    content = json.loads(response.content.decode())
    assert response.status_code == 200
    assert bool(len(content["results"])) is is_public


@pytest.mark.django_db
def test_organizer_can_see_answer(orga_client, answer):
    response = orga_client.get(answer.event.api_urls.answers, follow=True)
    content = json.loads(response.content.decode())
    assert response.status_code == 200
    assert len(content["results"]) == 1
    assert content["results"][0]["id"] == answer.id


@pytest.mark.django_db
@pytest.mark.parametrize("is_visible", (True, False))
def test_answers_not_visible_by_default_to_reviewers(review_client, answer, is_visible):
    with scope(event=answer.event):
        answer.question.is_visible_to_reviewers = is_visible
        answer.question.save()
    response = review_client.get(answer.question.event.api_urls.answers, follow=True)
    content = json.loads(response.content.decode())
    assert response.status_code == 200
    assert bool(len(content["results"])) is is_visible


@pytest.mark.django_db
def test_organizer_can_create_answer(event, orga_client, question, submission, speaker):
    with scope(event=event):
        count = Answer.objects.filter(question__event=event).count()
    response = orga_client.post(
        event.api_urls.answers,
        {
            "question": question.id,
            "submission": submission.code,
            "person": speaker.code,
            "answer": "Tralalalala",
        },
    )
    assert response.status_code == 201, response.content.decode()
    with scope(event=event):
        assert Answer.objects.filter(question__event=event).count() == count + 1
        answer = Answer.objects.filter(question__event=event).first()
        assert answer.answer == "Tralalalala"


@pytest.mark.django_db
def test_duplicate_answer_updates_existing_answer(
    event, orga_client, question, submission, speaker, answer
):
    with scope(event=event):
        count = Answer.objects.filter(question__event=event).count()
        response = orga_client.post(
            event.api_urls.answers,
            {
                "question": answer.question_id,
                "submission": answer.submission.code,
                "person": "",
                "answer": "Tralalalala",
            },
        )
    assert response.status_code == 201, response.content.decode()
    with scope(event=event):
        assert Answer.objects.filter(question__event=event).count() == count
        answer = Answer.objects.filter(question__event=event).first()
        assert answer.answer == "Tralalalala"


@pytest.mark.django_db
def test_organizer_can_edit_answers(event, orga_client, answer):
    response = orga_client.patch(
        event.api_urls.answers + f"{answer.pk}/",
        {"answer": "ohno.png"},
        content_type="application/json",
    )
    assert response.status_code == 200, response.content.decode()
    with scope(event=event):
        answer.refresh_from_db()
        assert answer.answer == "ohno.png"


@pytest.mark.django_db
def test_reviewer_cannot_create_answer(
    event, review_client, question, submission, speaker
):
    with scope(event=event):
        count = Answer.objects.filter(question__event=event).count()
    response = review_client.post(
        event.api_urls.answers,
        {
            "question": question.id,
            "submission": submission.code,
            "person": speaker.code,
            "answer": "Tralalalala",
        },
    )
    assert response.status_code == 403, response.content.decode()
    with scope(event=event):
        assert Answer.objects.filter(question__event=event).count() == count


@pytest.mark.django_db
def test_reviewer_cannot_edit_answer(event, review_client, answer):
    response = review_client.patch(
        event.api_urls.answers + f"{answer.pk}/",
        {"answer": "ohno.png"},
        content_type="application/json",
    )
    assert response.status_code == 403, response.content.decode()
    with scope(event=event):
        answer.refresh_from_db()
        assert answer.answer != "ohno.png"


@pytest.mark.django_db
@pytest.mark.parametrize("required_field", ("answer", "question"))
def test_fields_required_on_create(event, orga_client, required_field):
    response = orga_client.post(
        event.api_urls.answers,
        {},
        content_type="application/json",
    )
    assert response.data.get(required_field)[0] == "This field is required."
    assert response.status_code == 400, response.content.decode()


@pytest.mark.django_db
@pytest.mark.parametrize("required_field", ("answer", "question"))
def test_fields_required_on_update(event, orga_client, answer, required_field):
    response = orga_client.put(
        event.api_urls.answers + f"{answer.pk}/",
        {},
        content_type="application/json",
    )
    assert response.data.get(required_field)[0] == "This field is required."
    assert response.status_code == 400, response.content.decode()


@pytest.mark.django_db
@pytest.mark.parametrize(
    "is_detail, method",
    (
        (False, "post"),
        (True, "put"),
        (True, "patch"),
    ),
)
def test_field_question_may_not_be_null(event, orga_client, answer, is_detail, method):
    url = event.api_urls.answers
    if is_detail:
        url += f"{answer.pk}/"

    response = getattr(orga_client, method)(
        url, {"question": ""}, content_type="application/json"
    )
    assert response.data.get("question")[0] == "This field may not be null."
    assert response.status_code == 400, response.content.decode()


@pytest.mark.django_db
@pytest.mark.parametrize(
    "is_detail, method",
    (
        (False, "post"),
        (True, "put"),
        (True, "patch"),
    ),
)
def test_field_answer_may_not_be_blank(event, orga_client, answer, is_detail, method):
    url = event.api_urls.answers
    if is_detail:
        url += f"{answer.pk}/"

    response = getattr(orga_client, method)(
        url, {"answer": ""}, content_type="application/json"
    )
    assert response.data.get("answer")[0] == "This field may not be blank."
    assert response.status_code == 400, response.content.decode()


@pytest.mark.django_db
@pytest.mark.parametrize(
    "is_detail, method",
    (
        (False, "post"),
        (True, "put"),
        (True, "patch"),
    ),
)
def test_field_question_must_be_valid_pk(event, orga_client, answer, is_detail, method):
    url = event.api_urls.answers
    if is_detail:
        url += f"{answer.pk}/"

    response = getattr(orga_client, method)(
        url, {"question": "invalid_pk"}, content_type="application/json"
    )
    assert (
        response.data.get("question")[0]
        == "Incorrect type. Expected pk value, received str."
    )
    assert response.status_code == 400, response.content.decode()


@pytest.mark.django_db
@pytest.mark.parametrize(
    "is_detail, method",
    (
        (False, "post"),
        (True, "put"),
        (True, "patch"),
    ),
)
def test_field_review_must_be_valid_pk(event, orga_client, answer, is_detail, method):
    url = event.api_urls.answers
    if is_detail:
        url += f"{answer.pk}/"

    response = getattr(orga_client, method)(
        url, {"review": "invalid_pk"}, content_type="application/json"
    )
    assert (
        response.data.get("review")[0]
        == "Incorrect type. Expected pk value, received str."
    )
    assert response.status_code == 400, response.content.decode()


@pytest.mark.django_db
@pytest.mark.parametrize(
    "is_detail, method",
    (
        (False, "post"),
        (True, "put"),
        (True, "patch"),
    ),
)
def test_objects_do_not_exist(event, orga_client, answer, is_detail, method):
    url = event.api_urls.answers
    if is_detail:
        url += f"{answer.pk}/"

    response = getattr(orga_client, method)(
        url, {"review": 5, "question": 4}, content_type="application/json"
    )
    assert response.data.get("review")[0] == 'Invalid pk "5" - object does not exist.'
    assert response.data.get("question")[0] == 'Invalid pk "4" - object does not exist.'
    assert response.status_code == 400, response.content.decode()
