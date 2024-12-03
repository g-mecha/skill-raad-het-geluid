from ovos_workshop.skills import OVOSSkill
from ovos_workshop.decorators import intent_handler
import time
from ovos_utils.log import LOG
from ovos_bus_client.message import Message
from ovos_workshop.decorators import killable_intent, killable_event
from .quiz_data import rounds_data
import random

class RonjaSkill(OVOSSkill):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def initialize(self):
        self.current_round = 0
        self.intro_played = False
        self.stop_called = False
        self.skip_intro = False  # Initialize the variable
        
    def generate_round_data(self, round_num):
        round_data = rounds_data.get(round_num)
        if round_data:
            questions = round_data['questions']
            correct_answers = round_data['correct_answers']

            combined = list(zip(questions, correct_answers))
            random.shuffle(combined)
            questions, correct_answers = zip(*combined)

            return (
                questions,
                correct_answers,
                self.root_dir + round_data['main_question'],
            )
        else:
            LOG.error(f"No data found for round {round_num}")
            return None

    @intent_handler("SkipIntro.intent")
    def skip_intro_intent(self):
        self.set_skip_intro(True)
        self.bus.emit(Message("mycroft.audio.speech.stop"))

    @intent_handler("StartQuiz.intent")
    @killable_intent(msg='recognizer_loop:wakeword')
    def start_quiz(self):
        self.play_game()

    def set_skip_intro(self, value):
        self.skip_intro = value

    def play_intro(self, intro, duration_intro):
        if not self.skip_intro:
            self.play_audio(intro)
            time_end = time.time() + duration_intro
            while time.time() < time_end and not self.skip_intro:
                time.sleep(0.1)

    def play_main_question(self, main_question, duration_main):
        self.play_audio(main_question)
        time.sleep(duration_main)

    def play_question_answer(self, question, question_audio_file, duration_answers):
        self.gui.show_text(question, override_idle=True)
        self.play_audio(question_audio_file)
        time.sleep(duration_answers)

    def play_correct_answer(self, correct_answer_audio, duration_correct):
        self.play_audio(correct_answer_audio)
        time.sleep(duration_correct)
        self.gui.show_text('Goed!', override_idle=True)

    def play_false_answer(self, false_answer_audio, duration_false):
        self.play_audio(false_answer_audio)
        self.gui.show_text('Ronja', override_idle=True)
        time.sleep(duration_false)

    def play_outro(self, outro, duration_outro):
        if outro:
            self.play_audio(outro)
            time_end = time.time() + duration_outro
            while time.time() < time_end and not self.skip_intro:
                time.sleep(0.1)

    def play_game(self):
        total_rounds = 5

        self.gui.show_text("Raad het geluid", override_idle=True)
        # self.play_audio(f"{self.root_dir}/assets/audio/effects/intro/intro.mp3", wait=24)

        intro_played = True

        if intro_played:

            for round_num in range(0, total_rounds):
                self.current_round = round_num

                self.gui.show_text(f"Ronde {round_num + 1}")
                self.play_audio(f"{self.root_dir}/assets/audio/effects/continue/geluid1.mp3", wait=4)

                questions, correct_answers, main_question, = self.generate_round_data(round_num)

                self.play_main_question(main_question, 5)

                # for question, correct_answer in zip(questions, correct_answers):
                #     self.play_main_question(main_question, 5)

                #     self.play_question_answer(question, question_audio_file, duration_answers)

                #     reply = None
                #     while reply not in ['ja', 'nee', 'stop']:
                #         response = self.get_response()

                #         if response:
                #             reply = response.lower()
                #         else:
                #             self.speak("Kies maar, ja of nee.")

                #     if reply == 'ja' and correct_answer:
                #         self.play_correct_answer(correct_answer_audio, duration_correct)
                #         self.play_outro(outro, duration_outro)
                #         break
                #     elif (reply == 'ja' and not correct_answer) or (reply == 'nee' and correct_answer):
                #         self.play_false_answer(false_answer_audio, duration_false)
                #         self.play_outro(outro, duration_outro)
                #         break
                #     elif reply == 'stop':
                #         return
                #     elif round_num == total_rounds:
                #         self.gui.show_text('Einde', override_idle=True)
                #         return

                # self.set_skip_intro(False)

    def stop(self):
        time.sleep(2)
        self.gui.show_text('', override_idle=3)
        return
