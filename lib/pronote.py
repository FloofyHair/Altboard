import urequests
import network
import time
import ntptime
import os  # For file handling
import json  # For JSON handling
import gc  # For garbage collection
from machine import Pin, SPI  # For SPI (if needed)
import sys  # For system operations

DEBUG = False

class Event:
    def __init__(self):
        self.start: str = ""
        self.end: str = ""
        self.subjectID: int = 0
        self.subjectName: str = ""
        self.teacher: str = ""
        self.location: str = ""
        self.exceptional: str = ""
        self.raw: str = ""
        self.subjectColor: int = 0

    def to_dict(self):
        return {
            "subject": self.subjectName,
            "teacher": self.teacher,
            "location": self.location,
            "exceptional": self.exceptional,
            "start": self.start,
            "end": self.end,
            "color": self.subjectColor
        }

class Pronote:
    FIRST_HOUR = 8
    SLOTS_PER_DAY = 10
    
    def __init__(self):
        # No SD card initialization
        self.week = [[None for _ in range(self.SLOTS_PER_DAY)] for _ in range(7)]
        # self.setup_spiffs()  # Remove SPIFFS setup

    def setup_spiffs(self):
        """Initialize SPIFFS."""
        try:
            spiffs.mount()  # Mount SPIFFS
            print("SPIFFS mounted successfully")
        except Exception as e:
            print(f"Failed to mount SPIFFS: {e}")

    def convert_to_tuple(self, date_str):
        # Parse the date string
        year = int(date_str[0:4])
        month = int(date_str[4:6])
        day = int(date_str[6:8])
        hour = int(date_str[9:11])
        minute = int(date_str[11:13])
        second = int(date_str[13:15])
        
        # Define the time zone offset (e.g., UTC+1)
        TIME_ZONE_OFFSET = -8  # Adjust this value as needed

        # Adjust hour for time zone
        hour += TIME_ZONE_OFFSET
        
        # Ensure hour is within valid range
        if hour < 0:
            hour += 24
            day -= 1  # Adjust day if necessary
        elif hour >= 24:
            hour -= 24
            day += 1  # Adjust day if necessary
        
        # Create a time tuple
        time_tuple = (year, month, day, hour, minute, second, 0, 0, -1)  # weekday and yearday are placeholders
        
        # Convert to timestamp and get the weekday and yearday
        timestamp = time.mktime(time_tuple)
        weekday = time.localtime(timestamp)[6]  # Get the weekday (0=Monday, 6=Sunday)
        yearday = time.localtime(timestamp)[7]  # Get the day of the year
        
        # Return the complete tuple
        return (year, month, day, hour, minute, second, weekday, yearday)

    def get_week_schedule(self, url, day):
        START_POS = 370000
        END_POS = 440000

        self.week = [[None for _ in range(self.SLOTS_PER_DAY)] for _ in range(7)]  # Reset week structure
        
        today_weekday = day[6]
        week_start = (day[0], day[1], day[2] - today_weekday, 0, 0, 0, 0, day[7] - today_weekday)
        week_end = (day[0], day[1], day[2] + (6 - today_weekday), 23, 59, 59, 6, day[7] + (6 - today_weekday))
        if DEBUG: print(f"Start: {week_start}, End: {week_end}")
        
        # Define a list of weekday names
        WEEKDAY_NAMES = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        
        # Fetching
        if DEBUG: print("Fetching data... ", end='')
        response = urequests.get(url)
        if DEBUG: print("Data fetched")
        
        if DEBUG: print("Parsing data... ")
        total_length = int(response.headers.get('Content-Length', 0))
        bytes_read = 0
        
        event_raw = ""
        event_data = ""
        event = Event()
        read = False
        
        # Skip bytes until START_POS
        chunk = 16384
        while bytes_read < START_POS:
            if DEBUG: print(f"Skipping {bytes_read} / {total_length} bytes")
            chunk_size = min(chunk, START_POS - bytes_read)
            response.raw.read(chunk_size)
            bytes_read += chunk_size

        while True:
            line = response.raw.readline()
            if not line:
                break
            if bytes_read > END_POS:
                break
            
            # Parsing
            if read:
                event_raw += line.decode('utf-8')
            if line.startswith(b"BEGIN:VEVENT"):
                read = True
            if line.startswith(b"END:VEVENT"):
                read = False
                bytes_read += len(event_raw)
                
                # Parsing event
                lines = event_raw.splitlines()
                event_lines = []
                for line in lines[1:]:
                    if line.startswith(' '):
                        event_lines[-1] += line[1:]
                    else:
                        event_lines.append(line)
                
                event_data = '\n'.join(event_lines)
                event_data = event_data.replace(";LANGUAGE=fr", "")
                event_data = event_data.replace("Cours annulé : ", "")
                event_data = event_data.replace("Prof. absent : ", "")
                
                # Parse event details using dictionary comprehension
                event_details = {
                    line.split(':', 1)[0]: line.split(':', 1)[1]
                    for line in event_data.splitlines()
                    if ':' in line
                }
                
                if 'SUMMARY' not in event_details:
                    continue

                # Parse summary to get subject and teacher
                summary_parts = event_details['SUMMARY'].split(' - ')
                subjects = summary_parts[0].split(' / ')
                subject_name = subjects[1].strip() if len(subjects) > 1 else subjects[0].strip()
                teacher = summary_parts[1] if len(summary_parts) > 1 else ""
                
                # Extract exceptional status from CATEGORIES
                exceptional = ""
                if 'CATEGORIES' in event_details:
                    categories = event_details['CATEGORIES']
                    if ' - ' in categories:
                        exceptional = categories.split(' - ')[1]
                
                event.subjectID = NAME_TO_ID.get(subject_name, 0)
                event.subjectName = SUBJECT_MAPPINGS.get(event.subjectID, ("Unknown", '\033[38;5;245m'))[0]
                event.location = event_details.get('LOCATION', "")
                event.teacher = teacher
                event.start = self.convert_to_tuple(event_details.get('DTSTART', "")) if event_details.get('DTSTART', "") != "" else (0, 0, 0, 0, 0, 0, 0, 0)
                event.end = self.convert_to_tuple(event_details.get('DTEND', "")) if event_details.get('DTEND', "") != "" else (0, 0, 0, 0, 0, 0, 0, 0)
                event.exceptional = exceptional
                event.raw = event_data
                event.subjectColor = SUBJECT_MAPPINGS.get(event.subjectID, ("Unknown", "#F5F5F5"))[1]
                
                # Calculate slots
                start_slot = max(1, min(self.SLOTS_PER_DAY, int((event.start[3] + (event.start[4] >= 30)) - self.FIRST_HOUR + 1)))
                end_slot = max(1, min(self.SLOTS_PER_DAY, int((event.end[3] + (event.end[4] >= 30)) - self.FIRST_HOUR)))
                
                if event.start[7] <= week_end[7] and event.end[7] >= week_start[7]:
                    if DEBUG: print(f"Added: ({bytes_read} / {total_length}) {self.pad_string(event.subjectName[:15], 15)} {self.pad_string(event.teacher[:15], 15)} {self.pad_string(str(event.start), 32)} {self.pad_string(str(event.end), 32)} {self.pad_string(event.location[:3], 3)} {self.pad_string(event.exceptional[:15], 15)}")
                    # Add event to the week schedule
                    for i in range(event.start[7], event.end[7] + 1):
                        if i >= week_start[7] and i <= week_end[7]:
                            day_index = (i+1) % 7  # Get the index for the day (0=Monday, 6=Sunday)
                            for slot in range(start_slot, end_slot + 1):
                                if self.week[day_index][slot - 1] is None:  # Adjust for 0-based index
                                    self.week[day_index][slot - 1] = event
                else:
                    if DEBUG: print(f"({bytes_read} / {total_length}) {self.pad_string(event.subjectName[:15], 15)} {self.pad_string(event.teacher[:15], 15)} {self.pad_string(str(event.start), 32)} {self.pad_string(str(event.end), 32)} {self.pad_string(event.location[:3], 3)} {self.pad_string(event.exceptional[:15], 15)}")
                    
                
                event = Event()
                event_data = ""
                event_raw = ""
        if DEBUG: print("Data parsed")
        return self.week

    def pad_string(self, s, width):
        """Pad the string to the specified width."""
        return (s + ' ' * width)[:width]  # Pad and truncate to the width

    def fetch_calendar(self):
        """Fetch the calendar from the file system."""
        try:
            with open("/calendar_data.json", "r") as file:
                calendar_data = json.load(file)
                # Turn dictionaries back into Event objects
                for day_index in range(len(calendar_data)):
                    for slot_index in range(len(calendar_data[day_index])):
                        event_dict = calendar_data[day_index][slot_index]
                        if event_dict is not None:
                            event = Event()
                            event.subjectName = event_dict["subject"]
                            event.teacher = event_dict["teacher"]
                            event.location = event_dict["location"]
                            event.exceptional = event_dict["exceptional"]
                            event.start = event_dict["start"]
                            event.end = event_dict["end"]
                            event.subjectColor = event_dict["color"]
                            calendar_data[day_index][slot_index] = event
                return calendar_data
        except OSError:
            print("Calendar data not found. Updating calendar...")
            self.update_calendar()
            
        return self.fetch_calendar()

    def update_calendar(self):
        """Update the calendar and save it to the file system."""
        url = "https://4040017y.index-education.net/pronote/ical/mesinformations.ics"
        url += "?icalsecurise=4E45AB2EF84A44092FC2D98FEE5F3DC581D61639DF4EEB2A8AC8038AC8F98E12E30F26CB036CC97AE0CC7E4B787E3B64"
        url += "&version=2024.3.8&param=266f3d32"
        day = time.localtime()
        week_schedule = self.get_week_schedule(url, day)

        # Convert Event objects to dictionaries for JSON storage
        for day_index in range(len(week_schedule)):
            for slot_index in range(len(week_schedule[day_index])):
                event = week_schedule[day_index][slot_index]
                if event is not None:
                    week_schedule[day_index][slot_index] = event.to_dict()  # Convert to dict

        gc.collect()

        try:
            with open("/calendar_data.json", "w") as file:  # Use .json for JSON storage
                json.dump(week_schedule, file)  # Store calendar data in JSON format
            print("Calendar data successfully saved to the file system.")
        except Exception as e:
            print(f"Error saving calendar data: {e}")

