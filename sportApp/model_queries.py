__author__ = 'Niklas Aronsson'
import logging
import datetime
from django.db.models import Q
from sportApp.models import Tournament, Game, Player, Division
from TableData import StandingsTable


logger = logging.getLogger('ModelQueries')


class TournamentData(object):
    """
    Interface to get tournament data for tournament / division.
    """
    def __init__(self, tournament_id, division_id):
        logger.info("TournamentData __init__")
        self.StandingsTable = StandingsTable(tournament_id)
        self._id = tournament_id
        self.tournament = Tournament.objects.get(id=tournament_id)
        self.games = self.tournament.games.filter(division_id=division_id)
        self.name = self.tournament.name
        self.unplayed_games = [g for g in self.games if g.played is False]
        self.played_games = [g for g in self.games if g.played is True]
        self.standings = None
        self._make_standings()

    def _make_standings(self):
        for game in self.games:
            self.StandingsTable.add_game(game)
        self.standings = self.StandingsTable.get_standing()


def get_active_tournaments():
    return Tournament.objects.filter(active=True)


def get_divisions():
    return Division.objects.all().order_by("rank")


def get_latest_played_games(number_of_games=20):
    return Game.objects.filter(played=True).order_by("date").reverse()[:number_of_games]


def get_todays_games():
    """
    Returns games that have a data of today or earlier.
    :return:
    """
    todays_date = datetime.date.today()
    logger.info("Today's date is: {0}".format(todays_date))
    return Game.objects.filter(played=False).filter(date__lte=todays_date).order_by("division__rank")


def get_todays_games_for_player(player_id):
    return Game.objects.filter(((Q(home_player_id=player_id) |
                                 Q(away_player_id=player_id)) &
                                 Q(played=False) &
                                 Q(date__lte=datetime.date.today())))


def get_game_progress(current_tournaments):
    results = []
    for tournament in current_tournaments:
        played_percentage = int(len(tournament.games.filter(played=True))*100/len(tournament.games.all()))
        results.append(played_percentage)
    return results


def get_players_per_division():
    """
    Return a list of tuples containing two items: [Division_instance, player_list]

    :return:
    """
    result_list = []
    all_divisions = Division.objects.all()
    for div in all_divisions:
        players = Player.objects.filter(current_division_id=div.id)
        logger.info("League: {0} have {1} players.".format(div.name, len(players)))
        result_list.append([div, players])
    return result_list


def get_games_left_to_play(player_id):
    """
    Returns a list of games the player have yet to play.

    :param player_id:
    :return:
    """
    return Game.objects.filter(((Q(home_player_id=player_id) |
                                 Q(away_player_id=player_id)) &
                                 Q(played=False)))


def get_games_played_by_player(player_id, show_latest=20):
    """
    Returns a list of games the player have yet to play.

    :param player_id:
    :return:
    """
    return Game.objects.filter(((Q(home_player_id=player_id) |
                                 Q(away_player_id=player_id)) &
                                 Q(played=True)))[:show_latest]








