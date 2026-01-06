
import datetime
from tools import list_calendar_events, check_availability, create_calendar_event

def test_tools():
    print("Testing Google Calendar Tools...")
    
    # Define a time range (Tomorrow 2 PM - 3 PM)
    tomorrow = datetime.datetime.now() + datetime.timedelta(days=1)
    start_time = tomorrow.replace(hour=14, minute=0, second=0, microsecond=0)
    end_time = tomorrow.replace(hour=15, minute=0, second=0, microsecond=0)
    
    start_str = start_time.isoformat() + "Z"
    end_str = end_time.isoformat() + "Z"

    print(f"\n1. Checking availability for {start_str}...")
    av_res = check_availability(start_str, end_str)
    print(f"Result: {av_res}")

    print(f"\n2. Creating a test event...")
    create_res = create_calendar_event("Test Meeting Agent", start_str, end_str, "test@example.com")
    print(f"Result: {create_res}")
    
    print(f"\n3. Listing events to verify...")
    list_res = list_calendar_events(start_str, end_str)
    print(f"Result: {list_res}")

if __name__ == "__main__":
    test_tools()
