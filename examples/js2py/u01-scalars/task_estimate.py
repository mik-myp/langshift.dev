raw_title = "  Read Python basics  "
raw_minutes = "95"
title = raw_title.strip()
estimated_minutes = int(raw_minutes)
hours = estimated_minutes // 60
minutes = estimated_minutes % 60
print(f"Task: {title}")
print(f"Estimate: {hours}h {minutes}m")
print(f"Decimal hours: {estimated_minutes / 60:.2f}")
