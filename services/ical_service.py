from datetime import datetime, timedelta
from typing import Dict, List, Any
import uuid


class ICalService:
    def __init__(self):
        pass
    
    def generate_ical_from_itinerary(self, itinerary_data: Dict[str, Any]) -> str:
        """Generate iCalendar (.ics) file content from itinerary data"""
        location = itinerary_data.get('location', 'Unknown')
        origin = itinerary_data.get('origin', '')
        duration = itinerary_data.get('duration', 0)
        days = itinerary_data.get('days', [])
        
        # Create trip title
        trip_title = f"Trip to {location}"
        if origin:
            trip_title = f"Trip from {origin} to {location}"
        
        # Start building iCal content
        ical_lines = [
            "BEGIN:VCALENDAR",
            "VERSION:2.0",
            "PRODID:-//Travel AI//Trip Planner//EN",
            "CALSCALE:GREGORIAN",
            "METHOD:PUBLISH",
            f"X-WR-CALNAME:{trip_title}",
            "X-WR-TIMEZONE:America/Los_Angeles",
        ]
        
        # Add events for each day
        event_uid_prefix = str(uuid.uuid4())
        
        for day_idx, day in enumerate(days):
            day_num = day.get('day', day_idx + 1)
            date_str = day.get('date', '')
            items = day.get('items', [])
            
            # Parse date
            try:
                if date_str:
                    event_date = datetime.strptime(date_str, '%Y-%m-%d')
                else:
                    event_date = datetime.now() + timedelta(days=day_idx)
            except:
                event_date = datetime.now() + timedelta(days=day_idx)
            
            for item_idx, item in enumerate(items):
                time_str = item.get('time', '9:00 AM')
                title = item.get('title', 'Activity')
                description = item.get('description', '')
                item_location = item.get('location', location)
                duration_str = item.get('duration', '1 hour')
                
                # Parse time and create datetime
                start_time = self._parse_time_string(time_str)
                event_start = event_date.replace(
                    hour=start_time['hour'],
                    minute=start_time['minute']
                )
                
                # Calculate end time based on duration
                event_end = self._calculate_end_time(event_start, duration_str)
                
                # Format datetime for iCal (YYYYMMDDTHHMMSS)
                dtstart = event_start.strftime('%Y%m%dT%H%M%S')
                dtend = event_end.strftime('%Y%m%dT%H%M%S')
                
                # Generate unique ID
                event_uid = f"{event_uid_prefix}-{day_num}-{item_idx}"
                
                # Build event
                ical_lines.extend([
                    "BEGIN:VEVENT",
                    f"UID:{event_uid}",
                    f"DTSTAMP:{datetime.now().strftime('%Y%m%dT%H%M%S')}",
                    f"DTSTART:{dtstart}",
                    f"DTEND:{dtend}",
                    f"SUMMARY:{title}",
                    f"DESCRIPTION:{description}",
                    f"LOCATION:{item_location}",
                    "STATUS:CONFIRMED",
                    "SEQUENCE:0",
                    "END:VEVENT"
                ])
        
        # Close calendar
        ical_lines.append("END:VCALENDAR")
        
        return "\r\n".join(ical_lines)
    
    def _parse_time_string(self, time_str: str) -> Dict[str, int]:
        """Parse time string like '9:00 AM' or '14:30'"""
        time_str = time_str.strip().upper()
        
        # Default
        hour = 9
        minute = 0
        
        try:
            # Handle formats like "9:00 AM", "2:30 PM"
            if 'AM' in time_str or 'PM' in time_str:
                parts = time_str.replace('AM', '').replace('PM', '').strip().split(':')
                hour = int(parts[0])
                minute = int(parts[1]) if len(parts) > 1 else 0
                
                if 'PM' in time_str and hour != 12:
                    hour += 12
                elif 'AM' in time_str and hour == 12:
                    hour = 0
            else:
                # Handle 24-hour format
                parts = time_str.split(':')
                hour = int(parts[0])
                minute = int(parts[1]) if len(parts) > 1 else 0
        except:
            pass
        
        return {'hour': hour, 'minute': minute}
    
    def _calculate_end_time(self, start_time: datetime, duration_str: str) -> datetime:
        """Calculate end time based on duration string"""
        # Parse duration string like "1 hour", "2 hours", "30 minutes"
        duration_str = duration_str.lower()
        
        hours = 1  # default
        minutes = 0
        
        try:
            if 'hour' in duration_str:
                hours_match = duration_str.split('hour')[0].strip()
                hours = float(hours_match) if hours_match else 1
            elif 'minute' in duration_str:
                minutes_match = duration_str.split('minute')[0].strip()
                minutes = int(minutes_match) if minutes_match else 30
            elif 'overnight' in duration_str:
                hours = 12  # Overnight stays
        except:
            pass
        
        return start_time + timedelta(hours=hours, minutes=minutes)

