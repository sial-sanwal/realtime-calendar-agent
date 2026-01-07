
import os
import datetime
import json
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

SCOPES = ['https://www.googleapis.com/auth/calendar']

# Global variable to store user credentials (in-memory for the session)
USER_CREDENTIALS = None

def set_user_credentials(creds):
    global USER_CREDENTIALS
    USER_CREDENTIALS = creds

def get_calendar_service():
    """Authenticates with Google Calendar API using User Credentials if available, else local file."""
    creds = USER_CREDENTIALS
    
    # Fallback to local file if no user credentials provided (for testing/dev)
    if not creds:
        if os.path.exists('token.json'):
            creds = Credentials.from_authorized_user_file('token.json', SCOPES)
        
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                if os.path.exists('credentials.json'):
                    flow = InstalledAppFlow.from_client_secrets_file(
                        'credentials.json', SCOPES)
                    creds = flow.run_local_server(port=0)
                else:
                    return None # No credentials found
            
            # Save the credentials for the next run (only for local file mode)
            if not USER_CREDENTIALS and creds: # Only save if we're not using in-memory credentials and creds were obtained
                with open('token.json', 'w') as token:
                    token.write(creds.to_json())

    if not creds:
        print("Error: No valid credentials found or provided.")
        return None

    service = build('calendar', 'v3', credentials=creds)
    return service

def list_calendar_events(start_datetime: str, end_datetime: str):
    """
    Lists calendar events within a specified range.
    Args:
        start_datetime: ISO format string, e.g., '2024-01-01T09:00:00Z'
        end_datetime: ISO format string, e.g., '2024-01-01T17:00:00Z'
    """
    try:
        service = get_calendar_service()
        # Call the Calendar API
        print(f"Fetching events from {start_datetime} to {end_datetime}...")
        events_result = service.events().list(
            calendarId='primary', 
            timeMin=start_datetime,
            timeMax=end_datetime,
            singleEvents=True,
            orderBy='startTime'
        ).execute()
        events = events_result.get('items', [])

        if not events:
            return json.dumps({"events": [], "message": "No events found."})

        results = []
        for event in events:
            start = event['start'].get('dateTime', event['start'].get('date'))
            end = event['end'].get('dateTime', event['end'].get('date'))
            results.append({
                "summary": event.get('summary', 'No Title'),
                "start": start,
                "end": end
            })
        
        return json.dumps({"events": results})
    except Exception as e:
        print(f"Error calling Google Calendar API: {e}")
        return json.dumps({"error": str(e)})

def check_availability(start_datetime: str, end_datetime: str):
    """
    Checks if a time slot is available by looking for overlapping events.
    """
    try:
        events_json = list_calendar_events(start_datetime, end_datetime)
        data = json.loads(events_json)
        
        if "error" in data:
            return json.dumps(data)
            
        events = data.get("events", [])
        
        if not events:
            return json.dumps({"available": True, "message": "Slot is free."})
        else:
            return json.dumps({
                "available": False, 
                "message": f"Conflict detected. Found {len(events)} existing event(s).",
                "conflicts": events
            })
    except Exception as e:
        return json.dumps({"error": str(e)})

def create_calendar_event(summary: str, start_datetime: str, end_datetime: str, attendee_email: str = None):
    """
    Creates a new calendar event.
    """
    try:
        service = get_calendar_service()
        
        event = {
            'summary': summary,
            'start': {
                'dateTime': start_datetime,
                'timeZone': 'Asia/Karachi', 
            },
            'end': {
                'dateTime': end_datetime,
                'timeZone': 'Asia/Karachi',
            },
        }

        if attendee_email:
            event['attendees'] = [{'email': attendee_email}]

        print(f"Creating event: {summary} ({start_datetime} - {end_datetime})")
        event = service.events().insert(calendarId='primary', body=event).execute()
        
        return json.dumps({
            "status": "success", 
            "id": event.get('id'),
            "link": event.get('htmlLink'),
            "message": f"Event created: {event.get('htmlLink')}"
        })
    except Exception as e:
        print(f"Error creating event: {e}")
        return json.dumps({"error": str(e)})

tools_definition = [
  {
    "type": "function",
    "name": "list_calendar_events",
    "description": "List calendar events for a specific time range to see what is already booked.",
    "parameters": {
      "type": "object",
      "properties": {
        "start_datetime": {
          "type": "string",
          "description": "Start datetime in ISO 8601 format (e.g., 2024-01-01T09:00:00Z)"
        },
        "end_datetime": {
          "type": "string",
          "description": "End datetime in ISO 8601 format"
        }
      },
      "required": ["start_datetime", "end_datetime"]
    }
  },
  {
    "type": "function",
    "name": "check_availability",
    "description": "Check if a specific time slot is free.",
    "parameters": {
      "type": "object",
      "properties": {
        "start_datetime": {
          "type": "string",
          "description": "Start datetime in ISO 8601 format"
        },
        "end_datetime": {
          "type": "string",
          "description": "End datetime in ISO 8601 format"
        }
      },
      "required": ["start_datetime", "end_datetime"]
    }
  },
  {
    "type": "function",
    "name": "create_calendar_event",
    "description": "Book a new event on the calendar.",
    "parameters": {
      "type": "object",
      "properties": {
        "summary": {
          "type": "string",
          "description": "Title of the event"
        },
        "start_datetime": {
          "type": "string",
          "description": "Start datetime in ISO 8601 format"
        },
        "end_datetime": {
          "type": "string",
          "description": "End datetime in ISO 8601 format"
        },
        "attendee_email": {
          "type": "string",
          "description": "Email of the attendee"
        }
      },
      "required": ["summary", "start_datetime", "end_datetime"]
    }
  }
]
