from machine import Pin # type: ignore
import time

class Label:
    def __init__(self, x, y, text, color, bg_color, font_file='fonts/vga_8x8.bin'):
        self.x = x
        self.y = y
        self.text = text
        self.color = color
        self.bg_color = bg_color
        self.font_file = font_file
        self.visible = False

    def draw(self, display):
        """Draw the label on the display."""
        display.draw_text(self.x, self.y, self.text, self.color, self.bg_color, self.font_file)
        self.visible = True

    def erase(self, display):
        """Erase the label by redrawing with background color."""
        if self.visible:
            display.draw_text(self.x, self.y, self.text, self.bg_color, self.bg_color, self.font_file)
            self.visible = False

    def update(self, display, new_text):
        """Update the text of the label efficiently."""
        max_len = max(len(self.text), len(new_text))
        for i in range(max_len):
            current_char = self.text[i] if i < len(self.text) else None
            new_char = new_text[i] if i < len(new_text) else None

            if current_char != new_char:
                x_offset = self.x + i * 8  # Assuming font width is 8 pixels
                if current_char is not None:  # Erase the current character if it exists
                    display.draw_text(x_offset, self.y, current_char, self.bg_color, self.bg_color, self.font_file)
                if new_char is not None:  # Draw the new character if it exists
                    display.draw_text(x_offset, self.y, new_char, self.color, self.bg_color, self.font_file)

        self.text = new_text

class Picture:
    def __init__(self, x, y, width, height, image_data=None, color=0xFFFF, bg_color=0x0000):
        """
        Initialize the Picture object.

        :param x: Top-left x-coordinate.
        :param y: Top-left y-coordinate.
        :param width: Width of the image.
        :param height: Height of the image.
        :param image_data: A 2D list of 0s and 1s representing the image.
        :param color: Foreground color for 1s.
        :param bg_color: Background color for 0s.
        """
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.image_data = image_data  # 2D list of 0s and 1s
        self.color = color
        self.bg_color = bg_color
        self.visible = False

    def draw(self, display):
        """Draw the picture on the display."""
        if self.image_data:
            for row_index, row in enumerate(self.image_data):
                for col_index, pixel in enumerate(row):
                    pixel_color = self.color if pixel == 1 else self.bg_color
                    display.draw_pixel(self.x + col_index, self.y + row_index, pixel_color)
            self.visible = True

    def erase(self, display):
        """Erase the picture by filling it with the background color."""
        if self.visible:
            for row_index in range(self.height):
                for col_index in range(self.width):
                    display.draw_pixel(self.x + col_index, self.y + row_index, self.bg_color)
            self.visible = False


class DisplayDriver:
    def __init__(self):
        # Pin configuration
        self.data_pins = [Pin(i, Pin.OUT) for i in range(35, 43)] + [Pin(2, Pin.OUT)]
        self.dc = Pin(13, Pin.OUT)  # Data/Command
        self.wr = Pin(12, Pin.OUT)  # Write
        self.cs = Pin(11, Pin.OUT)  # Chip Select
        self.reset = Pin(14, Pin.OUT)  # Reset
        self.backlight = Pin(3, Pin.OUT)  # Backlight

        # Screen dimensions
        self.width = 320  # Logical width
        self.height = 240  # Logical height

    def transform_coordinates(self, x, y):
        return self.height - 1 - y, self.width - 1 - x

    def write_9bit(self, value, is_data=True):
        self.dc.value(is_data)
        mask = value
        for pin in self.data_pins:
            pin.value(mask & 1)
            mask >>= 1
        self.wr.off()
        self.wr.on()

    def init_display(self):
        self.reset.off()
        time.sleep(0.1)
        self.reset.on()
        time.sleep(0.1)

        self.cs.off()
        commands = [
            (0x01, False),
            (0x28, False),
            (0x3A, False),
            (0x55, True),
            (0x11, False),
        ]
        for cmd, is_data in commands:
            self.write_9bit(cmd, is_data)
            if cmd == 0x01:
                time.sleep(0.2)
        self.write_9bit(0x29, is_data=False)
        self.cs.on()

    def fill_screen(self, color):
        self.cs.off()
        self.write_9bit(0x2A, is_data=False)
        self.write_9bit(0x00)
        self.write_9bit(0x00)
        self.write_9bit((self.height - 1) >> 8)
        self.write_9bit((self.height - 1) & 0xFF)
        self.write_9bit(0x2B, is_data=False)
        self.write_9bit(0x00)
        self.write_9bit(0x00)
        self.write_9bit((self.width - 1) >> 8)
        self.write_9bit((self.width - 1) & 0xFF)
        self.write_9bit(0x2C, is_data=False)

        self.dc.value(1)
        high_byte, low_byte = (color >> 8) & 0xFF, color & 0xFF
        for _ in range(self.width * self.height):
            for i, pin in enumerate(self.data_pins):
                pin.value((high_byte >> i) & 1)
            self.wr.off()
            self.wr.on()
            for i, pin in enumerate(self.data_pins):
                pin.value((low_byte >> i) & 1)
            self.wr.off()
            self.wr.on()
        self.cs.on()

    def draw_text(self, x, y, text, color, bg_color, font_file='fonts/vga_8x8.bin', draw_bg=True):
        font_width = 8
        font_height = 8
        with open(font_file, 'rb') as f:
            for char_index, char in enumerate(text):
                f.seek(ord(char) * font_height)
                font_data = list(f.read(font_height))
                for row, byte in enumerate(font_data):
                    for col in range(8):
                        pixel_color = color if byte & (1 << (7 - col)) else (bg_color if draw_bg else None)
                        if pixel_color is not None:  # Skip drawing if no background is required
                            self.draw_pixel(x + col + char_index * font_width, y + row, pixel_color)


    def draw_pixel(self, x, y, color):
        x, y = self.transform_coordinates(x, y)
        self.cs.off()
        self.write_9bit(0x2A, is_data=False)
        self.write_9bit(x >> 8)
        self.write_9bit(x & 0xFF)
        self.write_9bit(x >> 8)
        self.write_9bit(x & 0xFF)
        self.write_9bit(0x2B, is_data=False)
        self.write_9bit(y >> 8)
        self.write_9bit(y & 0xFF)
        self.write_9bit(y >> 8)
        self.write_9bit(y & 0xFF)
        self.write_9bit(0x2C, is_data=False)

        self.dc.value(1)
        high_byte, low_byte = (color >> 8) & 0xFF, color & 0xFF
        for i, pin in enumerate(self.data_pins):
            pin.value((high_byte >> i) & 1)
        self.wr.off()
        self.wr.on()
        for i, pin in enumerate(self.data_pins):
            pin.value((low_byte >> i) & 1)
        self.wr.off()
        self.wr.on()
        self.cs.on()


# Main usage
if __name__ == "__main__":
    display = DisplayDriver()
    display.backlight.on()
    display.init_display()
    display.fill_screen(0x0000)

    # Using the Label class
    label = Label(10, 10, "Hello!", 0xFFFF, 0x0000)
    label.draw(display)
    time.sleep(2)
    label.update(display, "Updated Text")
    time.sleep(2)
    label.erase(display)
