from lib.display_driver import Label

class Label:
    def __init__(self, description, value_func):
        self.description = description
        self.value_func = value_func

    def get_value(self):
        return self.value_func()

    def __str__(self):
        return f"{self.description}: {self.get_value()}"

class Menu:
    # Define colors for different menu item types
    COLORS = {
        'default': 0xFFFF,  # White for info-only items
        'action': 0x07E0,   # Green for action items
        'submenu': 0x001F,  # Blue for submenu items
    }

    def __init__(self, menu_structure, display):
        """
        Initialize the menu system.
        
        :param menu_structure: Dictionary defining the menu hierarchy.
        :param display: Display driver instance for rendering the menu.
        """
        self.menu_structure = menu_structure
        self.display = display
        self.current_menu = menu_structure
        self.menu_history = []
        self.current_selection_index = 0
        self.labels = []
        self.settings_manager = None  # Will be set by settings manager

    def get_item_color(self, menu_item):
        """Determine the color based on menu item type."""
        if "submenu" in menu_item:
            return self.COLORS['submenu']
        elif "action" in menu_item:
            return self.COLORS['action']
        return self.COLORS['default']

    def display_menu(self):
        """Render the current menu on the display."""
        # Clear previous labels
        self.clear_menu()
        
        # Get ordered menu items
        items = list(self.current_menu.items())
        
        for i, (key, item) in enumerate(items):
            description = item["description"]
            color = self.get_item_color(item)
            
            # Handle labels
            if "label" in item:
                label = Label(item["label"]["description"], item["label"]["value_func"])
                description += f": {label.get_value()}"
            
            prefix = "> " if i == self.current_selection_index else "  "
            label = Label(10, 20 + i * 20, f"{prefix}{description}", color, 0x0000)
            self.labels.append(label)
            label.draw(self.display)

    def update_selection(self, previous_index, current_index):
        """Update the selection marker on the display."""
        # Update the previously selected label
        if 0 <= previous_index < len(self.labels):
            text = self.labels[previous_index].text
            updated_text = f"  {text[2:]}"
            self.labels[previous_index].update(self.display, updated_text)

        # Update the currently selected label
        if 0 <= current_index < len(self.labels):
            text = self.labels[current_index].text
            updated_text = f"> {text[2:]}"
            self.labels[current_index].update(self.display, updated_text)

    def navigate(self, button_id):
        """
        Handle menu navigation based on button press.
        
        :param button_id: Button identifier for navigation action.
        """
        previous_index = self.current_selection_index
        options = list(self.current_menu.keys())

        if button_id == "UP":
            self.current_selection_index = (self.current_selection_index - 1) % len(self.current_menu)
        elif button_id == "DOWN":
            self.current_selection_index = (self.current_selection_index + 1) % len(self.current_menu)
        elif button_id == "RIGHT":
            selected_option = options[self.current_selection_index]
            selected_item = self.current_menu[selected_option]

            if "submenu" in selected_item:
                self.menu_history.append(self.current_menu)
                self.current_menu = selected_item["submenu"]
                self.current_selection_index = 0
                self.display_menu()
            elif "action" in selected_item and callable(selected_item["action"]):
                if selected_item.get("disappears", False):
                    self.clear_menu()  # Clear the menu
                selected_item["action"]()  # Execute the action
            return
        elif button_id == "LEFT" and self.menu_history:
            self.current_menu = self.menu_history.pop()
            self.current_selection_index = 0
            self.display_menu()
            return

        self.update_selection(previous_index, self.current_selection_index)

    def clear_menu(self):
        """Clear all menu items from the display."""
        for label in self.labels:
            label.erase(self.display)
        self.labels = []

    def update_settings_descriptions(self, settings):
        """Update settings menu items with current values."""
        if "2" in self.menu_structure and "submenu" in self.menu_structure["2"]:
            settings_menu = self.menu_structure["2"]["submenu"]
            settings_menu["1"]["description"] = f"Network SSID: {settings.wifi_ssid or 'Not Set'}"
            settings_menu["2"]["description"] = f"Network Pass: {'*' * len(settings.wifi_password) if settings.wifi_password else 'Not Set'}"
            settings_menu["3"]["description"] = f"Pronote Link: {settings.pronote_link or 'Not Set'}"
            
            # Refresh display if we're currently in the settings menu
            if self.current_menu == settings_menu:
                self.display_menu()
