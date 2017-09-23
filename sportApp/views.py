import datetime
import logging
import random
from django.http import HttpResponse, HttpResponseRedirect
from django.template import RequestContext, loader
from django.conf import settings
from sportApp.models import Game, Player, Tournament, Division
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.core.urlresolvers import reverse
from sportApp.forms import MatchEditForm, RegisterPlayerForm, NewTournamentForm, LogInForm, DivisionSelectForm
from sportApp.forms import DivisionSelector
from django.shortcuts import redirect, render, get_object_or_404
import sportApp.model_queries as mq
import sportApp.app_logic
from sportApp.GenerateGames import GenerateGames


logging.basicConfig(format='%(name)s:%(levelname)s:%(lineno)s:%(message)s', level=logging.INFO)
logger = logging.getLogger('DjangoViews')


def home(request):
    active_tournaments = mq.get_active_tournaments()
    game_progress_per_tournament = mq.get_game_progress(active_tournaments)
    context = {"tournament_data": zip(active_tournaments, game_progress_per_tournament),
               "todays_games": mq.get_todays_games(),
               "latest_played_games": mq.get_latest_played_games(),
               "divisions": mq.get_divisions()}
    return render(request, 'home.html', context)


def rankings(request):
    context = {}
    return render(request, 'rankings.html', context)


def show_tournament_data(request, tournament_id, division_id):
    if "name" in request.POST:
        name = request.POST.get("name", False)
        if name:
            return HttpResponseRedirect(reverse('show_tournament_data', args=[tournament_id, name]))
        else:
            # todo: This means select all!
            logger.info("Show all tables at once!")
            return HttpResponseRedirect(reverse('show_tournament_data', args=[tournament_id, 0]))
    t_data = None
    all_tables = []
    current_tournament = Tournament.objects.get(id=tournament_id)
    if division_id != "0":
        division_select = DivisionSelector({'name': division_id})
        logger.info("Show tournament data for tournament: {0} div: {1}".format(tournament_id, division_id))
        t_data = mq.TournamentData(tournament_id, division_id)
        division_instance = Division.objects.get(pk=division_id)
    else:
        division_select = DivisionSelector({'name': 0})
        logger.info("Show data for all tables at once.")
        current_divisions = Division.objects.filter(active=True).all()
        division_instance = None
        for div in current_divisions:
            logger.info("Get Standings for {0}".format(div.name))
            t = mq.TournamentData(tournament_id, div.id)
            all_tables.append([div, t.standings])
    context = {"tournament_data": t_data,
               "tournament_id": tournament_id,
               "division_id": division_id,
               "division_select": division_select,
               "table": t_data,
               "all_tables": all_tables,
               "current_tournament": current_tournament,
               "division": division_instance}
    return render(request, 'tournament_info.html', context)


def edit_match_data(request, match_id, tournament_id, division_id):
    current_game = get_object_or_404(Game, pk=match_id)
    error_msg = ""
    if not request.POST:
        match_form = MatchEditForm(instance=current_game, initial={'date':datetime.date.today()})
    else:
        match_form = MatchEditForm(request.POST, instance=current_game)
        if match_form.is_valid():
            if not (isinstance(match_form.cleaned_data['home_score'], int) or
                    isinstance(match_form.cleaned_data['away_score'], int)):
                error_msg = "Please input a valid integer."
            else:
                game_data = match_form.save(commit=False)
                game_data.played = True
                game_data.save()
                if int(tournament_id) and int(division_id):
                    logger.info("Game result saved. Show tournament data.")
                    return HttpResponseRedirect(reverse('show_tournament_data', args=[tournament_id, division_id]))
                else:
                    logger.info("Game result saved. Go to home.")
                    return HttpResponseRedirect(reverse('home', args=[]))

        else:
            error_msg = "Incorrect date."
    context = {"match_form": match_form,
               "current_game": current_game,
               "error_msg": error_msg,
               "tournament_id": tournament_id,
               "division_id": division_id}
    return render(request, 'edit_match_data.html', context)


def register_player(request):
    if request.POST:
        player_form = RegisterPlayerForm(request.POST)
        if player_form.is_valid():
            player_form.save()
            return HttpResponseRedirect(reverse('home', args=[]))
    else:
        player_form = RegisterPlayerForm()
    context = {"RegisterPlayerForm": player_form}
    return render(request, 'register_player.html', context)


def active_players(request):
    selected_division = request.GET.get("name", False)
    division_name = ""
    if selected_division:
        division_select = DivisionSelector(request.GET)
        division_name = Division.objects.get(pk=selected_division).name
        players = Player.objects.filter(active=True).filter(current_division__id=selected_division)
    else:
        division_select = DivisionSelector()
        players = Player.objects.filter(active=True)
    context = {"Players": players,
               "division_name": division_name,
               "division_select": division_select}
    return render(request, 'active_players.html', context)

