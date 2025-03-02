import network  # type: ignore
import socket
import _thread
from lib.display_driver import Label, DisplayDriver
from lib.nvs import NVSManager
from states.base import State
from lib.settings_template import get_settings_html, get_updated_html  # Import the HTML template function
import time

class UpdateSettingsState(State):
    def __init__(self, display: DisplayDriver, nvs: NVSManager):
        self.display_driver = display
        self.nvs = nvs
        
        # Configuration for the Access Point
        self.AP_SSID = "TestAP"
        self.AP_PASSWORD = ""  # Empty string for no password
        
        # Start the access point
        self.ap = network.WLAN(network.AP_IF)
        self.ap.active(True)
        self.ap.config(essid=self.AP_SSID, password=self.AP_PASSWORD)
        
        # Wait for AP to be active
        while not self.ap.active():
            pass
        
        # Get and print AP details
        self.ip = self.ap.ifconfig()[0]  # Store the IP address
        print(f"\nAccess Point Started!")
        print(f"SSID: {self.AP_SSID}")
        print(f"Password: {self.AP_PASSWORD or 'No password'}")
        print(f"IP Address: http://{self.ip}")
        
        # Initialize server attributes
        self.server = None
        self.server_thread = None
        self.running = True  # Flag to control server loop
        
        # Start web server in a separate thread
        self.start_server()
        
        # Setup display
        self.options = ["Access Point Started",
                        f"AP SSID: {self.AP_SSID}", 
                        f"IP: {self.ip}"]
        self.labels = [Label(10, 10 + i * 20, f"  {option}", 0xFFFF, 0x0000) for i, option in enumerate(self.options)]
        self.current_option = 0
        self.previous_option = 0
        [label.draw(self.display_driver) for label in self.labels]
        self.update_display_options(self.labels, self.options, self.current_option, self.previous_option, self.display_driver)

    def start_server(self):
        """Start the web server in a separate thread."""
        self.server = socket.socket()
        self.server.bind(('0.0.0.0', 80))  # Bind to all interfaces
        self.server.listen(1)
        print("Web server running...")

        def run_server():
            while self.running:  # Check the running flag
                try:
                    conn, addr = self.server.accept()
                    print(f"Connection from {addr}")
                    request = conn.recv(1024).decode()
                    print(f"Request: {request}")

                    # Check if the request is for the submit action
                    if "GET /submit" in request:
                        # Extract the network and password from the request
                        network_name = self.extract_query_param(request, "networks")
                        password = self.extract_query_param(request, "password")
                        print(f"Network: {network_name}, Password: {password}")

                        # Save the settings to NVS
                        self.nvs.set_string("ssid", network_name)
                        self.nvs.set_string("pass", password)

                        # Respond with a success message or redirect
                        html = get_updated_html()  # Use the new updated HTML function
                        conn.send('HTTP/1.0 200 OK\r\nContent-type: text/html\r\n\r\n')
                        conn.send(html.encode())
                        conn.close()
                        continue  # Skip the rest of the loop for this request

                    # Generate the HTML page using the template
                    network_options = self.get_available_networks()  # Get available networks
                    html = get_settings_html(network_options, self.nvs)  # Pass NVS to the template

                    conn.send('HTTP/1.0 200 OK\r\nContent-type: text/html\r\n\r\n')
                    conn.send(html.encode())
                    conn.close()
                except Exception as e:
                    if self.running:  # Only print if the server is still running
                        print(f"Error handling connection: {e}")
                    try:
                        conn.close()
                    except:
                        pass

        self.server_thread = _thread.start_new_thread(run_server, ())

    def extract_query_param(self, request, param):
        """Extract a query parameter from the request."""
        try:
            # Find the start of the parameter
            start = request.index(param + "=") + len(param) + 1
            end = request.index("&", start) if "&" in request[start:] else len(request)
            return request[start:end].replace("%20", " ")  # Decode URL-encoded spaces
        except ValueError:
            return ""

    def get_available_networks(self):
        """Scan for available Wi-Fi networks and return them as HTML options."""
        wlan = network.WLAN(network.STA_IF)
        wlan.active(True)
        networks = wlan.scan()
        options = ''.join(f'<option value="{net[0].decode()}">{net[0].decode()}</option>' for net in networks)
        return options

    def stop_server(self):
        """Stop the web server."""
        self.running = False  # Set the flag to stop the server loop
        if self.server:
            self.server.close()
            self.server = None
            print("Web server stopped.")

    def navigate(self, button_id: str) -> State:
        if button_id == "UP": self.current_option = (self.current_option - 1) % len(self.options)
        if button_id == "DOWN": self.current_option = (self.current_option + 1) % len(self.options)
        if (button_id == "LEFT"):
            self.ap.active(False)
            self.stop_server()
            [label.erase(self.display_driver) for label in self.labels]
            from states.settings import SettingsState
            return SettingsState(self.display_driver, self.nvs)  # Return to SettingsState
        
        self.display()
        self.previous_option = self.current_option
        return self
    
    def display(self):
        self.update_display_options(self.labels, self.options, self.current_option, self.previous_option, self.display_driver)