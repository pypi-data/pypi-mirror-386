from otree.api import *


doc = """
Your app description
"""


class C(BaseConstants):
    NAME_IN_URL = '{{ app_name }}'
    PLAYERS_PER_GROUP = None
    NUM_ROUNDS = 1


class Subsession(BaseSubsession):
    pass


class Group(BaseGroup):
    pass


class Player(BasePlayer):
    num_errors = models.IntegerField(initial=0)


class Trial(BaseTrial):
    word = models.StringField()
    solution = models.StringField()
    response = models.StringField()


def creating_session(subsession: Subsession):
    # you can delete this read_csv if you prefer
    # to generate the trial data in your python code.
    rows = read_csv(__name__ + '/trials.csv', Trial)

    for p in subsession.get_players():
        for row in rows:
            Trial.create(player=p, word=row['word'], solution=row['solution'])


# PAGES
class Task(Page):
    trial_model = Trial
    trial_stimulus_fields = ['word']
    trial_response_fields = ['response']

    @staticmethod
    def before_next_page(player: Player, timeout_happened):
        # calculate the user's score
        for trial in Trial.filter(player=player):
            if trial.response != trial.solution:
                player.num_errors += 1


class Results(Page):
    @staticmethod
    def vars_for_template(player: Player):
        # get the variable 'trials' so it can be displayed in the HTML template
        trials = Trial.filter(player=player)
        return dict(trials=trials)


page_sequence = [Task, Results]
