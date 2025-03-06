import network # type: ignore
import _thread
import time

class WiFiManager:
    def __init__(self, display, wifi_icons):
        self.display = display
        self.wifi_connected_icon = wifi_icons.connected
        self.wifi_disconnected_icon = wifi_icons.disconnected
        self.thread_active = False
        self.is_connected = False
        
        # Show disconnected icon initially
        self.wifi_disconnected_icon.draw(self.display)

    def connect(self, ssid, password):
        """Connect to WiFi using provided credentials."""
        if not ssid or not password:
            print("No WiFi credentials provided")
            self.wifi_disconnected_icon.draw(self.display)
            return False

        def wifi_thread():
            try:
                wlan = network.WLAN(network.STA_IF)
                wlan.active(True)

                if not wlan.isconnected():
                    print(f"Connecting to WiFi: {ssid}")
                    wlan.connect(ssid, password)
                    timeout = 10
                    start_time = time.time()

                    while not wlan.isconnected():
                        if time.time() - start_time > timeout:
                            print("Failed to connect to WiFi")
                            self.is_connected = False
                            self.wifi_disconnected_icon.draw(self.display)
                            self.thread_active = False
                            return
                        time.sleep(1)

                if wlan.isconnected():
                    print("Connected to WiFi! IP:", wlan.ifconfig()[0])
                    self.is_connected = True
                    self.wifi_disconnected_icon.erase(self.display)
                    self.wifi_connected_icon.draw(self.display)

                self.thread_active = False
                
            except Exception as e:
                print(f"WiFi error: {e}")
                self.is_connected = False
                self.wifi_disconnected_icon.draw(self.display)
                self.thread_active = False

        if not self.thread_active:
            self.thread_active = True
            _thread.start_new_thread(wifi_thread, ())

def check_wifi_connection():
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    if wlan.isconnected():
        print("Wi-Fi is connected.")
    else:
        print("Wi-Fi is not connected.") 