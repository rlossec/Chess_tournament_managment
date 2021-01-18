import datetime

from chess.models.game import Tournament
from chess.models.actors import Actor
from chess.models.database import DataBaseHandler

from chess.views.menuview import MenuView
from chess.views.flow import view_validation_new_actor, view_input_new_actor, \
    view_intro_home_menu, view_tournament_creation, view_tournament_players,\
    view_id_player, view_launch_tournament, view_round_matchs, \
    view_validation_actors_imported, view_tournament_final, \
    view_validation_actors_exported, view_validation_players, \
    view_import_no_tournament

from chess.views.reports import report_actors_by_alpha, report_actors_by_rank,\
    report_tournaments_list, report_tournament_players, \
    report_tournament_matchs, report_tournament_rounds

from chess.controllers.menus import Menu
from chess.controllers.input import tournament_inputs, input_actor, \
    input_match_results, input_tournament_players, input_tournament_id


NB_PLAYERS = 8
NB_MATCH = 4
NB_ROUND = 4


class BrowseControllers:
    def __init__(self):
        self.controller = None

    def start(self):
        """
        launch the home menu.
        A loop while to browse between the controllers.
        :return: None
        """
        self.controller = HomeMenuController(True)
        while self.controller:
            self.controller = self.controller()


class Actors:
    """
    Store the actors in a class attribute,
    the keys are the actors id and the values
    are the instances of actors.
    """
    actors = {}

    def __init__(self):
        self.menu = Menu()
        self.view = MenuView(self.menu)

    def __call__(self):
        view_input_new_actor()
        actor_arguments = input_actor()
        actor = Actor(actor_arguments[0],
                      actor_arguments[1],
                      actor_arguments[2],
                      actor_arguments[3],
                      actor_arguments[4])
        Actors.actors[actor.actor_id] = actor
        view_validation_new_actor(actor)
        self.menu.add("auto", "Ajouter un nouveau joueur", Actors())
        self.menu.add("auto", "Exporter les joueurs", ExportActors(Actors.actors.values()))
        self.menu.add("auto", "Retour au menu principal", HomeMenuController())
        self.menu.add("q", "Quitter", Ending())

        user_choice = self.view.get_user_choice()
        return user_choice.handler


class HomeMenuController:
    """
    Handle the main menu
    """
    def __init__(self, init_import=False):
        self.menu = Menu()
        self.view = MenuView(self.menu)
        self.init_import = init_import

    def __call__(self):
        view_intro_home_menu()
        self.menu.add("auto", "Importer des joueurs", ImportActors())
        self.menu.add("auto", "Ajouter un nouveau joueur", ImportActors(self.init_import))
        self.menu.add("auto", "Lancer un tournoi", TournamentCreation())
        self.menu.add("auto", "Reprendre un tournoi", ResumeTournament())
        self.menu.add("auto", "Obtenir un rapport", ReportMenu())
        self.menu.add("q", "Quitter", Ending())

        user_choice = self.view.get_user_choice()
        return user_choice.handler


class TournamentCreation:
    """
    Handle the tournament creation
    """
    def __init__(self):
        self.tournament = None

    def __call__(self):
        view_tournament_creation()
        tournament_arguments = tournament_inputs()
        self.tournament = Tournament(tournament_arguments[0],
                                     tournament_arguments[1],
                                     tournament_arguments[2],
                                     tournament_arguments[3])
        self.tournament.start_date = datetime.date.today()
        return TournamentPlayersMenu(self.tournament)


class TournamentPlayersMenu:
    """
    Menu to input Players of the tournament
    """
    def __init__(self, tournament):
        self.tournament = tournament
        self.menu = Menu()
        self.view = MenuView(self.menu)

    def __call__(self):
        view_tournament_players(self.tournament)

        self.menu.add("auto",
                      "Ajouter les joueurs par leur identifiant",
                      TournamentPlayers(self.tournament))
        self.menu.add("auto",
                      "Interrompre le tournoi",
                      TournamentPause(self.tournament))
        self.menu.add("auto",
                      "Retour au Menu Principal",
                      HomeMenuController())
        self.menu.add("q", "Quitter", Ending())

        user_choice = self.view.get_user_choice()
        return user_choice.handler


class TournamentPause:
    """
    A menu to give the alternative to interrupt or go on the tournament
    """
    def __init__(self, tournament):
        self.tournament = tournament
        self.menu = Menu()
        self.view = MenuView(self.menu)

    def __call__(self):
        self.menu.add("auto",
                      "Continuer et passer au tour suivant",
                      LaunchTournament(self.tournament))
        self.menu.add("auto",
                      "Interrompre le tournoi",
                      TournamentInterruption(self.tournament))

        user_choice = self.view.get_user_choice()
        return user_choice.handler


class TournamentInterruption:
    """
    Interrupt the tournament and load the datas in the database
    to be able to resume it.
    """
    def __init__(self, tournament):
        self.tournament = tournament
        handler = DataBaseHandler()
        handler.database.table('tournament').truncate()
        handler.export_interrupted_tournament(self.tournament)

    def __call__(self):
        return Ending()


