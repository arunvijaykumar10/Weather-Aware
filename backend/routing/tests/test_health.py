import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient


@pytest.mark.django_db
def test_health_check_endpoint():
    client = APIClient()
    url = reverse('health-check')
    response = client.get(url)

    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {
        "status": "healthy",
        "service": "spotter-weather-aware-routing-backend",
    }


def test_cors_headers_on_health_endpoint():
    client = APIClient()
    response = client.get('/api/health/', HTTP_ORIGIN='http://localhost:5173')

    assert response.status_code == status.HTTP_200_OK
    assert response.headers.get('Access-Control-Allow-Origin') == 'http://localhost:5173'
