from ovos_workshop.skills import OVOSSkill
from ovos_workshop.decorators import intent_handler
import time
from ovos_utils.log import LOG
from ovos_bus_client.message import Message
from ovos_workshop.decorators import killable_intent, killable_event
from .quiz_data import rounds_data
import random

class RaadHetGeluidSkill(OVOSSkill):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def initialize(self):
        self.current_round = 0
        self.points = 0
        self.stop_called = False
        self.reply = None

        #intro stuff
        self.skip_intro = True #Debug funcion, keep this True for the release version
        self.intro_played = False

    #TODO: figure out while this still works despite intro_played being set to False
    # @intent_handler("SkipIntro.intent")
    # def skip_intro_intent(self):
    #     if not self.intro_played:
    #         self.intro_played = True
    #         self.bus.emit(Message("mycroft.audio.speech.stop"))

    @intent_handler("StartQuiz.intent")
    @killable_intent(msg='recognizer_loop:wakeword')
    def start_quiz(self):
        self.play_intro()
        
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

    def play_intro(self):
        self.gui.show_text("Raad het geluid", override_idle=True)
        # if self.intro_played:
        if self.skip_intro == False:
            self.play_audio(f"{self.root_dir}/assets/audio/effects/intro/intro.mp3", wait=24)

        self.intro_played = True
        self.play_game()

    def play_main_question(self, main_question, duration_main):
        self.play_audio(main_question)
        time.sleep(duration_main)

    def play_question_answer(self, question, duration_answers):
        self.gui.show_text(question, override_idle=True)
        self.speak(question)
        time.sleep(duration_answers)

    def play_answer_response(self, wasCorrect):
        self.reply = None
        message_number = random.randint(1, 5)
        if (wasCorrect):
            self.points+=1
            self.play_audio(f"{self.root_dir}/assets/audio/effects/feedback/sfx-correct.mp3", wait=.5)
            self.play_audio(f"{self.root_dir}/assets/audio/effects/feedback/goed{message_number}.mp3", wait=4)
        else:
            self.play_audio(f"{self.root_dir}/assets/audio/effects/feedback/sfx-wrong.mp3", wait=.5)
            self.play_audio(f"{self.root_dir}/assets/audio/effects/feedback/fout{message_number}.mp3", wait=4)


    def play_game(self):
        total_rounds = 5

        for round_num in range(0, total_rounds):
            self.current_round = round_num

            if round_num == total_rounds:
                break

            self.gui.show_text(f"Ronde {round_num + 1}")
            self.play_audio(f"{self.root_dir}/assets/audio/effects/continue/geluid{round_num+1}.mp3", wait=4)

            # TODO: need this later
            # random.sample(range(1, 100), 3)
            # [77, 52, 45]

            questions, correct_answers, main_question, = self.generate_round_data(round_num)

            # TODO: hardcoded audio lenght, fix in data file like Ronja
            self.play_main_question(main_question, 6)

            for question, correct_answer in zip(questions, correct_answers):
                self.play_question_answer(question, 3)

                while self.reply == None:
                    response = self.get_response().lower()
                    if (response == 'ja'): self.reply = 'ja'
                    elif (response == 'nee'): self.reply = 'nee'
                    elif (response == 'herhaal'): self.play_main_question(main_question, 6)
                    else: self.speak("Kies ja of nee. zeg herhaal as je het geluid opniuew wilt horen")


                if self.reply == 'ja' and correct_answer:
                    self.play_answer_response(True)
                    break
                elif (self.reply == 'ja' and not correct_answer) or (self.reply == 'nee' and correct_answer):
                    self.play_answer_response(False)
                    break
                elif self.reply == 'stop':
                    return
                ## Set reply to none so that the player can still play the game
                elif (self.reply == 'nee' and not correct_answer): self.reply = None

            # self.set_skip_intro(False)
        
        if (self.points == 1):
            self.gui.show_text("Je hebt een punt gescoord")
            self.play_audio(f"{self.root_dir}/assets/audio/effects/outro/einde1punt.mp3", wait=16)
        else:
            self.gui.show_text(f"Je hebt {self.points} punten gescoord")
            self.play_audio(f"{self.root_dir}/assets/audio/effects/outro/einde{self.points}punten.mp3", wait=16)
            

    def stop(self):
        time.sleep(2)
        self.gui.show_text('', override_idle=3)
        return
