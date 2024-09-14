import json

import pytest
from django.conf import settings


@pytest.mark.django_db
def test_api_user_endpoint(orga_client, room):
    base_path = settings.BASE_PATH
    response = orga_client.get(base_path + "api/me", follow=True)
    assert response.status_code == 200
    content = json.loads(response.content.decode())
    assert set(content.keys()) == {"name", "email", "locale", "timezone"}
