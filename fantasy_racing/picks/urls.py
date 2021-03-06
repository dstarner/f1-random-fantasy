from django.urls import path

from . import views


urlpatterns = [
    path('about', views.about, name='about'),
    path('schedule/<int:year>', views.schedule, name='schedule_year'),
    path('schedule', views.schedule, name='schedule'),

    path('standings/<int:year>', views.standings, name='standing_year'),
    path('standings', views.standings, name='standings'),

    path('picks/<int:id>', views.picks, name='race_id'),
    path('picks', views.picks, name='race'),
    path('pick', views.pick, name='pick'),
    path('play', views.play, name='play'),

    path('player/<str:username>', views.player, name='player'),
    path('player/<str:username>/<int:year>', views.player_season, name='player_season'),
    path('players', views.players, name='players'),

    path('stats', views.statistics, name='statistics'),

    path('', views.index, name='index'),
]