from models import TaskCreate, TaskPatch

original = TaskCreate(title="Keep spelling", minutes=25, done=True, note="keep me")
for raw in [{}, {"done": False}, {"note": "new"}, {"note": None}, {"minutes": 0}]:
    patch = TaskPatch.model_validate(raw)
    changes = patch.model_dump(exclude_unset=True)
    merged = original.model_dump()
    merged.update(changes)
    print("sent:", raw)
    print("changes:", changes)
    print("merged:", TaskCreate.model_validate(merged).model_dump())

print("WRONG dump of empty patch:", TaskPatch().model_dump())
print("WRONG exclude_none:", TaskPatch(note=None).model_dump(exclude_unset=True, exclude_none=True))
print("WRONG exclude_defaults:", TaskPatch(done=False).model_dump(exclude_unset=True, exclude_defaults=True))
