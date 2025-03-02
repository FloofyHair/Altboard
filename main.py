from lib.display_driver import DisplayDriver
from lib.buttons import ButtonManager
from lib.wifi_icons import WiFiIcons
from lib.wifi_manager import WiFiManager
from lib.nvs import NVSManager
from states import MainMenuState

class Application:
    def __init__(self):
        # Initialize display
        self.display = DisplayDriver()
        self.display.backlight.on()
        self.display.init_display()
        self.display.fill_screen(0x0000)
        
        # Initialize NVS
        self.nvs = NVSManager()
        
        # Initialize WiFi
        self.wifi_icons = WiFiIcons()
        self.wifi_manager = WiFiManager(self.display, self.wifi_icons)
        if self.nvs.get_string("ssid") and self.nvs.get_string("pass"):
            self.wifi_manager.connect(self.nvs.get_string("ssid"), self.nvs.get_string("pass"))
            
        # Initialize state with display and nvs
        self.current_state = MainMenuState(self.display, self.nvs)
        
        # Initialize button manager with state navigation callback
        self.button_manager = ButtonManager(self.handle_button)
        
    def handle_button(self, button_id: str):
        new_state = self.current_state.navigate(button_id)
        
        if new_state is not self.current_state:
            print("New State:", new_state)
            self.current_state = new_state

def main():
    app = Application()

if __name__ == "__main__":
    try:
        main()
        while True:
            pass
    except KeyboardInterrupt as e:
        print(f"User requested exit. Goodbye! Error: {e}")
