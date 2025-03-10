from lib.display_driver import Label, DisplayDriver
from lib.nvs import NVSManager
from states.base import State
from states.pronote import PronoteState
from states.settings import SettingsState

class MainMenuState(State):
    def __init__(self, display: DisplayDriver, nvs: NVSManager):
        self.display_driver = display
        self.nvs = nvs
        self.options = ["Pronote", "Settings"]
        self.labels = [Label(10, 10 + i * 20, f"  {option}", 0xFFFF, 0x0000) for i, option in enumerate(self.options)]
        self.current_option = 0
        self.previous_option = 0
        [label.draw(self.display_driver) for label in self.labels]
        self.update_display_options(self.labels, self.options, self.current_option, self.previous_option, self.display_driver)
        
    def navigate(self, button_id: str) -> State:
        if button_id == "UP": self.current_option = (self.current_option - 1) % len(self.options)
        if button_id == "DOWN": self.current_option = (self.current_option + 1) % len(self.options)
        if button_id == "RIGHT":
            for label in self.labels: label.erase(self.display_driver)
            if self.current_option == 0: return PronoteState(self.display_driver, self.nvs)
            if self.current_option == 1: return SettingsState(self.display_driver, self.nvs)
        self.display()
        self.previous_option = self.current_option
        return self
    
    def display(self):
        self.update_display_options(self.labels, self.options, self.current_option, self.previous_option, self.display_driver) 