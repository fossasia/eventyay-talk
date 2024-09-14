from urllib.parse import urlparse

import bs4
import pytest
from django.conf import settings
from django.http.request import QueryDict


@pytest.mark.django_db
def test_no_crash_on_incorrect_event(client, event):
    response = client.get(
        f"/{event.slug}typoe/",
    )
    assert response.status_code == 404


@pytest.mark.django_db
def test_no_crash_on_incorrect_event_for_orga(orga_client, event):
    response = orga_client.get(
        f"/{event.slug}typoe/",
    )
    assert response.status_code == 404


@pytest.mark.django_db
def test_event_startpage_query_string_handling(client, event, access_code):
    """The link to the CfP page should contain the query parameters given in
    the request URL."""
    params_dict = QueryDict(
        f"track=academic&submission_type=academic_talk&access_code={access_code.code}"
    )
    base_path = settings.BASE_PATH
    response = client.get(
        base_path + f"{event.slug}/?{params_dict}",
    )
    assert response.status_code == 200
    doc = bs4.BeautifulSoup(response.rendered_content, "lxml")
    info_btns = doc.select("a.btn-info")
    hrefs = [i.get("href") for i in info_btns]
    assert len(hrefs) > 0
    url_parts = [urlparse(h) for h in hrefs]
    paths = [u.path for u in url_parts]
    dest_path = settings.BASE_PATH + f"{event.slug}/cfp"
    assert dest_path in paths
    cfp_idx = paths.index(dest_path)
    # Comparing the strings only is not sufficient because the order of dictionaries is different
    # between different versions of Python.
    q = QueryDict(url_parts[cfp_idx].query)
    assert q.get("track") == params_dict.get("academic")
    assert q.get("submission_type") == params_dict.get("academic_talk")


@pytest.mark.django_db
def test_event_cfp_query_string_handling(client, event):
    """The link to the submission form should contain the query parameters
    given in the request URL."""
    params_dict = QueryDict("track=academic&submission_type=academic_talk")
    base_path = settings.BASE_PATH
    response = client.get(
        base_path + f"{event.slug}/cfp?{params_dict}",
    )
    assert response.status_code == 200
    doc = bs4.BeautifulSoup(response.rendered_content, "lxml")
    info_btn = doc.select("a.btn-success")[0]
    href = info_btn.get("href")
    assert href is not None
    url_parts = urlparse(href)
    q = QueryDict(url_parts.query)
    assert url_parts.path.endswith("/submit/") is True
    assert q.get("track") == params_dict.get("academic")
    assert q.get("submission_type") == params_dict.get("academic_talk")


@pytest.mark.django_db
def test_no_crash_on_root_view(client, event, other_event):
    other_event.is_public = False
    other_event.save()
    base_path = settings.BASE_PATH
    response = client.get(base_path)
    content = response.content.decode()
    assert response.status_code == 200
    assert event.slug in content
    assert other_event.slug not in content


@pytest.mark.django_db
def test_no_crash_on_root_view_as_organiser(orga_client, event, other_event):
    other_event.is_public = False
    other_event.save()
    response = orga_client.get(settings.BASE_PATH)
    content = response.content.decode()
    assert response.status_code == 200
    assert event.slug in content
    assert other_event.slug not in content


@pytest.mark.django_db
def test_no_crash_on_robots_txt(client):
    response = client.get(settings.BASE_PATH + "robots.txt")
    assert response.status_code == 200


@pytest.mark.parametrize(
    "url,expected",
    (
        ("/talk/400", 400),
        ("/talk/403", 403),
        ("/talk/403/csrf", 403),
        ("/talk/404", 404),
        ("/talk/500", 500),
    ),
)
@pytest.mark.django_db
def test_example_error_views(client, url, expected):
    response = client.get(url)
    assert response.status_code == expected