# Original name to ID mapping
NAME_TO_ID = {
    "Math Speciality (H)": 1,
    "Physics and Chemistry Speciality (H)": 2,
    "Personalized support": 3,
    "History Geography": 4,
    "English (US standards)": 5,
    "Complex Number Theory": 6,
    "Représentation théâtrale": 7,
    "Physical Education": 8,
    "Vacances": 9,
    "Férié": 10,
    "EMC": 11,
    "Spanish": 12,
    "Enseig. scientifique": 13,
    "Philosophy": 14,
    "Assembly": 15,
    "EXAMEN BACCALAUREAT": 16,
    "Révisions": 17,
    "Bac Mock exam": 18,
    "NO CLASS": 19,
    "College Counseling & Guidance": 20,
    "Concert": 21,
}

# ID to display name and color mapping
SUBJECT_MAPPINGS = {
    1: ("Math", 0xDAA4A4),      # #DAA4A4
    2: ("Physics", 0xE1C59F),    # #E1C59F
    3: ("Help", 0xDAE79A),        # #DAE79A
    4: ("History", 0xABEE95),    # #ABEE95
    5: ("English", 0x90F4B1),     # #90F4B1
    6: ("Math Expert", 0x8BFAF1), # #8BFAF1
    7: ("Theater", 0x88C3FF),    # #88C3FF
    8: ("Sports", 0x9389FF),      # #9389FF
    9: ("Vacances", 0xD88BFF),  # #D88BFF
    10: ("Férié", 0xFF8CE2),     # #FF8CE2
    11: ("EMC", 0xFF8DA0),       # #FF8DA0
    12: ("Spanish", 0xFFBC8F),   # #FFBC8F
    13: ("Science", 0xFFFD90),    # #FFFD90
    14: ("Philosophy", 0xC1FF91),# #C1FF91
    15: ("Assembly", 0x93FFA3),   # #93FFA3
    16: ("Exam", 0x94FFE3),      # #94FFE3
    17: ("Revision", 0x96DEFF),  # #96DEFF
    18: ("Mock Exam", 0x97A1FF),  # #97A1FF
    19: ("No Class", 0xCA98FF),  # #CA98FF
    20: ("Counseling", 0xFF9AF8),# #FF9AF8
    21: ("Concert", 0xFF9BBE),   # #FF9BBE
    0: ("Unknown", 0xF5F5F5),    # Gray (fallback)
}

# Exception mapping: original name to (ID, display name, color)
EXCEPTION_MAPPINGS = {
    "Exceptionnel": (1, "Exceptional", 0x2E6C70),  # #2E6C70
    "Remplacement": (2, "Replacement", 0x2B3D6E),   # #2B3D6E
    "Prof. absent": (3, "Teacher absent", 0x44286C), # #44286C
    "Changement de salle": (4, "Room change", 0x6A2664), # #6A2664
    "Conseil de classe": (5, "Class council", 0x682334), # #682334
    "Cours annulé": (6, "Class canceled", 0x653D20), # #653D20
    "Cours modifié": (7, "Class modified", 0x5D631E), # #5D631E
    "Report": (8, "Report", 0x2C601C), # #2C601C
    "Cours maintenu": (9, "Class maintained", 0x1A5E37), # #1A5E37
    "Cours déplacé": (10, "Class moved", 0x17545B), # #17545B
}
