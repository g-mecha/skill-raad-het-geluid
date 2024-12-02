# OVOS skill "Ronja en de piraten"
Unofficial voice skill for [OVOS](https://openvoiceos.org) of the game "Ronja en de Piraten" (Dutch for: "Ronja and the pirates").

## Original version
The voice version of Ronja was originally made for Google Home by [Q42](www.q42.nl), in collaboration with clients of [Visio](www.visio.org). 
Unfortunately Google deciced in 2023 to stop with their conversational action platfom and so this game was nog playable anymore for clients... ;(
In 2023 we therefore asked Q42 if they could  make a webversion of the voice games, to be played in any browser. These beautiful voice games are back to life again. 
The games are free to play here and are fully keyboard accessible too (TAB, ENTER, ESC for skipping the intro's):
[https://onbeperktspelen.visio.org](https://onbeperktspelen.visio.org) (Dutch only).
There's no voice input option on the website.

## Voice skill prototype
As a protoype I've created this voice skill for OVOS. Now it will live longer :)
The Python code is made with help of my dear friend ChatGPT and many thanks for the OVOS community for their support/knowledge that I could feed to the AI.
The skill is far from perfect, but a first try for me to make a voice skill this way. You can run into issues, so to stick to the pirate theme: be warned ;)
Otherwise: have fun playing the game!
And thanks of course to Q42 for their beatiful audio creation.

## To do:
* add setup file for easier install via PIP
* better stopping of the skill
* resume the next time at certain point in the game

## Intents
Ja, Nee, Sla over (to skip the intro's), Stop

## Keyboard/ physical button version
There's a [keyboard prototype of this skill](https://github.com/timonvanhasselt/skill_ronja_keyboard)
It uses `python-evdev` for the input events. It can also be used to play with big buttons (for instance for 'Ja' and 'Nee') 

## Video demo (YouTube)
[![Ronja en de piraten demo youtube](https://img.youtube.com/vi/-ol85-y1o88/0.jpg)](https://www.youtube.com/watch?v=-ol85-y1o88]/watch?v=-ol85-y1o88)
