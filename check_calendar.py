
import datetime
import json
from tools import list_calendar_events

def check_upcoming_events():
    print("Checking upcoming events on your calendar...")
    
    # Check next 7 days
    now = datetime.datetime.utcnow()
    end = now + datetime.timedelta(days=7)
    
    start_str = now.isoformat() + "Z"
    end_str = end.isoformat() + "Z"

    events_json = list_calendar_events(start_str, end_str)
    data = json.loads(events_json)
    
    if "events" in data and data["events"]:
        print(f"\nSUCCESS: Found {len(data['events'])} event(s):")
        for event in data["events"]:
            print(f"- {event['summary']} ({event['start']} to {event['end']})")
    else:
        print("\nNo events found (or error occurred).")
        print(data)

if __name__ == "__main__":
    check_upcoming_events()
