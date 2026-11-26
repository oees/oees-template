from http import HTTPStatus

import pytest
from django.test import Client

pytestmark = pytest.mark.django_db


def test_home_is_a_full_page_in_spanish_by_default(client: Client) -> None:
    response = client.get("/")

    body = response.content.decode()
    assert response.status_code == HTTPStatus.OK
    assert '<html lang="es">' in body
    assert "<h1>El titular principal de la página</h1>" in body


def test_home_follows_the_visitor_language(client: Client) -> None:
    response = client.get("/", headers={"Accept-Language": "en"})

    body = response.content.decode()
    assert '<html lang="en">' in body
    assert "<h1>Your main headline goes here</h1>" in body


def test_unknown_page_gets_the_site_404_page(client: Client) -> None:
    response = client.get("/esta-pagina-no-existe/")

    assert response.status_code == HTTPStatus.NOT_FOUND
    assert "No encontramos esta página" in response.content.decode()
