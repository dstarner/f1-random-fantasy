from django.contrib import admin

from .models import FAQ, Race, RaceDriver, RacePick, RaceResult, RaceTeam, Schedule, TwitterUser


admin.site.site_header = 'F1 Random Fantasy'
admin.site.site_title = 'F1 Random Fantasy'
admin.site.index_title = 'F1 Random Fantasy Portal'


@admin.register(FAQ)
class FAQAdmin(admin.ModelAdmin):

    list_display = ('question',)
    search_fields = ('question', 'answer')


@admin.register(Schedule)
class ScheduleAdmin(admin.ModelAdmin):

    list_display = ('year',)


@admin.register(RaceTeam)
class RaceTeamAdmin(admin.ModelAdmin):

    list_display = ('name',)
    search_fields = ('name',)


@admin.register(RaceDriver)
class RaceDriverAdmin(admin.ModelAdmin):

    list_display = ('name', 'default_team')
    search_fields = ('first_name', 'last_name', 'default_team__name')


@admin.register(Race)
class RaceAdmin(admin.ModelAdmin):

    list_display = ('track', 'date', 'is_viewable', 'is_current')


@admin.register(RacePick)
class RacePickAdmin(admin.ModelAdmin):

    list_display = ('user', 'race', 'driver')


@admin.register(RaceResult)
class RaceResultAdmin(admin.ModelAdmin):

    list_display = ('race', 'driver', 'position')


@admin.register(TwitterUser)
class TwitterUserAdmin(admin.ModelAdmin):

    list_display = ('display_name', 'name', 'id')
    search_fields = ('username', 'name')

    @admin.display(ordering='username', description='Display Name')
    def display_name(self, obj):
        return str(obj)