class TournamentPlayers:
    """
    Handle the input of the players of the tournament.
    """
    def __init__(self, tournament):
        self.tournament = tournament
        self.menu = Menu()
        self.view = MenuView(self.menu)

    def __call__(self):
        actors = []
        actors_id = []
        while len(actors) < NB_PLAYERS:
            num_player = len(actors) + 1
            view_id_player(self.tournament, num_player)
            message = "Vous pouvez revenir au menu principal " \
                      "en entrant 00000000. \nVeuillez indiquer " \
                      f"l'identifiant du joueur {num_player}: "
            error_message = ""
            actor_id = input_tournament_players(message)
            bug_dont_exist = 0
            bug_already_in = 0
            while actor_id in actors_id or actor_id not in Actors.actors:
                if actor_id == "00000000":
                    handler = HomeMenuController()
                    return handler()
                if actor_id in actors_id:
                    if bug_dont_exist == 0:
                        error_message = "Erreur: ce joueur est déjà présent dans le tournoi. "
                    bug_dont_exist += 1
                if actor_id not in Actors.actors:
                    if bug_already_in == 0:
                        error_message = "Erreur: identifiant inconnu. "
                    bug_already_in += 1
                actor_id = input_tournament_players(error_message + message)
            actors_id.append(actor_id)
            actor = Actors.actors[actor_id]
            actors.append(actor)
        self.tournament.define_players(actors)
        view_validation_players(actors)

        return LaunchTournament(self.tournament)


class LaunchTournament:
    """
    Launch the tournament, there is a kind of a loop
    between LaunchTournament and TournamentPause
    for the 4 rounds.
    """
    def __init__(self, tournament):
        self.tournament = tournament

    def __call__(self):
        if not self.tournament:
            view_import_no_tournament()
            return HomeMenuController()
        num_round = len(self.tournament.rounds)
        if num_round == 0:
            view_launch_tournament(self.tournament)
        if num_round == 4:
            view_tournament_final(self.tournament)
            self.tournament.finished = True
            database = DataBaseHandler()
            database.export_tournament(self.tournament)
        else:
            self.tournament.init_round(num_round)                                 # Instance de round et définition des matchs
            view_round_matchs(self.tournament.rounds[num_round])                  # Affichage des matchs
            winners = input_match_results(self.tournament.rounds[num_round])      # Attente, entrée des gagnants
            self.tournament.register_round_results(num_round, winners)            # Entrées dans instance de round
            view_round_matchs(self.tournament.rounds[num_round])                  # Affichage résultats
            return TournamentPause(self.tournament)


class ResumeTournament:
    """
    Resume a tournament.
    It imports the datas and progress of
    the last tournament interrupt.
    """
    def __call__(self):
        handler = DataBaseHandler()
        tournament = handler.import_interrupted_tournament()
        return LaunchTournament(tournament)


class ImportActors:
    """

    """
    def __init__(self, init=False):
        self.handler = HomeMenuController()
        self.init = init

    def __call__(self):
        if self.init:
            self.handler = Actors()
        handler = DataBaseHandler()
        num_actors, actors = handler.import_actors()
        view_validation_actors_imported(actors)
        for actor in actors:
            Actors.actors[actor.actor_id] = actor
        actors_table = handler.database.table("actors")
        actors_table.truncate()
        return self.handler()


class ExportActors:
    """

    """
    def __init__(self, actors):
        self.actors = actors

    def __call__(self):
        handler = DataBaseHandler()
        print(vars(handler.database.table("actors")))
        for actor in self.actors:
            handler.export_actor(actor)
        view_validation_actors_exported(self.actors)
        return HomeMenuController()


class ReportMenu:
    """
    Menu between the different reports
    """
    def __init__(self):
        self.menu = Menu()
        self.view = MenuView(self.menu)

    def __call__(self):
        self.menu.add("auto", "Liste des acteurs", ActorsList())
        self.menu.add("auto", "Liste des tournois", TournamentsList())
        self.menu.add("auto", "Rapports pour un tournoi", TournamentReportInput())
        self.menu.add("auto", "Retour au Menu principal", HomeMenuController())
        self.menu.add("q", "Quitter", Ending())

        user_choice = self.view.get_user_choice()
        return user_choice.handler


class ActorsList:
    """
    Menu to obtain the actors lists
    """
    def __init__(self):
        self.menu = Menu()
        self.view = MenuView(self.menu)

    def __call__(self):
        self.menu.add("auto", "Trier par ordre alphabétique", ActorsListAlphabetical())
        self.menu.add("auto", "Trier selon leur classement", ActorsListRank())
        self.menu.add("auto", "Obtenir un autre rapport", ReportMenu())
        self.menu.add("auto", "Retour au Menu principal", HomeMenuController())
        self.menu.add("q", "Quitter", Ending())

        user_choice = self.view.get_user_choice()
        return user_choice.handler


