import os
from notion_client import Client
from dotenv import load_dotenv

load_dotenv()
notion = Client(auth=os.getenv("NOTION_TOKEN"))
db_id = "351c0436-d1b1-81c4-ba29-f76bb1b2a25c"

resp = notion.databases.query(database_id=db_id)
for p in resp['results'][:5]:
    props = p.get("properties", {})
    parent_id = None
    for n in ["상위 항목", "Parent", "parent", "상위항목"]:
        if n in props and props[n].get("type") == "relation":
            rel = props[n].get("relation", [])
            if rel: parent_id = rel[0].get("id")
    print(parent_id)
