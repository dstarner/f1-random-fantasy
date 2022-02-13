from datetime import datetime

from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone


class ScheduleManager(models.Manager):

    def get_by_natural_key(self, year):
        return self.get(year=year)


class Schedule(models.Model):

    year = models.PositiveIntegerField(unique=True)

    objects = ScheduleManager()

    class Meta:
        ordering = ('year',)
    
    def get_by_natural_key(self):
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
    
    def get_by_natural_key(self):
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
        return f'{self.track}'


class TwitterUser(models.Model):

    id = models.PositiveIntegerField(primary_key=True, unique=True, verbose_name='Twitter ID')

    username = models.CharField(max_length=64, unique=True)

    name = models.CharField(max_length=128)

    def __str__(self) -> str:
        return f'@{self.username}'