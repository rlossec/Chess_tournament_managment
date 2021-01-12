from chess.models.actors import Actor, Player
from chess.models.match import Match
from chess.models.round import Round
from chess.models.game import Tournament

from chess.utils.conversion import str_to_date, \
    str_space_to_list, str_space_to_int_list


def deserialize_actor(serialized_actor):
    """
    transforms a dictionary containing the values of an actor instance
     into the corresponding actor instance.
    :param serialized_actor: structured dictionary.
    :return: instance of actor.
    """
    actor = Actor(serialized_actor['last_name'],
                  serialized_actor['first_name'],
                  str_to_date(serialized_actor['birthdate']),
                  serialized_actor['gender'],
                  serialized_actor['rank'])
    actor.actor_id = serialized_actor['actor_id']
    actor.tournaments = str_space_to_list(serialized_actor['tournaments'])
    return actor


def deserialize_player(serialized_player):
    """
    transforms a dictionary containing the values of a player instance
     into the corresponding player instance.
    :param serialized_player: structured dictionary.
    :return: instance of player.
    """
    actor = deserialize_actor(serialized_player['actor'])
    player = Player(actor,
                    serialized_player['tournament_id'],
                    serialized_player['player_id'])
    string_attribute = ['name', 'rank', 'ranking', 'points', 'place']
    for key in string_attribute:
        setattr(player, key, serialized_player[key])
    player.opponents = str_space_to_int_list(serialized_player['opponents'])
    return player


def deserialize_match(serialized_match):
    """
    transforms a dictionary containing the values of a match instance
     into the corresponding match instance.
    :param serialized_match: structured dictionary.
    :return: instance of match.
    """
    match = Match(serialized_match['match_nb'],
                  serialized_match['round_nb'],
                  serialized_match['tournament_id'])
    player1 = deserialize_player(serialized_match['player1'])
    setattr(match, 'player1', player1)
    player2 = deserialize_player(serialized_match['player2'])
    setattr(match, 'player2', player2)
    string_attribute = ['winner', 'finished', 'points_assigned']
    for attribute in string_attribute:
        setattr(match, attribute, serialized_match[attribute])
    return match


def deserialize_round(serialized_round):
    """
    transforms a dictionary containing the values of a round instance
     into the corresponding round instance.
    :param serialized_round: structured dictionary.
    :return: instance of round.
    """
    deserialized_players = []
    for player in serialized_round['players']:
        deserialized_players.append(deserialize_player(player))
    r0und = Round(serialized_round['round_nb'],
                  serialized_round['tournament_id'],
                  deserialized_players)

    string_attribute = ['players_ranked', 'finished', 'players_sorted']
    for attribute in string_attribute:
        setattr(r0und, attribute, serialized_round[attribute])

    matchs = {}
    for match_nb, match in serialized_round['matchs'].items():
        matchs[int(match_nb)] = deserialize_match(match)
    setattr(r0und, 'matchs', matchs)
    return r0und


def deserialize_tournament(serialized_tournament):
    """
    transforms a dictionary containing the values of a tournament instance
     into the corresponding tournament instance.
    :param serialized_tournament: structured dictionary.
    :return: instance of tournament.
    """
    tour = Tournament(serialized_tournament['name'],
                      serialized_tournament['location'],
                      serialized_tournament['timer_type'],
                      serialized_tournament['description'])
    string_attributes = ['tournament_id',
                         'number_of_rounds',
                         'players_assigned']
    for attribute in string_attributes:
        setattr(tour, attribute, serialized_tournament[attribute])

    tour.start_date = str_to_date(serialized_tournament['start_date'])
    tour.end_date = str_to_date(serialized_tournament['end_date'])

    tour.rounds = []
    for r0und in serialized_tournament['rounds']:
        tour.rounds.append(deserialize_round(r0und))
    tour.list_of_players = []
    for player in serialized_tournament['list_of_players']:
        tour.list_of_players.append(deserialize_player(player))
    return tour


class DataBaseHandler:
    def __init__(self, database):
        self.database = database
        self.tournament_step = None

    def export_actor(self, actor):
        """
        transfers an instance of actor in a table of the database
        the instance of actor is transformed in a dictionnary first.
        :param actor: instance of actor
        :return: None
        """
        actors_table = self.database.table('actors')
        dictio = actor.actor_to_dict()
        actors_table.insert(dictio)

    def export_tournament(self, tournament, step):
        """
        transfers an instance of tournament in a table of the database,
        the instance of tournament is transformed in a dictionnary first.
        The step is the progress in the tournament.
        :param tournament: instance of tournament
        :param step: progress in the tournament.
        :return: None
        """
        self.tournament_step = step
        tournament_table = self.database.table('tournament')
        dictio = tournament.tournament_to_dict()
        tournament_table.insert(dictio)

    def import_actors(self):
        """
        import a list of actors instances transformed in a dictionnary,
        the dictionnary is converted in the list of the corresponding
        instances of actors.
        :return: the number of actors imported and
         the list of actors instances
        """
        actors_table = self.database.table('actors')
        serialized_actors = actors_table.all()
        actors = []
        for value in serialized_actors:
            actor = deserialize_actor(value)
            actors.append(actor)
        return len(serialized_actors), actors

    def import_tournament(self):
        """
        import a list of one tournament transformed in a dictionary,
        it is converted in  the corresponding instance of tournament.
        :return: the progress in tournament, and the instance of tournament.
        """
        tournament_table = self.database.table('tournament')
        list_serialized_tournament = tournament_table.all()
        serialized_tournament = list_serialized_tournament[0]
        tournament = deserialize_tournament(serialized_tournament)
        return self.tournament_step, tournament


