"""Public content pages: one template under pages/ and one URL in urls.py each."""

from django.http import HttpRequest, HttpResponse
from django.shortcuts import render


def home(request: HttpRequest) -> HttpResponse:
    return render(request, "pages/home.html")
