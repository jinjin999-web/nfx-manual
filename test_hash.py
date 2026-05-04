import hashlib, json
with open("docs/.sync_state.json", "r") as f: state = json.load(f)
key = "형상/CAD_File/내보내기.md"
with open(f"docs/{key}", "r") as f: content = f.read()
h = hashlib.md5(content.encode('utf-8')).hexdigest()
print(f"State hash: {state[key]['hash']}")
print(f"File hash:  {h}")
print(f"Match: {state[key]['hash'] == h}")
