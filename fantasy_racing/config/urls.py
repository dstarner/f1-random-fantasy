"""f1_random_fantasy_racing URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.shortcuts import render
from django.urls import path

from fantasy_racing.picks import urls as picks_urls


def handler404(request, exception=None):
    response = render(request,'404.html')
    response.status_code = 404
    return response


def handler500(request, exception=None):
    response = render(request,'500.html')
    response.status_code = 500
    return response


urlpatterns = [
    path('admin/', admin.site.urls),
    path('_404', handler404, name='404'),
    path('_500', handler500, name='500'),
] + picks_urls.urlpatterns
