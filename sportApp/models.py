import logging
import datetime
import django
from django.db import models
from django.conf import settings


logger = logging.getLogger('Models')


class Division(models.Model):
    name = models.CharField(max_length=40)
    rank = models.IntegerField()
    active = models.BooleanField(default=True)

    def __unicode__(self):
        return self.name

    class Meta:
        ordering = ["rank"]


class Player(models.Model):
    name = models.CharField(max_length=40, unique=True)
    email = models.EmailField(blank=True)
    team = models.CharField(max_length=30, default=settings.DEFAULT_TEAM_NAME)
    current_division = models.ForeignKey(Division, unique=False)
    active = models.BooleanField(default=True)
    goals_made = models.IntegerField(default=0)
    goals_against = models.IntegerField(default=0)
    games_played = models.IntegerField(default=0)
    games_won = models.IntegerField(default=0)
    games_lost = models.IntegerField(default=0)
    games_draw = models.IntegerField(default=0)

    def __unicode__(self):
        return u"{0} - {1}".format(self.name, self.current_division.name)

    class Meta:
        ordering = ["current_division"]


class GameManager(models.Manager):
    def get_stats_for_player(self, player_id):
        games = self.filter(home_player_id=player_id) | self.filter(away_player_id=player_id)
        stat_dict = {"games_played": 0,
                     "games_to_play": 0,
                     "games_won": 0,
                     "games_lost": 0,
                     "games_draw": 0,
                     "goals_made": 0,
                     "goals_against": 0}
        for g in games:
            if g.wo_home or g.wo_away:
                goals_against = 0
                goals_made = 0
                logger.info("WO in current game!")
                if g.wo_away and player_id == g.home_player.id:
                    goals_made = 5
                    goals_against = 0
                elif g.wo_home and player_id == g.home_player.id:
                    goals_made = 0
                    goals_against = 5
                elif g.wo_away and player_id == g.away_player.id:
                    goals_made = 0
                    goals_against = 5
                elif g.wo_home and player_id == g.away_player.id:
                    goals_made = 5
                    goals_against = 0
                else:
                    logger.info("No goals bound!")
            elif g.wo_away and g.wo_away:
                logger.info("WO for both players.")
                # TODO: Handle!

            elif g.is_game_a_draw() is not None:
                goals_against = g.is_game_a_draw()
                goals_made = goals_against
                stat_dict["games_draw"] += 1
            else:
                result, goals_made, goals_against = g.did_player_win(player_id)
                if result:
                    stat_dict["games_won"] += 1
                elif result is None:
                    stat_dict["games_to_play"] += 1
                    continue
                else:
                    stat_dict["games_lost"] += 1
            stat_dict["goals_made"] += goals_made
            stat_dict["goals_against"] += goals_against
            stat_dict["games_played"] += 1
        return stat_dict


class Game(models.Model):
    home_player = models.ForeignKey(Player, related_name='home_player', unique=False)
    away_player = models.ForeignKey(Player, related_name='away_player', unique=False)
    division = models.ForeignKey(Division, unique=False)
    home_score = models.IntegerField(blank=True, null=True)
    away_score = models.IntegerField(blank=True, null=True)
    played = models.BooleanField(default=False)
    walk_over = models.BooleanField(default=False, help_text="Since WO per player added this should probably not be used.")
    wo_home = models.BooleanField(default=False, help_text="Set this to True if home player is WO. Both players can be WO and then both will have a -5 score.")
    wo_away = models.BooleanField(default=False, help_text="Set this to True if home player is WO")
    date = models.DateField(default=django.utils.timezone.now, blank=True)
    game_description = models.CharField(max_length=30, blank=True, null=True, default="")
    objects = GameManager()

    def is_game_a_draw(self):
        if self.home_score == self.away_score:
            logger.info("Game is a draw!")
            return self.home_score
        else:
            logger.info("Game is not a draw!")
            return None

    @property
    def final_home_score(self):
        if not self.wo_home:
            return self.home_score
        return "W.O."

    @property
    def final_away_score(self):
        if not self.wo_away:
            return self.away_score
        return "W.O."

    @property
    def final_standing(self):
        if not (self.wo_away or self.wo_home):
            return "{0} - {1}".format(self.home_score, self.away_score)
        if self.wo_away and self.wo_home:
            return "W.O. - W.O."
        elif self.wo_away and not self.wo_home:
            return "5 - 0 (W.O.)"
        return "0 - 5 (W.O.)"

    def did_player_win(self, player_id):
        """
        Returns a tuple [ game_status, goals_scored, goals_against]

        games_status - Player id won: True
                       Player id lost: False
                       game not played: None

        """
        logger.info("Game-Model: Get Game stats for player: {0}".format(player_id))
        if self.played is False:
            logger.info("Game-Model: Game is not played")
            return None, 0, 0
        else:
            if int(self.home_player.id) == int(player_id):
                if self.home_score > self.away_score:
                    logger.info("Game-Model: Player is home team and won.")
                    return True, self.home_score, self.away_score
                else:
                    logger.info("Game-Model: Player is home team and lost.")
                    return False, self.home_score, self.away_score
            else:
                if self.home_score < self.away_score:
                    logger.info("Game-Model: Player is away team and won")
                    return True, self.away_score, self.home_score
                else:
                    logger.info("Game-Model: Player is away team and lost")
                    return False, self.away_score, self.home_score

    def get_winner_player_id(self):
        """

        """
        if self.played is False:
            return False, 0, 0, 0
        elif self.home_score == self.away_score:
            return 0, 0, 0, 0
        else:
            if self.home_score > self.away_score:
                return self.home_player.id
            else:
                return self.away_player.id

    def __unicode__(self):
        if not self.played:
            return u"{0} {1} - {2} {3}".format(self.date,
                                               self.home_player.name,
                                               self.away_player.name,
                                               self.division.name)
        return u"{0} {1} vs {2}: {3} - {4}".format(self.date,
                                                   self.home_player.name,
                                                   self.away_player.name,
                                                   self.home_score,
                                                   self.away_score)

    class Meta:
        ordering = ["date"]


class Tournament(models.Model):
    winner = models.ForeignKey(Player,
                               related_name='tournament_winner',
                               unique=False, blank=True, null=True, default=None)
    name = models.CharField(max_length=40, unique=True)
    active = models.BooleanField(default=True)
    games = models.ManyToManyField(Game, blank=True)
    start_date = models.DateField(blank=True, default=django.utils.timezone.now)
    end_date = models.DateField(blank=True, default=datetime.datetime.now() + datetime.timedelta(days=30))

    def __unicode__(self):
        return self.name

    class Meta:
        get_latest_by = "end_date"


