from datetime import datetime

from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone


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


class RaceDriver(models.Model):

    first_name = models.CharField(max_length=32)

    last_name = models.CharField(max_length=64)

    default_number = models.IntegerField(help_text='The driver\'s default number')

    default_team = models.ForeignKey(RaceTeam, on_delete=models.CASCADE)

    is_active = models.BooleanField(default=True)

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


class RaceEntry(models.Model):

    number = models.IntegerField()

    driver = models.ForeignKey(RaceDriver, on_delete=models.PROTECT)

    team = models.ForeignKey(RaceTeam, on_delete=models.PROTECT)

    race = models.ForeignKey(Race, on_delete=models.CASCADE)

    class Meta:
        default_related_name = 'cars'
        unique_together = ('race', 'driver')
    
    def __str__(self) -> str:
        return f'{self.driver} @ {self.race}'


class TwitterUser(models.Model):

    id = models.PositiveIntegerField(primary_key=True, unique=True, verbose_name='Twitter ID')

    username = models.CharField(max_length=64, unique=True)

    name = models.CharField(max_length=128)

    profile_img = models.URLField()

    class Meta:
        verbose_name = 'Twitter User'
        verbose_name_plural = 'Twitter Users'

    def __str__(self) -> str:
        return f'@{self.username}'


class RacePick(models.Model):

    user = models.ForeignKey(TwitterUser, on_delete=models.CASCADE)

    entry = models.ForeignKey(RaceEntry, on_delete=models.CASCADE)

    tweet_id = models.CharField(max_length=64)

    class Meta:
        unique_together = ['entry', 'user']
    
    def __str__(self):
        return f"{self.user}'s pick for {self.entry}"
