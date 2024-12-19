from ovos_workshop.skills import OVOSSkill
from ovos_workshop.decorators import intent_handler, conversational_intent
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
        self.reply = "None"

        #Intro variables
        self.intro_played = False

        #Debug funcions, set these to False for the release version
        self.skip_intro = True 
        self.skip_questions = True 
        self.state = 0

# <editor-fold desc="intents">

    @intent_handler("StartQuiz.intent")
    def start_quiz(self):
        self.player_quit = False
        self.play_intro()

    # TODO: figure out while this still works despite intro_played being set to False
    # @intent_handler("SkipIntro.intent")
    # def skip_intro_intent(self):
    #     if not self.intro_played:
    #         self.intro_played = True
    #         self.bus.emit(Message("mycroft.audio.speech.stop"))

    @intent_handler("StopPlaying.intent")
    def stop_playing(self):
        self.player_quit = True
        self.end_game()

    # TODO: doesn't work
    @conversational_intent("SkipIntro.intent")
    def state_change_test(self):
        self.state = 1

# </editor-fold>
        
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

    def get_mic_input(self, question):
        return self.ask_yesno(question)
    
    def reset_reply(self):
        self.reply = "None"
   
        # elif response in ['herhaal', 'herhaal de vraag', 'wat was de vraag', 'herhaal het geluid', 'wat was het geluid']:
        #     return 'repeat'      
        # elif response in ['stop raad het geluid', 'stop met spelen', 'ik ben klaar']:
        #     return 'quit'

        # else: return None

    # def test_func(self):   
    #     if self.state == 0:
    #         self.speak("0")
    #     elif self.state == 1:
    #         self.speak("1")
            

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
            if round_num == total_rounds or self.player_quit == True:
                break

            self.gui.show_text(f"Ronde {round_num + 1}")
            if (self.skip_questions == False): self.play_audio(f"{self.root_dir}/assets/audio/effects/continue/geluid{round_num+1}.mp3", wait=True)

            questions, correct_answers, main_question, = self.generate_round_data(questions_to_use[round_num])

            if (self.skip_questions == False): self.play_main_audioclip(main_question)

            for question, correct_answer in zip(questions, correct_answers):
                # Instantly end the runtime
                if (self.player_quit == True): return

                # This is ugly, but it works
                # If the player answered a question wrong or correct,
                # exit this set of questions and to to the next one
                if (can_Exit):
                    can_Exit = False
                    break

                self.gui.show_text(question, override_idle=True)

                while not can_Exit:

                    # Keep zlooking for a response until we have a valid one
                    while self.reply == "None":
                        self.reply = self.get_mic_input(question)

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

                    # End the program here when one fo the stop phrases is called
                    # Yes we have to do this twice
                    elif (self.reply == 'quit'):
                        self.end_game()
                        return

                    else:
                        self.speak("Dat begreep ik niet. Zeg ja of nee. Zeg herhaal als je het geluid opnieuw wilt horen", expect_response=True, wait=True)
                        self.reset_reply()
            # self.set_skip_intro(False)

    #</editor-fold>

    # <editor-fold desc="End of game logic">

        if (self.player_quit == True): return
        
        # End of the game
        if (self.points == 1):
            self.gui.show_text("Je hebt een punt gescoord")
            self.play_audio(f"{self.root_dir}/assets/audio/effects/outro/einde1punt.mp3", wait=16)
        else:
            self.gui.show_text(f"Je hebt {self.points} punten gescoord")
            self.play_audio(f"{self.root_dir}/assets/audio/effects/outro/einde{self.points}punten.mp3", wait=16)

        # while self.reply == None:
        #     self.reply = self.get_mic_input()
        #     if self.reply == 'yes': self.play_game()
        #     elif (self.reply == 'no'): self.end_game()
        #     else: self.speak("Zeg ja om opnieuw te spelen en nee om te stopen")            
    #</editor-fold>

    def end_game(self):
        self.bus.emit(Message("mycroft.audio.speech.stop"))
        self.gui.show_text("Bedankt voor het spelen")
        self.speak("Bedankt voor het spelen van Raad het Geluid. Tot ziens!")
        
