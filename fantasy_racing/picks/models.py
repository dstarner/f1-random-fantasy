import random

from django.core.exceptions import ValidationError
from django.db import models
from django.db.models.functions import Coalesce
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone
from django_extensions.db.fields import CreationDateTimeField


class FAQ(models.Model):

    question = models.CharField(max_length=256)

    answer = models.TextField()

    order = models.SmallIntegerField(default=0, help_text='Higher shows first')

    class Meta:
        ordering = ('-order',)
        verbose_name = 'Frequently Asked Question'
        verbose_name_plural = 'Frequently Asked Questions'

    def __str__(self) -> str:
        return self.question


class RaceTeamManager(models.Manager):

    def get_by_natural_key(self, name):
        return self.get(name=name)


class RaceTeam(models.Model):

    name = models.CharField(max_length=64)

    objects = RaceTeamManager()

    class Meta:
        verbose_name = 'Race Team'
        verbose_name_plural = 'Race Teams'
    
    def natural_key(self):
        return (self.name,)

    def __str__(self):
        return self.name


class RaceDriverManager(models.Manager):

    def get_by_natural_key(self, first_name, last_name):
        return self.get(first_name=first_name, last_name=last_name)
    
    def random(self):
        active_driver_ids = list(self.filter(is_active=True).values_list('id', flat=True))
        return self.get(id=random.choice(active_driver_ids))


class RaceDriver(models.Model):

    first_name = models.CharField(max_length=32)

    last_name = models.CharField(max_length=64)

    default_number = models.IntegerField(help_text='The driver\'s default number')

    default_team = models.ForeignKey(RaceTeam, on_delete=models.CASCADE)

    is_active = models.BooleanField(default=True)

    objects = RaceDriverManager()

    class Meta:
        default_related_name = 'drivers'
        ordering = ('last_name',)
        verbose_name = 'Driver'
        verbose_name_plural = 'Drivers'
    
    def natural_key(self):
        return (self.first_name, self.last_name)
    
    @property
    def name(self) -> str:
        return f'{self.first_name} {self.last_name}'
    
    def __str__(self):
        return self.name


class ScheduleManager(models.Manager):

    def get_by_natural_key(self, year):
        return self.get(year=year)


class Schedule(models.Model):

    year = models.PositiveIntegerField(unique=True)

    objects = ScheduleManager()

    class Meta:
        ordering = ('year',)
    
    def natural_key(self):
        return (self.year,)
    
    def __str__(self) -> str:
        return str(self.year)
    
    @property
    def races_complete(self):
        return self.races.filter(date__lte=timezone.now().date()).count()


class RaceManager(models.Manager):

    def get_by_natural_key(self, date):
        return self.get(date=date)

    def viewable(self):
        current: Race = self.current()
        return self.filter(date__lte=current.date)
    
    def current(self):
        return self.filter(date__gte=timezone.now().date()).first()


class Race(models.Model):

    schedule = models.ForeignKey(Schedule, on_delete=models.CASCADE)

    track = models.CharField(max_length=128)

    date = models.DateField()

    submit_by = models.DateTimeField(help_text='Time that things must be submitted by in UTC')

    objects = RaceManager()

    class Meta:
        default_related_name = 'races'
        ordering = ('date',)
    
    def clean(self) -> None:
        if self.schedule.year != self.date.year:
            raise ValidationError('Schedule year must equal race year')
    
    def natural_key(self):
        return (self.date,)
    
    @property
    def is_viewable(self):
        return self.schedule.races.viewable().filter(id=self.id).exists()
    
    @property
    def is_current(self):
        return self.schedule.races.current() == self
    
    @property
    def idx(self):
        race_ids = list(self.schedule.races.values_list('id', flat=True))
        return race_ids.index(self.id)
    
    def __str__(self) -> str:
        return f'{self.track} in {self.schedule.year}'


class TwitterUserQuerySet(models.QuerySet):

    def with_start_count(self, schedule: Schedule = None):
        if not schedule:
            return self.annotate(starts=models.Count('picks'))
        return self.annotate(starts=models.Count('picks', filter=models.Q(picks__race__schedule=schedule)))
    
    def details(self, schedule: Schedule = None):

        def with_schedule_q(q: models.QuerySet):
            if not schedule:
                return q
            schedule_q = models.Q(picks__race__schedule=schedule)
            return q & schedule_q if q else schedule_q

        qs = self.with_start_count(schedule=schedule)
        return qs.annotate(
            wins=models.Count('picks', filter=with_schedule_q(models.Q(picks__result__position=1))),
            podiums=models.Count('picks', filter=with_schedule_q(models.Q(picks__result__position__lte=3))),
            top_10s=models.Count('picks', filter=with_schedule_q(models.Q(picks__result__position__lte=10))),
            avg_finish=Coalesce(models.Avg('picks__result__position', filter=with_schedule_q(None)), 0.0),
            # Coalesce handles the case of null result/points before a season starts
            points=Coalesce(models.Sum('picks__result__points', filter=with_schedule_q(None)), 0)
        )

    def participating_users(self, schedule: Schedule):
        return self.with_start_count(schedule=schedule) \
                   .filter(starts__gt=0).all()


class TwitterUser(models.Model):

    id = models.PositiveIntegerField(primary_key=True, unique=True, verbose_name='Twitter ID')

    username = models.CharField(max_length=64, unique=True)

    name = models.CharField(max_length=128)

    profile_img = models.URLField()

    objects = TwitterUserQuerySet.as_manager()

    class Meta:
        verbose_name = 'Twitter User'
        verbose_name_plural = 'Twitter Users'

    def __str__(self) -> str:
        return f'@{self.username}'
    
    @property
    def first_pick(self):
        if not getattr(self, '_first_pick', None):
            self._first_pick = self.picks.order_by('race__date').first()
        return self._first_pick


class RaceResult(models.Model):

    driver = models.ForeignKey(RaceDriver, on_delete=models.CASCADE)

    race = models.ForeignKey(Race, on_delete=models.CASCADE)

    position = models.SmallIntegerField()

    points = models.SmallIntegerField()

    class Meta:
        unique_together = [
            ('race', 'driver'),
            ('race', 'position'),
        ]
        default_related_name = 'results'
        ordering = ('race', 'position',)
        verbose_name = 'Race Result'
        verbose_name_plural = 'Race Results'
    
    def __str__(self) -> str:
        return f'{self.driver} @ {self.race}'


class RacePick(models.Model):

    user = models.ForeignKey(TwitterUser, on_delete=models.CASCADE)

    driver = models.ForeignKey(RaceDriver, on_delete=models.PROTECT)

    race = models.ForeignKey(Race, on_delete=models.CASCADE)

    tweet_id = models.CharField(max_length=64)

    timestamp = CreationDateTimeField()

    result = models.ForeignKey(
        RaceResult, on_delete=models.CASCADE, null=True, blank=True,
        help_text='Is associated on result save'
    )

    class Meta:
        unique_together = ['race', 'user']
        default_related_name = 'picks'
        ordering = ('timestamp',)
        verbose_name = 'Race Pick'
        verbose_name_plural = 'Race Picks'
    
    def __str__(self):
        return f"{self.user}'s pick for {self.race}"


@receiver(post_save, sender=RaceResult)
def update_race_pick_results(instance: RaceResult, **kwargs):
    """When a result is provided, update all associated picks to point at it
    """
    RacePick.objects.filter(race=instance.race, driver=instance.driver).all().update(result=instance)
