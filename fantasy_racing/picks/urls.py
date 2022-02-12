from django.urls import path

from . import views


urlpatterns = [
    path('about', views.about, name='about'),
    path('schedule/<int:year>', views.schedule, name='schedule_year'),
    path('schedule', views.schedule, name='schedule'),
    path('picks/<int:id>', views.picks, name='race_id'),
    path('picks', views.picks, name='race'),
    path('play', views.play, name='play'),
    path('', views.index, name='index'),
]