from lib.display_driver import Label, DisplayDriver
from lib.nvs import NVSManager
from states.base import State
from lib.pronote import Pronote
import time

class PronoteState(State):
    def __init__(self, display: DisplayDriver, nvs: NVSManager):
        self.display_driver = display
        self.nvs = nvs
        self.labels = []
        self.pronote = Pronote()
        self.fetch_and_display_schedule()

    def navigate(self, button_id: str) -> State:
        if button_id == "LEFT": 
            # Clear horizontal line for day headers
            x_start = 0
            x_end = 320
            y_position = 20
            self.display_driver.draw_line(x_start, y_position, x_end, y_position, 0x0000, 1)
            
            # Clear vertical lines for time slots
            x_position = 30
            x_spacing = 58
            y_start = 0
            y_end = 240
            for i in range(5):
                self.display_driver.draw_line(x_position + i * x_spacing, y_start, x_position + i * x_spacing, y_end, 0x0000, 1)

            [label.erase(self.display_driver) for label in self.labels]
            from states.main_menu import MainMenuState
            return MainMenuState(self.display_driver, self.nvs)
        return self
    
    def fetch_and_display_schedule(self):
        events = self.pronote.fetch_calendar()
        
        # Display the fetched schedule on the screen
        day_labels = ["Mon", "Tue", "Wed", "Thu", "Fri"]
        time_slots = ["08", "09", "10", "11", "12", "01", "02", "03", "04", "05"]

        # Draw horizontal line for day headers
        x_start = 0
        x_end = 320
        y_position = 20
        self.display_driver.draw_line(x_start, y_position, x_end, y_position, 0xFFFF, 1)

        # Draw vertical lines for time slots
        x_position = 30
        x_spacing = 58
        y_start = 0
        y_end = 240
        for i in range(5):
            self.display_driver.draw_line(x_position + i * x_spacing, y_start, x_position + i * x_spacing, y_end, 0xFFFF, 1)

        # Draw day headers
        x_start = 35
        x_spacing = 58
        y_position = 6
        for i, day in enumerate(day_labels):
            label = Label(x_start + i * x_spacing, y_position, day, 0xFFFF, 0x0000)
            self.labels.append(label)
            label.draw(self.display_driver)
        
            
        # Draw time slots
        x_position = 3
        y_position = 28
        y_spacing = 22
        for i, time_slot in enumerate(time_slots):
            label = Label(x_position, y_position + i * y_spacing, time_slot, 0xFFFF, 0x0000)
            self.labels.append(label)
            label.draw(self.display_driver)
            
        # Draw time slots and events
        x_start = 35
        y_start = 27
        y_spacing = 22
        x_spacing = 58
        for time_index, time_slot in enumerate(time_slots):
            y_position = y_start + time_index * y_spacing
            for day_index in range(len(day_labels)):
                event = events[day_index][time_index]
                if event is None:
                    continue
                max_chars = 6
                subject_name = event.subjectName[:max_chars]
                subject_color = event.subjectColor
                label = Label(x_start + day_index * x_spacing, y_position, subject_name, subject_color, 0x0000)
                self.labels.append(label)
                label.draw(self.display_driver)
        
    def display(self):
        self.update_display_options(self.labels, self.options, self.current_option, self.previous_option, self.display_driver) 