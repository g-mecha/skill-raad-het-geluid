from ovos_utils.log import LOG
from ovos_bus_client.message import Message
from .quiz_data import questions_data
import random
from ovos_workshop.skills.game_skill import ConversationalGameSkill
from ovos_workshop.decorators import intent_handler, conversational_intent


class RaadHetGeluidSkill(ConversationalGameSkill):
    def __init__(self, *args, **kwargs):
        super().__init__(skill_voc_filename="raad_het_geluid", *args, **kwargs)
        self.current_round = 0
        self.points = 0
        self.player_quit = False
        self.reply = "None"
        self.repeat_intents = []
        self.intro_played = False
        self.skip_intro = True
        self.skip_questions = True
        self.state = 0
        # self._playing = False
        # self._paused = False

    def initialize(self):
        self.generate_intent_arrays()

    def generate_intent_arrays(self):
        f = open(f"{self.root_dir}/locale/{self.lang.lower()}/intents/RepeatQuestion.intent", "r")
        for intent in f:
            self.repeat_intents.append(intent.strip())

    def on_play_game(self):
        # self._playing = True
        self.play_intro()

    def on_pause_game(self):
        # self._paused = True
        super().on_pause_game()

    def on_resume_game(self):
        # self._paused = False
        super().on_resume_game()

    def on_stop_game(self):
        # self._playing = False
        self.player_quit = True
        self.gui.show_text("Bedankt voor het spelen")
        self.speak("Bedankt voor het spelen van Raad het Geluid. Tot ziens!")

    def play_intro(self):
        self.gui.show_text("Raad het geluid", override_idle=True)
        if not self.skip_intro:
            self.play_audio(f"{self.root_dir}/assets/audio/effects/intro/intro.mp3", wait=24)
        self.intro_played = True
        self.play_game()

    def play_game(self):
        self.current_round = 0
        self.points = 0
        self.player_quit = False
        # self._playing = True

        total_rounds = 5
        numbers_of_available_questions = len(questions_data)
        questions_to_use = random.sample(range(0, numbers_of_available_questions), total_rounds)

        for round_num in range(total_rounds):
            if self.player_quit:
                break

            self.current_round = round_num
            self.gui.show_text(f"Ronde {round_num + 1}")
            if not self.skip_questions:
                self.play_audio(f"{self.root_dir}/assets/audio/effects/continue/geluid{round_num + 1}.mp3", wait=True)

            questions, correct_answers, main_question = self.generate_round_data(questions_to_use[round_num])

            if not self.skip_questions:
                self.play_main_audioclip(main_question)

            for question, correct_answer in zip(questions, correct_answers):
                if self.player_quit:
                    break

                self.gui.show_text(question, override_idle=True)
                self.play_question(question)

                while True:
                    self.reply = self.get_mic_input()
                    if self.reply == "repeat":
                        self.play_main_audioclip(main_question)
                        self.play_question(question)
                    elif self.reply == "yes" and correct_answer:
                        self.points += 1
                        self.play_answer_response(True)
                        break
                    elif self.reply == "yes" or self.reply == "no":
                        self.play_answer_response(False)
                        break
                    elif self.reply == "quit":
                        self.on_stop_game()
                        return
                    else:
                        self.speak("Dat begreep ik niet. Zeg ja of nee.", expect_response=True)

        self.end_game()

    def generate_round_data(self, round_num):
        round_data = questions_data.get(round_num)
        if round_data:
            questions = round_data["questions"]
            correct_answers = round_data["correct_answers"]
            combined = list(zip(questions, correct_answers))
            random.shuffle(combined)
            questions, correct_answers = zip(*combined)
            return questions, correct_answers, self.root_dir + round_data["main_question"]
        else:
            LOG.error(f"No data found for round {round_num}")
            return None

    def play_answer_response(self, wasCorrect):
        self.reset_reply()
        message_number = random.randint(1, 5)
        if wasCorrect:
            self.play_audio(f"{self.root_dir}/assets/audio/effects/feedback/sfx-correct.mp3", wait=True)
            self.play_audio(f"{self.root_dir}/assets/audio/effects/feedback/goed{message_number}.mp3", wait=True)
        else:
            self.play_audio(f"{self.root_dir}/assets/audio/effects/feedback/sfx-wrong.mp3", wait=True)
            self.play_audio(f"{self.root_dir}/assets/audio/effects/feedback/fout{message_number}.mp3", wait=True)

    def reset_reply(self):
        self.reply = "None"

    def end_game(self):
        # self._playing = False
        if self.points == 1:
            self.gui.show_text("Je hebt een punt gescoord")
            self.play_audio(f"{self.root_dir}/assets/audio/effects/outro/einde1punt.mp3", wait=16)
        else:
            self.gui.show_text(f"Je hebt {self.points} punten gescoord")
            self.play_audio(f"{self.root_dir}/assets/audio/effects/outro/einde{self.points}punten.mp3", wait=16)