class ActorsListAlphabetical:
    """
    Handle the list of actors in alphabetical order
    """
    def __init__(self):
        self.menu = Menu()
        self.view = MenuView(self.menu)

    def __call__(self):
        handler = DataBaseHandler()
        num_actors, actors_list = handler.import_actors()
        report_actors_by_alpha(actors_list)
        self.menu.add("auto", "Retour au choix du tri", ActorsList())
        self.menu.add("auto", "Obtenir un autre rapport", ReportMenu())
        self.menu.add("auto", "Retour au Menu principal", HomeMenuController())
        self.menu.add("q", "Quitter", Ending())

        user_choice = self.view.get_user_choice()
        return user_choice.handler


class ActorsListRank:
    """
    Handle the list of actors in rank order
    """
    def __init__(self):
        self.menu = Menu()
        self.view = MenuView(self.menu)

    def __call__(self):
        handler = DataBaseHandler()
        num_actors, actors_list = handler.import_actors()
        report_actors_by_rank(actors_list)
        self.menu.add("auto", "Retour au choix du tri", ActorsList())
        self.menu.add("auto", "Obtenir un autre rapport", ReportMenu())
        self.menu.add("auto", "Retour au Menu principal", HomeMenuController())
        self.menu.add("q", "Quitter", Ending())

        user_choice = self.view.get_user_choice()
        return user_choice.handler


class TournamentsList:
    """
    Handle the list of tournaments
    """
    def __init__(self):
        self.menu = Menu()
        self.view = MenuView(self.menu)

    def __call__(self):
        report_tournaments_list()
        self.menu.add("auto", "Obtenir un autre rapport", ReportMenu())
        self.menu.add("auto", "Retour au Menu principal", HomeMenuController())
        self.menu.add("q", "Quitter", Ending())

        user_choice = self.view.get_user_choice()
        return user_choice.handler


class TournamentReportInput:
    """
    Ask for the tournament we want to get reports from
    """
    def __call__(self):
        tournament_id = input_tournament_id()
        pass
        # chercher tournament_id dans les tournois
        #handler = TournamentRapportMenu(tournament)
        #return handler


class TournamentReportMenu:
    """
    Handle the menu of reports of a tournament
    """
    def __init__(self, tournament):
        self.tournament = tournament
        self.menu = Menu()
        self.view = MenuView(self.menu)

    def __call__(self):
        #view_tournament_reports()
        self.menu.add("auto", "Liste des joueurs du tournoi", TournamentPlayersList(self.tournament))
        self.menu.add("auto", "Liste des matchs du tournoi", TournamentMatchsList(self.tournament))
        self.menu.add("auto", "Liste des matchs du tournoi", TournamentRoundsList(self.tournament))
        self.menu.add("auto", "Obtenir un autre rapport", ReportMenu())
        self.menu.add("auto", "Retour au Menu principal", HomeMenuController())
        self.menu.add("q", "Quitter", Ending())

        user_choice = self.view.get_user_choice()
        return user_choice.handler


class TournamentPlayersList:
    """
    Display the report of the players of a tournament
    """
    def __init__(self, tournament):
        self.tournament = tournament
        self.menu = Menu()
        self.view = MenuView(self.menu)

    def __call__(self):
        report_tournament_players()
        self.menu.add("auto", "Retour au menu rapport du tournoi", TournamentReportMenu(self.tournament))
        self.menu.add("auto", "Obtenir un autre rapport", ReportMenu())
        self.menu.add("auto", "Retour au Menu principal", HomeMenuController())
        self.menu.add("q", "Quitter", Ending())

        user_choice = self.view.get_user_choice()
        return user_choice.handler


class TournamentMatchsList:
    """
    Display the report of the matchs of a tournament
    """
    def __init__(self, tournament):
        self.tournament = tournament
        self.menu = Menu()
        self.view = MenuView(self.menu)

    def __call__(self):
        report_tournament_matchs()
        self.menu.add("auto", "Retour au menu rapport du tournoi", TournamentReportMenu(self.tournament))
        self.menu.add("auto", "Obtenir un autre rapport", ReportMenu())
        self.menu.add("auto", "Retour au Menu principal", HomeMenuController())
        self.menu.add("q", "Quitter", Ending())

        user_choice = self.view.get_user_choice()
        return user_choice.handler


class TournamentRoundsList:
    """
    Display the report of the rounds of a tournament
    """
    def __init__(self, tournament):
        self.tournament = tournament
        self.menu = Menu()
        self.view = MenuView(self.menu)

    def __call__(self):
        report_tournament_rounds()
        self.menu.add("auto", "Retour au menu rapport du tournoi", TournamentReportMenu(self.tournament))
        self.menu.add("auto", "Obtenir un autre rapport", ReportMenu())
        self.menu.add("auto", "Retour au Menu principal", HomeMenuController())
        self.menu.add("q", "Quitter", Ending())

        user_choice = self.view.get_user_choice()
        return user_choice.handler


class Ending:
    """
    The exit screen
    """
    def __init__(self):
        self.menu = Menu()
        self.view = MenuView(self.menu)

    def __call__(self):
        print("Aurevoir")  # A modifier -> views


if __name__ == "__main__":
    app = BrowseControllers()
    app.start()
