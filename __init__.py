from ovos_workshop.decorators import intent_handler, conversational_intent
from ovos_utils.log import LOG
from ovos_workshop.skills.game_skill import ConversationalGameSkill
from ovos_workshop.intents import IntentBuilder
from ovos_bus_client.message import Message
from .quiz_data import questions_data
import random

class RaadHetGeluidSkill(ConversationalGameSkill):
    def __init__(self, *args, **kwargs):
        super().__init__(skill_voc_filename="raad_het_geluid", *args, **kwargs)

    def initialize(self):
        #Round variables
        self.current_round = 0
        self.points = 0

        #input variables
        self.reply = "None"

        self.repeat_intents= []

        #Intro variables
        self.intro_played = False

        #Debug funcions, set these to False for the release version
        self.skip_intro = True 
        self.skip_questions = True 
        self.state = 0

        self.generate_intent_arrays()

# <editor-fold desc="intents">

    def on_play_game(self):
        self.play_intro()
        # if not self.is_playing:
        #     self.speak_dialog("start.game")
        #     self.handle_intro()
        # else:
        #     self.speak_dialog("already.started")
        
    # TODO: figure out while this still works despite intro_played being set to False
    # @intent_handler("SkipIntro.intent")
    # def skip_intro_intent(self):
    #     if not self.intro_played:
    #         self.intro_played = True
    #         self.bus.emit(Message("mycroft.audio.speech.stop"))

    def on_abandon_game(self):
        self.log.debug("game abandoned! skill kicked out of active skill list!!!")
        self.on_stop_game()

    def on_stop_game(self):
        self.on_stop_game()
        

    # TODO: doesn't work
    @conversational_intent("RepeatQuestion.intent")
    def state_change_test(self):
        self.state = 1
        self.speak("Herhaal")

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

    #TODO: this is an temp hack fix, this should use ovos logic
    def generate_intent_arrays(self):
        f = open(f"{self.root_dir}/locale/{self.lang.lower()}/intents/RepeatQuestion.intent", "r")
        for intent in f:
            self.repeat_intents.append(intent.strip())
        

    def play_question(self, question):
        self.speak(question, wait=True)

    def play_main_audioclip(self, main_question):
        self.play_audio(main_question, wait=True)

    def play_answer_response(self, wasCorrect):
        self.reset_reply()
        message_number = random.randint(1, 5)
        if (wasCorrect):
            self.points+=1
            self.play_audio(f"{self.root_dir}/assets/audio/effects/feedback/sfx-correct.mp3", wait=True)
            self.play_audio(f"{self.root_dir}/assets/audio/effects/feedback/goed{message_number}.mp3", wait=True)
        else:
            self.play_audio(f"{self.root_dir}/assets/audio/effects/feedback/sfx-wrong.mp3", wait=True)
            self.play_audio(f"{self.root_dir}/assets/audio/effects/feedback/fout{message_number}.mp3", wait=True)

    def get_mic_input(self):
        response =  self.ask_yesno("")
        if (response == 'yes' or response == 'no'): return response
        elif response in self.repeat_intents:
            return 'repeat'
        # elif response in ['stop raad het geluid', 'stop met spelen', 'ik ben klaar']:
        #     return 'quit'
        else: return response
        
    
    def reset_reply(self):
        self.reply = "None"
            

    def play_game(self):
        total_rounds = 5
        self.player_quit = False
        can_Exit = False

    # <editor-fold desc="Main game logic">

        # Get the number of questions in quiz_data
        numbers_of_available_questions = len(questions_data)
        # Generate a random list of questions to use
        # This function will not create duplicates
        questions_to_use = random.sample(range(0, numbers_of_available_questions), total_rounds)

        for round_num in range(0, total_rounds):
            self.current_round = round_num

            # The player has reached the end of the game, quit the loop
            if round_num == total_rounds:
                break

            self.gui.show_text(f"Ronde {round_num + 1}")
            if (self.skip_questions == False): self.play_audio(f"{self.root_dir}/assets/audio/effects/continue/geluid{round_num+1}.mp3", wait=True)

            questions, correct_answers, main_question, = self.generate_round_data(questions_to_use[round_num])

            if (self.skip_questions == False): self.play_main_audioclip(main_question)

            for question, correct_answer in zip(questions, correct_answers):

                # If the player answered a question wrong or correct,
                # exit this set of questions and to to the next one
                if (can_Exit):
                    can_Exit = False
                    break

                self.gui.show_text(question, override_idle=True)
                self.play_question(question)

                # This will keep us in a single question loop until the player has answered a question right or wrong
                while not can_Exit:

                    # Keep zlooking for a response until we have a valid one
                    while self.reply == "None":
                        self.reply = self.get_mic_input()

                    #Responce handler
                    if self.reply == 'yes' and correct_answer:
                        self.play_answer_response(True)
                        can_Exit = True
                        
                    elif (self.reply == 'yes' and not correct_answer) or (self.reply == 'no' and correct_answer):
                        self.play_answer_response(False)
                        can_Exit = True

                    ## Set reply to none so that the player can still play the game
                    elif (self.reply == 'no' and not correct_answer):
                        self.reset_reply()
                        # Get out of this while loop and to the next question
                        break
                    
                    # This took like half a day to implement correctly >:(
                    elif (self.reply == 'repeat'):
                        self.reset_reply()
                        self.play_main_audioclip(main_question)
                        self.play_question(question)

                    else:
                        self.speak("Dat begreep ik niet. Zeg ja of nee. Zeg herhaal als je het geluid opnieuw wilt horen", expect_response=True, wait=True)
                        self.reset_reply()
            # self.set_skip_intro(False)

    #</editor-fold>

    # <editor-fold desc="End of game logic">
        
        # End of the game
        if (self.points == 1):
            self.gui.show_text("Je hebt een punt gescoord")
            self.play_audio(f"{self.root_dir}/assets/audio/effects/outro/einde1punt.mp3", wait=16)
        else:
            self.gui.show_text(f"Je hebt {self.points} punten gescoord")
            self.play_audio(f"{self.root_dir}/assets/audio/effects/outro/einde{self.points}punten.mp3", wait=16)

        while self.reply == None:
            self.reply =  self.ask_yesno("")
            if self.reply == 'yes': self.play_game()
            elif (self.reply == 'no'): self.on_stop_game()
            else: self.speak("Zeg ja om opnieuw te spelen en nee om te stopen")            
    #</editor-fold>

    def on_stop_game(self):
        self.gui.show_text("Bedankt voor het spelen")
        self.speak("Bedankt voor het spelen van Raad het Geluid. Tot ziens!")

        