@login_required
def new_tournament(request):
    if request.POST:
        new_tournament_form = NewTournamentForm(request.POST)
        if new_tournament_form.is_valid():
            logger.info("New tournament data is valid. Redirect to generate games.")
            t_data = new_tournament_form.save(commit=False)
            t_data.active = True
            t_data.save()
            return HttpResponseRedirect(reverse('generate_games', args=[t_data.id]))
        else:
            logger.info("New tournament data is invalid.")
    else:
        new_tournament_form = NewTournamentForm()
    context = {"new_tournament": new_tournament_form}
    return render(request, 'new_tournament.html', context)


def generate_games(request, tournament_id):
    division_player_data = mq.get_players_per_division()
    t_data = Tournament.objects.get(id=tournament_id)
    games_per_division = []
    for div, players in division_player_data:
        logger.info(u"Generate games for division: {0}".format(div))
        gg = GenerateGames(players, div, t_data.start_date, tournament_id)
        t_data.games.add(*gg.generated_games)
        games_per_division.append([div.name, gg.generated_games])

    context = {"current_tournament": t_data,
               "games_per_division": games_per_division}
    return render(request, 'generate_games.html', context)


def show_default_player(request):
    if 'default_player' in request.COOKIES:
        response = redirect('show_player_data', request.COOKIES['default_player'])
        response['Location'] += '?default=1'.format()
        return response
    else:
        return render(request, 'default_player.html', {})


def tournaments(request):
    context = {"active_tournaments": Tournament.objects.filter(active=True),
               "old_tournaments": Tournament.objects.filter(active=False)}
    return render(request, 'browse_tournaments.html', context)


def make_player_default(request, player_id):
    response = redirect('show_player_data', player_id)
    response['Location'] += '?default=1'.format()
    response.set_cookie('default_player', player_id, expires=None)
    return response


def show_player_data(request, player_id):
    context = {"default": request.GET.get("default", False),
               "player_data": get_object_or_404(Player, pk=player_id),
               "played_games": mq.get_games_played_by_player(player_id=player_id),
               "current_tournaments": Tournament.objects.filter(active=True).filter(),
               "player_stats": Game.objects.get_stats_for_player(player_id),
               "unplayed_games": mq.get_games_left_to_play(player_id)}
    return render(request, 'player_statistics.html', context)


def generate_divisions(request):
    for division_name, rank in settings.DEFAULT_DIVISIONS:
        if not Division.objects.filter(name=division_name).exists():
            new_division = Division(name=division_name, rank=rank)
            new_division.save()
    return HttpResponse("OK", mimetype='application/json')


def upload_player_list(request):
    status_msg = ""
    if request.POST:
        player_upload_form = DivisionSelectForm(request.POST, request.FILES)
        if player_upload_form.is_valid():
            division_id = request.POST['league']
            current_division = Division.objects.get(pk=division_id)
            logger.info("PlayerUpload is valid.")
            data_content = request.FILES['textfile'].read()
            new_players = data_content.split("\n")
            new_players = [p.rstrip() for p in new_players if p]
            for p in new_players:
                if p:
                    new_player = Player(name=p, current_division=current_division)
                    new_player.save()
            status_msg = "Added {0} new players to {1}".format(len(new_players), current_division)
        else:
            logger.info("PlayerUpload is invalid.")
    else:
        player_upload_form = DivisionSelectForm()

    context = {"DivisionSelectForm": player_upload_form,
               "status_msg": status_msg}
    return render(request, 'upload_player_list.html', context)


def randomize_players(request):
    if request.GET.get("random", False):
        ranks = Division.objects.values_list("rank", flat=True).distinct()
        logger.info("There are {0} different division ranks.".format(len(ranks)))
        for rank in ranks:
            players = Player.objects.filter(current_division__rank=rank)
            logger.info("There are {1} players with division ranked {0}".format(rank, len(players)))
            current_divisions = Division.objects.filter(rank=rank)
            group_size = int(players.count()/int(current_divisions.count()))
            logger.info("A group should have at least {0} players.".format(group_size))
            player_index = range(players.count())
            random.shuffle(player_index)
            while player_index:
                for division in current_divisions:
                    index_to_assaign = player_index.pop()
                    players[index_to_assaign].current_division = division
            for p in players:
                p.save()
    return render(request, "random.html", {})


def log_in(request):
    username = request.POST.get('username', False)
    password = request.POST.get('password', False)
    err_msg = None
    if request.POST:
        log_form = LogInForm(request.POST)
        user = authenticate(username=username, password=password)
        if user is not None:
            if user.is_active:
                login(request, user)
                logger.info("User {0} logged in".format(username))
                return HttpResponseRedirect(reverse('home', args=[]))
            else:
                pass
        else:
            err_msg = "Username and password did not match."
            logger.info("User {0} tried to log in".format(username))
    else:
        log_form = LogInForm()
    context = {"log_in_form": log_form,
               "error_message": err_msg}
    return render(request, 'log_in.html', context)


def log_out(request):
    logout(request)
    return HttpResponseRedirect(reverse('home', args=[]))

