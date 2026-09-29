titles = ["Read names", "Practice values"]
print(len(titles))
print(titles[0])
print(titles[-1])
titles[1] = "Practice containers"
result = titles.append("Review")
print(titles)
print(result)
finished = titles.pop(0)
print(finished)
print(titles)
print(titles[0:1])
print("Review" in titles)
