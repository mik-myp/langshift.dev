import settings
from settings import BUDGET, current_budget, tags

print("Initial:", BUDGET, settings.BUDGET)
settings.BUDGET = 40
print("Rebound:", BUDGET, settings.BUDGET, current_budget())
settings.tags.append("modules")
print("Shared:", tags, settings.tags)
tags = ["local"]
print("Local tags:", tags, settings.tags)
