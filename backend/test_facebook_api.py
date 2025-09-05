#!/usr/bin/env python3

import http.client
import json

conn = http.client.HTTPSConnection("facebook-scraper3.p.rapidapi.com")

headers = {
    'x-rapidapi-key': "f3435e87bbmsh512cdcef2082564p161dacjsnb5f035481232",
    'x-rapidapi-host': "facebook-scraper3.p.rapidapi.com"
}

# Test con Miami - exactamente como el usuario lo tiene
conn.request("GET", "/search/events?query=miami&start_date=2025-09-04&end_date=2025-10-04", headers=headers)

res = conn.getresponse()
data = res.read()

response = data.decode("utf-8")
print("RAW RESPONSE:")
print(response)
print("\n" + "="*50 + "\n")

try:
    json_data = json.loads(response)
    events = json_data.get('events', [])
    print(f"TOTAL EVENTS: {len(events)}")
    print("\nEVENT TITLES:")
    for i, event in enumerate(events, 1):
        print(f"{i}. {event.get('title', 'No title')}")
except Exception as e:
    print(f"Error parsing JSON: {e}")