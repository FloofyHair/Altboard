from lib.display_driver import Label, DisplayDriver
from lib.nvs import NVSManager

class State:
    """Interface for menu states"""
    def update_display_options(self, labels, options, current_option, previous_option, display) -> None:
        labels[previous_option].update(display, f"  {options[previous_option]}")
        labels[current_option].update(display, f"> {options[current_option]}")
        
    def navigate(self, button_id: str) -> 'State':
        raise NotImplementedError
    
    def display(self) -> None:
        raise NotImplementedError 