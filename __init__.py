from ovos_workshop.skills import OVOSSkill
from ovos_workshop.decorators import intent_handler
from ovos_utils.log import LOG
from ovos_bus_client.message import Message
from .quiz_data import questions_data
import random

class RaadHetGeluidSkill(OVOSSkill):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def initialize(self):
        #Round variables
        self.current_round = 0
        self.points = 0
        self.player_quit = False

        #input variables
        self.reply = None

        #Intro variables
        self.skip_intro = True #Debug funcion, set this to False for the release version
        self.intro_played = False

#<editor-fold desc="intents">
    @intent_handler("StartQuiz.intent")
    def start_quiz(self):
        self.player_quit = False
        self.play_intro()

    #TODO: figure out while this still works despite intro_played being set to False
    # @intent_handler("SkipIntro.intent")
    # def skip_intro_intent(self):
    #     if not self.intro_played:
    #         self.intro_played = True
    #         self.bus.emit(Message("mycroft.audio.speech.stop"))

    @intent_handler("StopPlaying.intent")
    def stop_playing(self):
        self.player_quit = True
        self.end_game()

#</editor-fold>
        
    def generate_round_data(self, round_num):
        round_data = questions_data.get(round_num)
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

    def play_sound_audioclip(self, main_question):
        self.play_audio(main_question, wait=True)

    def play_sound_question(self, question):
        self.gui.show_text(question, override_idle=True)
        self.speak(question, wait=True)

    def play_answer_response(self, wasCorrect):
        self.reply = None
        message_number = random.randint(1, 5)
        if (wasCorrect):
            self.points+=1
            self.play_audio(f"{self.root_dir}/assets/audio/effects/feedback/sfx-correct.mp3", wait=True)
            self.play_audio(f"{self.root_dir}/assets/audio/effects/feedback/goed{message_number}.mp3", wait=True)
        else:
            self.play_audio(f"{self.root_dir}/assets/audio/effects/feedback/sfx-wrong.mp3", wait=True)
            self.play_audio(f"{self.root_dir}/assets/audio/effects/feedback/fout{message_number}.mp3", wait=True)

    def get_mic_input(self):
        response = self.get_response().lower()
        if response in ['ja', 'jazeker', 'ja zeker', 'ja zeker ja']: 
            return 'ja'
        elif response in ['nee', 'nee hoor']:
            return 'nee'
        # elif response == "Herhaal":
        #     return 'repeat all'
        # elif response in ['nee', 'nee hoor']:
        #     return 'repeat question'
        # elif response in ['nee', 'nee hoor']:
        #     return 'repeat sound'
        # else: return None


    def play_game(self):
        total_rounds = 5
        self.player_quit = False

        # Get the number of questions in quiz_data
        numbers_of_available_questions = len(questions_data)
        # Generate a random list of questions to use
        # This function will not create duplicates
        questions_to_use = random.sample(range(0, numbers_of_available_questions), total_rounds)

        for round_num in range(0, total_rounds):
            self.current_round = round_num

            # The player has reached the end of the game, quit the loop
            if round_num == total_rounds or self.player_quit == True:
                break

            self.gui.show_text(f"Ronde {round_num + 1}")
            self.play_audio(f"{self.root_dir}/assets/audio/effects/continue/geluid{round_num+1}.mp3", wait=True)

            questions, correct_answers, main_question, = self.generate_round_data(questions_to_use[round_num])

            self.play_sound_audioclip(main_question)

            for question, correct_answer in zip(questions, correct_answers):
                # Instantly end the runtime
                if (self.player_quit == True): return
                self.play_sound_question(question)

                # Keep looking for a response until we have a valid one
                while self.reply == None:

                    self.reply = self.get_mic_input()

                    # 
                    # # 

                    # 
                    # elif (response == 'herhaal'): self.play_sound_audioclip(main_question)
                    # # End the program here when one fo the stop phrases is called
                    # # Yes we have to do this twice
                    # elif response in ['stop raad het geluid', 'stop met spelen', 'ik ben klaar']:
                    #     self.end_game()
                    #     return
                    # else: self.speak("Dat begreep ik niet. Zeg jazeker of nee hoor. Zeg herhaal als je het geluid opnieuw wilt horen", expect_response=True, wait=True)


                if self.reply == 'yes' and correct_answer:
                    self.play_answer_response(True)
                    break
                elif (self.reply == 'yes' and not correct_answer) or (self.reply == 'no' and correct_answer):
                    self.play_answer_response(False)
                    break
                ## Set reply to none so that the player can still play the game
                elif (self.reply == 'no' and not correct_answer): self.reply = None

            # self.set_skip_intro(False)

        if (self.player_quit == True): return
        
        # End of the game
        if (self.points == 1):
            self.gui.show_text("Je hebt een punt gescoord")
            self.play_audio(f"{self.root_dir}/assets/audio/effects/outro/einde1punt.mp3", wait=16)
        else:
            self.gui.show_text(f"Je hebt {self.points} punten gescoord")
            self.play_audio(f"{self.root_dir}/assets/audio/effects/outro/einde{self.points}punten.mp3", wait=16)

        while self.reply == None:
            self.reply = self.get_mic_input()
            if self.reply == 'yes': self.play_game()
            elif (self.reply == 'no'): self.end_game()
            else: self.speak("Kies jazeker of nee hoor.")            
    

    def end_game(self):
        self.bus.emit(Message("mycroft.audio.speech.stop"))
        self.gui.show_text("Bedankt voor het spelen")
        self.speak("Bedankt voor het spelen van Raad het Geluid. Tot ziens!")
        
