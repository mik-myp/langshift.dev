raw_topic = "  Python names  "
raw_sessions = "4"
minutes_per_session = 25

topic = raw_topic.strip()
sessions = int(raw_sessions)
total_minutes = sessions * minutes_per_session
hours = total_minutes // 60
minutes = total_minutes % 60

print(f"Topic: {topic}")
print(f"Sessions: {sessions}")
print(f"Total: {total_minutes} minutes ({hours}h {minutes}m)")
