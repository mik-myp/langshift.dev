import json

value = {"pair": (20, 35), "labels": {1: "one"}}
restored = json.loads(json.dumps(value))
print("Restored:", restored)
print("Equal:", restored == value)
try:
    json.dumps({"tags": {"python"}})
except TypeError:
    print("Set is not JSON-serializable")
try:
    json.dumps(float("nan"), allow_nan=False)
except ValueError:
    print("Non-finite output rejected")
print("Default decoder accepts NaN:", type(json.loads("NaN")) is float)
print("Repeated key:", json.loads('{"minutes": 10, "minutes": 20}'))
try:
    json.loads(str({"done": False}))
except json.JSONDecodeError:
    print("Python repr is not JSON")