if __name__ == '__main__':
    import datetime
    from tinydb import TinyDB

    handler = DataBaseHandler(TinyDB('db.json'))
    handler.database.table('actors').truncate()
    handler.database.table('tournament').truncate()

    """ Données """

    acteur1 = Actor("Skywalker", "Anakin", datetime.date(41, 5, 6), "M", 8)  # 2
    acteur2 = Actor("Skywalker", "Luke", datetime.date(19, 12, 7), "M", 21)  # 3
    acteur3 = Actor("Organa", "Leia", datetime.date(19, 12, 7), "F", 143)  # 8
    acteur4 = Actor("Tano", "Ahsoka", datetime.date(36, 11, 22), "F", 35)  # 5
    acteur5 = Actor("Yoda", "Maître", datetime.date(896, 10, 15), "M", 3)  # 1
    acteur6 = Actor("Palpatine", "Sheev", datetime.date(84, 2, 25), "M", 27)  # 4
    acteur7 = Actor("Kashyyyk", "Chewbacca", datetime.date(200, 8, 31), "M", 112)  # 7
    acteur8 = Actor("Solo", "Han", datetime.date(34, 7, 16), "M", 107)  # 6
    acteurs = [acteur1, acteur2, acteur3, acteur4, acteur5, acteur6, acteur7, acteur8]

    joueur1 = Player(acteur1, "00000001", 1)
    joueur2 = Player(acteur2, "00000001", 2)
    joueur3 = Player(acteur3, "00000001", 3)
    joueur4 = Player(acteur4, "00000001", 4)
    joueur5 = Player(acteur5, "00000001", 5)
    joueur6 = Player(acteur6, "00000001", 6)
    joueur7 = Player(acteur7, "00000001", 7)
    joueur8 = Player(acteur8, "00000001", 8)
    joueurs = [joueur1, joueur2, joueur3, joueur4, joueur5, joueur6, joueur7, joueur8]

    tournoi = Tournament(name="Star Wars Chess", location="In a galaxy far far away", timer_type="Bz",
                         description="Rien")
    tournoi.start_date = datetime.date.today()
    tournoi.define_players(joueurs)
    print("\n Initialisation : Joueurs \n")
    # print(tournoi.list_of_players)
    """ Tour 1"""
    tournoi.init_round(0)

    gagnants1 = [0, 1, 2, 0]
    tournoi.register_round_results(0, gagnants1)
    print("\n Tour 1 \n")
    # print(tournoi.rounds[0])
    # print(tournoi.list_of_players)

    """ Tour 2"""
    tournoi.init_round(1)

    gagnants2 = [1, 2, 2, 1]
    tournoi.register_round_results(1, gagnants2)
    print("\n Tour 2 \n")
    # print(tournoi.rounds[1])
    # print(tournoi.list_of_players)

    """ Tour 3"""
    tournoi.init_round(2)

    gagnants3 = [1, 1, 0, 2]
    tournoi.register_round_results(2, gagnants3)
    print("\n Tour 3 \n")
    # print(tournoi.rounds[2])
    # print(tournoi.list_of_players)

    """ Tour 4"""
    tournoi.init_round(3)

    gagnants4 = [2, 2, 1, 0]
    tournoi.register_round_results(3, gagnants4)
    print("\n Tour 4 \n")
    # print(tournoi.rounds[3])
    # print(tournoi.list_of_players)
    """ Fin partie """

    """ Test Acteur 
    print("\n ### Test acteur ### \n")
    acteur1.tournaments = ["00002200", "00002201"]
    for k in acteurs:
        handler.export_actor(k)
    # print(vars(acteur1))
    acters = handler.import_actors()
    print(acters)"""

    """Verification
    print(vars(acteur1))
    print(vars(acters[1][0]))
    """

    """ Test Joueur 
    print("\n ### Test joueur ### \n")
    """

    """ serialize 
    j3 = joueur3.player_to_dict()
    #print("\n dico2:", dico2)
    """

    """ deserialize 
    # acteur03 = deserialiaze_actor(dico2['actor'])
    # joueur03 = Player(acteur03, dico2['tournament_id'], dico2['player_id'])
    # joueur03.dict_to_player(dico2)
    joueur03 = deserialize_player(j3)
    print(vars(joueur3))
    print(vars(joueur03))
    print(vars(joueur3.actor))
    print(vars(joueur03.actor))
    """

    """ Test Match 
    print("\n ### Test Match ### \n")

    match = tournoi.rounds[0].matchs[0] """

    """ serialize 
    ser_match = match.match_to_dict()
    #print(ser_match) """

    """ deserialize 
    match0 = deserialize_match(ser_match)
    print(vars(match))
    print(vars(match0)) """

    """ Test Round """
    print("\n ### Test Round ### \n")

    round = tournoi.rounds[0]
    round_dico = round.round_to_dict()
    r0und = deserialize_round(round_dico)

    print("\n ## Test round ## \n")
    print(vars(round))
    print(vars(r0und))

    """ Test Tournament (serial, deserial)
    print("\n ### Test Tournament ### \n")"""
    # tour_dico = tournoi.tournament_to_dict()
    # print(tour_dico)
    # print("\n ## Test tournoi ## \n")
    # t0urnoi = deserialize_tournament(tour_dico)

    # print(vars(tournoi))
    # print(vars(t0urnoi))

    """ Tests export, import """
    print("\n ### Tests export, import ### \n")
    handler.export_tournament(tournoi, 3)
    tupl = handler.import_tournament()

    print(vars(tournoi))
    print(vars(tupl[1]))
    # problème dans matchs : clé '0' au lieu de 0