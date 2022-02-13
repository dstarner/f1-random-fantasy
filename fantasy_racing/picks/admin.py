from django.contrib import admin

from .models import Race, Schedule, TwitterUser


@admin.register(Schedule)
class ScheduleAdmin(admin.ModelAdmin):

    list_display = ('year',)


@admin.register(Race)
class RaceAdmin(admin.ModelAdmin):

    list_display = ('track', 'date', 'is_viewable', 'is_current')


@admin.register(TwitterUser)
class TwitterUserAdmin(admin.ModelAdmin):

    list_display = ('display_name', 'name', 'id')
    search_fields = ('username', 'name')

    @admin.display(ordering='username', description='Display Name')
    def display_name(self, obj):
        return str(obj)
