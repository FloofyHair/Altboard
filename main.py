from lib.display_driver import DisplayDriver
from lib.settings_manager import SettingsManager
from lib.menu import Menu
from lib.buttons import ButtonManager
from lib.wifi_icons import WiFiIcons
from lib.wifi_manager import WiFiManager

def main():
    # Initialize display
    display = DisplayDriver()
    display.backlight.on()
    display.init_display()
    # display.fill_screen(0x0000)

    # Initialize WiFi components
    wifi_icons = WiFiIcons()
    wifi_manager = WiFiManager(display, wifi_icons)

    # Initialize settings manager
    settings = SettingsManager(display, wifi_manager)
    
    # Initialize WiFi connection
    if settings.wifi_ssid and settings.wifi_password:
        print(f"Attempting to connect to saved network: {settings.wifi_ssid}")
        wifi_manager.connect(settings.wifi_ssid, settings.wifi_password)

    # Define menu structure with ordered dictionary
    menu_structure = {
    "1": {
        "description": "Pronote",
        "action": lambda: print("Viewing schedule..."),
        "disappears": True  # Menu will disappear when this option is selected
    },
    "2": {
        "description": "Settings",
        "submenu": {
            "1": {
                "description": "Update Settings",
                "action": lambda: settings.start_settings_mode(menu),
                "disappears": True
            },
            "2": {
                "description": "Network SSID",
                "label": {
                    "description": "SSID",
                    "value_func": lambda: settings.wifi_ssid or "Not Set"
                }
            },
            "3": {
                "description": "Network Pass",
                "label": {
                    "description": "Password",
                    "value_func": lambda: '*' * len(settings.wifi_password) if settings.wifi_password else "Not Set"
                }
            }
        }
    }
}

    # Initialize menu
    menu = Menu(menu_structure, display)
    menu.display_menu()

    # Initialize button manager with menu navigation callback
    ButtonManager(menu.navigate)

    # Connect settings and menu
    settings.menu = menu
    
    

if __name__ == "__main__":
    try:
        main()
        while True:
            pass
    except:
        print("User requested exit. Goodbye!")

