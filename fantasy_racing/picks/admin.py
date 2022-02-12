from django.contrib import admin

from .models import Race, Schedule


@admin.register(Schedule)
class ScheduleAdmin(admin.ModelAdmin):

    list_display = ('year',)


@admin.register(Race)
class RaceAdmin(admin.ModelAdmin):

    list_display = ('track', 'date', 'is_viewable', 'is_current')