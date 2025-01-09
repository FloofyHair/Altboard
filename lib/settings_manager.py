# settings_manager.py
import network # type: ignore
import socket
import json
from lib.display_driver import Label
from lib.wifi_manager import WiFiManager
from lib.wifi_icons import WiFiIcons
from lib.settings_template import get_settings_html


class SettingsManager:
    def __init__(self, display, wifi_manager):
        self.display = display
        self.ap = None
        # Access Point (configuration endpoint) credentials
        self.ap_ssid = "Alt"
        self.ap_password = ""
        self.ip_address = None
        # Network connection credentials (loaded from config)
        self.wifi_ssid = None
        self.wifi_password = None
        self.pronote_link = None
        self.wifi_manager = wifi_manager
        self.menu = None
        
        # Load saved settings
        self.load_settings()

    def load_settings(self):
        """Load settings from file."""
        try:
            with open('config.json', 'r') as f:
                settings = json.load(f)
                self.wifi_ssid = settings.get('wifi_ssid')
                self.wifi_password = settings.get('wifi_password')
                self.pronote_link = settings.get('pronote_link')
        except:
            # If file doesn't exist or is corrupt, set defaults
            self.wifi_ssid = "LFSF_Students"
            self.wifi_password = "8cham0n1xD*"
            self.pronote_link = None

    def save_settings(self):
        """Save settings to file."""
        settings = {
            'wifi_ssid': self.wifi_ssid,
            'pronote_link': self.pronote_link
        }
        with open('config.json', 'w') as f:
            json.dump(settings, f)

    def start_access_point(self):
        """
        Start the Access Point and store the SSID and IP Address.
        """
        self.ap = network.WLAN(network.AP_IF)
        self.ap.active(True)
        self.ap.config(essid=self.ap_ssid, password='')
        self.ip_address = self.ap.ifconfig()[0]
        print(f"Access Point started. SSID: {self.ap_ssid}, IP: {self.ip_address}")

    def stop_access_point(self):
        """
        Stop the Access Point and clean up resources.
        """
        if self.ap:
            self.ap.active(False)
            self.ap = None

    def serve_web_page(self):
        """Serve configuration web page."""
        html = self.generate_html_content()  # Similar to your Arduino version
        
        server = socket.socket()
        server.bind(('0.0.0.0', 80))
        server.listen(1)
        
        while True:
            conn, addr = server.accept()
            print(f"Connection from {addr}")
            request = conn.recv(1024).decode()
            
            if "GET /submit" in request:
                # Parse parameters similar to Arduino version
                params = self.parse_request_params(request)
                self.wifi_ssid = params.get('networks')
                self.wifi_password = params.get('password')
                self.pronote_link = params.get('pronote')
                
                # Save the new settings
                self.save_settings()
                
                # Try to connect to WiFi
                self.wifi_manager.connect(self.wifi_ssid, self.wifi_password)
                break
                
            elif "GET /close" in request:
                break
                
            conn.send('HTTP/1.1 200 OK\n')
            conn.send('Content-Type: text/html\n')
            conn.send('\n')
            conn.send(html)
            conn.close()
            
        server.close()

    def scan_networks(self):
        """Scan for available WiFi networks."""
        wlan = network.WLAN(network.STA_IF)
        wlan.active(True)
        networks = wlan.scan()
        
        # Generate HTML options for networks
        network_options = ""
        for net in networks:
            ssid = net[0].decode('utf-8')
            network_options += f'<option value="{ssid}">{ssid}</option>'
        return network_options

    def generate_html_content(self):
        """Generate HTML content for settings page."""
        network_options = self.scan_networks()
        return get_settings_html(network_options)

    def start_settings_mode(self, menu):
        """Start the Access Point and serve the web page."""
        # Start AP first to get IP
        self.start_access_point()

        # Create AP info submenu
        ap_submenu = {
            "1": {
                "description": f"AP SSID: {self.ap_ssid}",
                "order": 1
            },
            "2": {
                "description": f"AP IP: {self.get_ip_address()}",
                "order": 2
            }
        }

        # Store current menu and switch to AP info submenu
        menu.menu_history.append(menu.current_menu)
        menu.current_menu = ap_submenu
        menu.current_selection_index = 0
        menu.display_menu()

    def exit_settings_mode(self):
        """Called when exiting the settings submenu."""
        print("Exiting settings mode...")
        self.serve_web_page()  # Show the configuration page
        self.stop_access_point()  # Stop the AP

        # Reconnect to saved WiFi if available
        if self.wifi_ssid and self.wifi_password:
            self.wifi_manager.connect(self.wifi_ssid, self.wifi_password)
        
        # Update main menu with new settings
        if hasattr(self, 'menu'):
            self.menu.update_settings_descriptions(self)
            self.menu.display_menu()  # Force menu redraw

    def get_ip_address(self):
        """
        Get the current IP address.
        """
        return self.ip_address if self.ip_address else "Not Available"

    def parse_request_params(self, request):
        """Parse GET parameters from request."""
        try:
            # Find the parameters section of the request
            params_start = request.find('?') + 1
            params_end = request.find(' HTTP')
            if params_start > 0 and params_end > params_start:
                params_str = request[params_start:params_end]
                # Split into individual parameters
                params = {}
                for param in params_str.split('&'):
                    if '=' in param:
                        key, value = param.split('=', 1)
                        # URL decode the value
                        value = value.replace('+', ' ')
                        value = value.replace('%20', ' ')
                        params[key] = value
                return params
        except Exception as e:
            print(f"Error parsing parameters: {e}")
        return {}

    @property
    def menu(self):
        return self._menu

    @menu.setter
    def menu(self, menu):
        self._menu = menu
        if menu is not None:
            menu.settings_manager = self
