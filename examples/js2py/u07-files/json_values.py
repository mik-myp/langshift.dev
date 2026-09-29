import json

value = {"title": "学习", "minutes": 20, "done": False, "note": None}
text = json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False)
print("Is text:", type(text) is str)
print(text)
restored = json.loads(text)
print("Equal value:", restored == value)
print("Same object:", restored is value)
print("Escaped:", json.dumps("学习"))
