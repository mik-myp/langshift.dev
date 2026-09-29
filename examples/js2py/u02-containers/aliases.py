original = ["todo"]
alias = original
print(original is alias)
alias.append("review")
print(original)
alias = ["done"]
print(original)
print(alias)
print(original is alias)
