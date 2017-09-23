__author__ = 'enikaro'
import datetime
from django import forms
from django.conf import settings
from sportApp.models import Game, Player, Tournament, Division


class MatchEditForm(forms.ModelForm):

    class Meta:
        model = Game
        exclude = ['played', 'home_player', 'away_player', 'division']


class RegisterPlayerForm(forms.ModelForm):
    name = forms.CharField(widget=forms.TextInput(
                           attrs={'size': '60',
                                  'class': 'inputText'}))

    team = forms.CharField(initial=settings.DEFAULT_TEAM_NAME,
                           widget=forms.TextInput(
                               attrs={'size': '60',
                                      'class': 'inputText'}))

    email = forms.CharField(initial="someone@host.com",
                            widget=forms.TextInput(
                                attrs={'size': '60',
                                       'class': 'inputText'}))

    class Meta:
        model = Player
        exclude = [
            'active', 'games_won', 'goals_against', 'games_draw', 'games_played', 'goals_made', 'games_lost']


class NewTournamentForm(forms.ModelForm):
    class Meta:
        model = Tournament
        fields = '__all__'


class LogInForm(forms.Form):
    username = forms.CharField(widget=forms.TextInput(
                               attrs={'size': '25',
                               'class': 'inputText'}))
    password = forms.CharField(widget=forms.TextInput(
                               attrs={'size': '25',
                               'class': 'inputText'}))


class DivisionSelector(forms.ModelForm):
    name = forms.ModelChoiceField(queryset=Division.objects.filter(active=True).all(),
                                  empty_label="Show all")

    class Meta:
        model = Division
        fields = ["name"]


class DivisionSelectForm(forms.Form):
    league = forms.ModelChoiceField(queryset=Division.objects.filter(active=True).all(),
                                    empty_label="Select League")

    textfile = forms.FileField(label='Select a file')

    class Meta:
        fields = '__all__'

