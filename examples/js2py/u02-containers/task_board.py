template = {"title": "Untitled", "minutes": 25, "tags": ["python"], "owner": None}

first = template.copy()
first["tags"] = template["tags"].copy()
first["title"] = "Read names"
first["tags"].append("basics")

second = template.copy()
second["tags"] = template["tags"].copy()
second["title"] = "Practice containers"
second["owner"] = "Mina"

board = [first, second]
print(f"Tasks: {len(board)}")
print(board[0]["title"])
print(board[0]["tags"])
print(board[1]["tags"])
print(template["tags"])
print(board[0]["owner"] is None)
print(board[1]["owner"])
board[0]["minutes"] = 40
print(first["minutes"])
print(template["minutes"])
