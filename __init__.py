from ovos_workshop.decorators import intent_handler, conversational_intent
from ovos_workshop.skills.game_skill import ConversationalGameSkill
from ovos_bus_client.message import Message
import random
import os.path
import json

class RaadHetGeluidSkill(ConversationalGameSkill):
    def __init__(self, *args, **kwargs):
        # game_image = os.path.join(os.path.dirname(__file__), "gui", "all", "game.png")
        # super().__init__(skill_voc_filename="raad_het_geluid", # <- the game name so it can be started
        #                  skill_icon=game_image,
        #                  game_image=game_image,
        #                  *args, **kwargs)
        super().__init__(skill_voc_filename="raad_het_geluid", *args, **kwargs)

    def initialize(self):
        self.reset_varaibles()

    def reset_varaibles(self):
        #Round variables
        self.current_round = 1
        self.points = 0

        self.quit_game = False
        self.play_exit_message = True

        #input variables
        self.reply = "None"

        self.repeat_intents= []

        #Intro variables
        self.intro_played = False

        #Debug funcions, set these to False for the release version
        self.skip_intro = True 
        self.skip_questions = True 

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
        self.play_exit_message = False
        self.log.debug("game abandoned! skill kicked out of active skill list!!!")
        self.deactivate()
        # self.stop()

    # TODO: doesn't work
    # @conversational_intent("RepeatQuestion.intent")
    # def state_change_test(self):
    #     self.speak("Herhaal")

#</editor-fold>

    def play_intro(self):
        self.reset_varaibles()
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

    def play_sound_audioclip(self, audio_clip):
        self.play_audio(f"{self.root_dir}/assets/audio/questions/{audio_clip}.mp3", wait=True)

    def play_answer_response(self, wasCorrect):
        self.reset_reply()
        self.current_round+=1
        message_number = random.randint(1, 5)
        if (wasCorrect):
            self.points+=1
            self.play_audio(f"{self.root_dir}/assets/audio/effects/feedback/sfx-correct.mp3", wait=True)
            self.play_audio(f"{self.root_dir}/assets/audio/effects/feedback/goed{message_number}.mp3", wait=True)
        else:
            self.play_audio(f"{self.root_dir}/assets/audio/effects/feedback/sfx-wrong.mp3", wait=True)
            self.play_audio(f"{self.root_dir}/assets/audio/effects/feedback/fout{message_number}.mp3", wait=True)

    def get_mic_input(self):
        if not self.is_playing:
            return 

        response =  self.ask_yesno("")
        if (response == 'yes' or response == 'no'): return response
        elif response in self.repeat_intents:
            return 'repeat'
        elif response == 'stop':
            return 'quit'
        else: return response
    
    def reset_reply(self):
        self.reply = "None"


    def play_game(self):
        self.player_quit = False
        exit_current_question_loop = False

        #TODO:get data from online databse 
        # Opening JSON file
        f = open(f'{self.root_dir}/quiz_data.json')

        # returns JSON object as a dictionary
        quiz_data = json.load(f)

        # Closing file
        f.close()

        q = quiz_data['questions_data']
        q_copy = []
        
        for item in q:
            q_copy.append(item)

        random.shuffle(q_copy)
        
        for object in q_copy:  
            object_name = q[object]
            right_question = object_name['right_question']
            questions = object_name['incorrect_questions'] + [right_question]
            random.shuffle(questions) # shuffle so correct isnt always the last
            audio_file_name = object_name['audio_file_name']

            if not self.is_playing:
                return 

            self.gui.show_text(f"Ronde {self.current_round}")
            if (self.skip_questions == False): self.play_audio(f"{self.root_dir}/assets/audio/effects/continue/geluid{self.current_round}.mp3", wait=True)
            if (self.skip_questions == False): self.play_sound_audioclip(audio_file_name)

            for question in questions:

                if not self.is_playing:
                    return 

                # If the player answered a question wrong or correct,
                # exit this set of questions and to to the next one
                if (exit_current_question_loop == True):
                    exit_current_question_loop = False
                    break

                self.gui.show_text(question, override_idle=True)
                self.play_question(question)

                # This will keep us in a single question loop until the player has answered a question right or wrong
                while not exit_current_question_loop:

                    if not self.is_playing:
                        return 

                    # Keep zlooking for a response until we have a valid one
                    while self.reply == "None":
                        self.reply = self.get_mic_input()

                    #Responce handler
                    if self.reply == 'yes' and question == right_question:
                        self.play_answer_response(True)
                        (exit_current_question_loop) = True
                        
                    elif (self.reply == 'yes' and question != right_question) or (self.reply == 'no' and question == right_question):
                        self.play_answer_response(False)
                        (exit_current_question_loop) = True

                    ## Set reply to none so that the player can still play the game
                    elif (self.reply == 'no' and question != right_question):
                        self.reset_reply()
                        # Get out of this while loop and to the next question
                        break
                    
                    # This took like half a day to implement correctly >:(
                    elif (self.reply == 'repeat'):
                        self.reset_reply()
                        self.play_sound_audioclip(audio_file_name)
                        self.play_question(question)

                    elif (self.reply == 'quit'):
                        # self.deactivate()
                        self.on_stop_game()

                    else:
                        if not self.is_playing:
                            return 
                        self.speak("Dat begreep ik niet. Zeg ja of nee. Zeg herhaal als je het geluid opnieuw wilt horen", expect_response=True, wait=True)
                        self.reset_reply()
            # self.set_skip_intro(False)
        
        # End of the game
        if (self.points == 1):
            self.gui.show_text("Je hebt een punt gescoord")
            self.play_audio(f"{self.root_dir}/assets/audio/effects/outro/einde1punt.mp3", wait=16)
        else:
            self.gui.show_text(f"Je hebt {self.points} punten gescoord")
            self.play_audio(f"{self.root_dir}/assets/audio/effects/outro/einde{self.points}punten.mp3", wait=16)

        while self.reply == "None":
            self.reply = self.get_mic_input()
            if self.reply == 'yes':
                self.reset_varaibles()
                self.play_game()
            elif (self.reply == 'no'): self.on_stop_game()
            else:
                self.speak("Zeg ja om opnieuw te spelen en nee om te stopen")
                self.reset_reply()

# <editor-fold desc="gameskill functions">

    def on_pause_game(self):
        """called by ocp_pipeline on 'pause' if game is being played"""
        # self.speak("can't pause, exiting")
        self.on_stop_game()

    def on_stop_game(self):
        # self.bus.emit(Message("mycroft.audio.speech.stop"))
        self.gui.show_text("Bedankt voor het spelen")
        if (self.play_exit_message == True):
            self.speak("Bedankt voor het spelen van Raad het Geluid. Tot ziens!")
            self.play_exit_message = False

    def on_save_game(self):
        """if your game has no save/load functionality you should
        speak a error dialog here"""
        self.speak("can't save")

    def on_load_game(self):
        """if your game has no save/load functionality you should
        speak a error dialog here"""
        self.speak("can't load")

#</editor-fold>