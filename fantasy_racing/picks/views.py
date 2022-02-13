from collections import namedtuple
import logging
import random

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
    })


def schedule(request, year=None):
    schedule = Schedule.objects.last() if year is None else get_object_or_404(Schedule, year=year)
    years = Schedule.objects.values_list('year', flat=True)
    return render(request, 'schedule.html', {'schedule': schedule, 'years': years})


def picks(request, id=None):
    race = Race.objects.current() if id is None else get_object_or_404(Race, id=id)
    if not race:
        raise Http404
    
    picks = RacePick.objects.filter(race=race).all()
    return render(request, 'picks.html', {'race': race, 'title': race.track, 'picks': picks})


def standings(request, year=None):
    schedule = Schedule.objects.last() if year is None else get_object_or_404(Schedule, year=year)
    return render(request, 'standings.html', {'schedule': schedule, 'title': f'{schedule.year} Standings'})


def player(request, username):
    twitter_user = get_object_or_404(TwitterUser, username=username)
    return render(request, 'player.html', {'user': twitter_user})


def players(request):
    users = TwitterUser.objects.all()
    return render(request, 'players.html', {'users': users})


def statistics(request):
    SingleStat = namedtuple('SingleStat', field_names=('title', 'value'))
    return render(request, 'statistics.html', {
        'single_stats': [
            SingleStat(title='Total Players', value=TwitterUser.objects.count()),
            SingleStat(title='Total Picks', value=RacePick.objects.count()),
            SingleStat(title='Most Common Pick', value='#-1'),
            SingleStat(title='Winning Picks', value='-1'),
            SingleStat(title='Total Races', value=Race.objects.viewable().count()),
            SingleStat(title='Average Finish', value='-1.0'),
        ]
    })


def play(request: HttpRequest):
    oauth = twitter.get_oauth_client()
    auth_url = oauth.get_authorization_url(signin_with_twitter=True)
    response = HttpResponseRedirect(auth_url)
    request.session['request_token'] = oauth.request_token
    return response


def pick(request: HttpRequest):
    verifier = request.GET.get('oauth_verifier')
    oauth = twitter.get_oauth_client()
    token = request.session.get('request_token')
    if not (token and verifier):
        return redirect('index')

	# remove the request token now we don't need it
    request.session.delete('request_token')
    oauth.request_token = token

    access_token, access_token_secret = oauth.get_access_token(verifier)
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
    
    race = Race.objects.current()
    if not race:
        raise Http404

    random_driver: RaceDriver = RaceDriver.objects.random()
    pick, created = RacePick.objects.get_or_create(user=twitter_user, race=race, defaults=dict(
        driver=random_driver,
        tweet_id=1490491780520943620
    ))
    if not created:
        logger.info('Created %s', pick)

    context = {'race': race, 'user': twitter_user, 'pick': pick, 'created': created}
    return render(request, 'pick.html', context)