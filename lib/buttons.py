from machine import Pin # type: ignore

class ButtonManager:
    # Button pin mappings
    BUTTON_PINS = {
        "UP": 16,
        "DOWN": 6,
        "LEFT": 15,
        "RIGHT": 7,
        "SELECT_A": 4,
        "SELECT_B": 5
    }

    def __init__(self, callback):
        """
        Initialize button manager.
        
        :param callback: Function to call when button state changes
        """
        self.callback = callback
        self.pins = {}
        self.states = {}
        
        for button_id, pin_num in self.BUTTON_PINS.items():
            pin = Pin(pin_num, Pin.IN, Pin.PULL_UP)
            pin.irq(trigger=Pin.IRQ_FALLING | Pin.IRQ_RISING, 
                   handler=lambda p, bid=button_id: self._handle_interrupt(p, bid))
            self.pins[button_id] = pin
            self.states[button_id] = True

    def _handle_interrupt(self, pin, button_id):
        """Handle button interrupt and call callback if button is released."""
        new_state = pin.value()
        if self.states[button_id] == False and new_state == True:
            self.callback(button_id)
        self.states[button_id] = new_state 