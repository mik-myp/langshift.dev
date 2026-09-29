text = "学习"
raw = text.encode("utf-8")
print("Text length:", len(text))
print("Byte length:", len(raw))
print("Bytes:", raw)
print("Decoded:", raw.decode("utf-8"))
