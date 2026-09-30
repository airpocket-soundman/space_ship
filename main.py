import sys

from game import ui
from game.app import App

if __name__ == "__main__":
    # python main.py 720x720  のように画面サイズを選べる(既定は 640x480)
    screen = next((a for a in sys.argv[1:] if a in ui.SCREENS), "640x480")
    App(screen=screen).run()
