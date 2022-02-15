from collections import namedtuple
import logging
import random

from django.db import models
from django.http import Http404, HttpRequest
from django.shortcuts import get_object_or_404, redirect, render, HttpResponseRedirect
import tweepy

from fantasy_racing.utils import twitter

from .models import FAQ, Race, RaceDriver, RacePick, Schedule, TwitterUser


logger = logging.getLogger(__name__)


def index(request):
    race = Race.objects.current()
    return render(request, 'index.html', {
        'race': race,
        'headline': random.choice([
            'The fantasy racing game where you don\'t get to pick who wins.',
            'Why spend money on fantasy racing?',
            'Spinning a prize wheel meets fantasy Formula 1 racing.',
            'Fantasy racing that\'s not considered gambling.',
            'Fantasy racing crossed with a random number generator.',
        ])
    })


def about(request):
    return render(request, 'about.html', {
        'faqs': FAQ.objects.all(),
        'title': 'About'
    })


def schedule(request, year=None):
    schedule = Schedule.objects.last() if year is None else get_object_or_404(Schedule, year=year)
    years = Schedule.objects.values_list('year', flat=True)
    return render(request, 'schedule.html', {
        'schedule': schedule, 'years': years, 'title': f'{schedule.year} Schedule'
    })


def picks(request, id=None):
    race = Race.objects.current() if id is None else get_object_or_404(Race, id=id)
    if not race:
        raise Http404
    
    picks = RacePick.objects.filter(race=race).all()
    return render(request, 'picks.html', {'race': race, 'title': f'{race} Picks', 'picks': picks})


def standings(request, year=None):
    schedule = Schedule.objects.last() if year is None else get_object_or_404(Schedule, year=year)
    standings = TwitterUser.objects \
                           .participating_users(schedule=schedule) \
                           .details(schedule=schedule) \
                           .order_by('-points')
    leader_points = -1 * standings.first().points
    return render(request, 'standings.html', {
        'schedule': schedule, 'title': f'{schedule.year} Standings',
        'standings': standings, 'leader_points': leader_points
    })


def player(request, username):
    twitter_user = TwitterUser.objects.filter(username=username).details().first()
    if not twitter_user:
        raise Http404
    user_seasons = list(filter(lambda season: season.starts > 0, [
        TwitterUser.objects.filter(username=username).annotate(year=models.Value(sched.year)).details(schedule=sched).first()
        for sched in Schedule.objects.all().order_by('-year')
    ]))
    return render(request, 'player.html', {
        'user': twitter_user, 'title': f'{twitter_user} Career', 'seasons': user_seasons
    })


def player_season(request, username: str, year: int):
    schedule = get_object_or_404(Schedule, year=year)
    twitter_user = TwitterUser.objects.filter(username=username).details(schedule=schedule).first()
    user_seasons = list(filter(lambda season: season.starts > 0, [
        TwitterUser.objects.filter(username=username).with_start_count(schedule=schedule).annotate(year=models.Value(sched.year)).first()
        for sched in Schedule.objects.all().order_by('-year')
    ]))
    picks = RacePick.objects.filter(user=twitter_user, race__schedule=schedule).all()
    return render(request, 'player.html', {
        'user': twitter_user, 'seasons': user_seasons, 'year': year,
        'picks': picks, 'title': f'{twitter_user} {year} Schedule',
    })


def players(request):
    users = TwitterUser.objects \
                       .details() \
                       .order_by('-starts', 'avg_finish')
    return render(request, 'players.html', {'users': users, 'title': 'Players'})


def statistics(request):
    SingleStat = namedtuple('SingleStat', field_names=('title', 'value'))
    common_picks = RaceDriver.objects.annotate(num_picks=models.Count('picks')).order_by('-num_picks')[:25]
    most_wins = TwitterUser.objects \
                           .annotate(num_wins=models.Count('picks', filter=models.Q(picks__result__position=1))) \
                           .order_by('-num_wins')

    return render(request, 'statistics.html', {
        'single_stats': [
            SingleStat(title='Total Players', value=TwitterUser.objects.count()),
            SingleStat(title='Total Picks', value=RacePick.objects.count()),
            SingleStat(title='Most Common Pick', value=common_picks.first().last_name),
            SingleStat(title='Winning Picks', value=RacePick.objects.filter(result__position=1).count()),
            SingleStat(title='Total Races', value=Race.objects.viewable().count()),
            SingleStat(
                title='Average Finish',
                value=RacePick.objects.filter(result__isnull=False) \
                                      .aggregate(res=models.Avg('result__position'))['res']
            ),
        ],
        'starts': TwitterUser.objects.with_start_count().order_by('-starts')[:25],
        'common_picks': common_picks,
        'most_wins': most_wins,
        'title': 'Statistics'
    })


def play(request: HttpRequest):
    oauth = twitter.get_oauth_client()
    auth_url = oauth.get_authorization_url(signin_with_twitter=True)
    response = HttpResponseRedirect(auth_url)
    request.session['request_token'] = oauth.request_token
    return response


def pick(request: HttpRequest):
    race = Race.objects.current()
    if not race:
        raise Http404

    verifier = request.GET.get('oauth_verifier')
    oauth = twitter.get_oauth_client()
    token = request.session.get('request_token')
    if not (token and verifier):
        return redirect('index')

	# remove the request token now we don't need it
    request.session.delete('request_token')
    oauth.request_token = token

    try:
        access_token, access_token_secret = oauth.get_access_token(verifier)
    except tweepy.TweepyException as e:
        # If people refresh the page, then we just send them to the race page
        if '401' in str(e):
            return redirect('race_id', id=race.id)
        else:
            raise e

    client = twitter.get_client(access_token, access_token_secret)
    try:
        user_response = client.get_me(user_fields=['profile_image_url', 'username', 'id', 'name'])
        user = user_response.data
    except tweepy.Forbidden as e:
        logger.exception('unable to get user info: %s', e.response.json())
        raise e
    
    twitter_user, created = TwitterUser.objects.get_or_create(id=user.id, defaults=dict(
        username=user.username, name=user.name, profile_img=user.profile_image_url,
    ))
    if created:
        logger.info('%s just joined for the first time!', twitter_user)

    random_driver: RaceDriver = RaceDriver.objects.random()
    pick, created = RacePick.objects.get_or_create(user=twitter_user, race=race, defaults=dict(
        driver=random_driver,
        tweet_id=1490491780520943620
    ))
    if not created:
        logger.info('Created %s', pick)

    context = {'race': race, 'user': twitter_user, 'pick': pick, 'created': created, 'title': 'Pick'}
    return render(request, 'pick.html', context)