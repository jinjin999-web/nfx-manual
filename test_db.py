import os
from notion_client import Client
from dotenv import load_dotenv

load_dotenv()
notion = Client(auth=os.getenv("NOTION_TOKEN"))
db_id = os.getenv("NOTION_DATABASE_ID")

has_more, cursor = True, None
pages = []
while has_more:
    resp = notion.databases.query(database_id=db_id, start_cursor=cursor)
    for p in resp.get("results", []):
        props = p.get("properties", {})
        title = ""
        for n in ["이름", "Name", "title"]:
            if props.get(n, {}).get("type") == "title":
                title = "".join(t.get("plain_text", "") for t in props[n]["title"]).strip()
        
        parent_id = None
        for n in ["상위 항목", "Parent", "parent"]:
            if props.get(n, {}).get("type") == "relation":
                rel = props[n].get("relation", [])
                if rel: parent_id = rel[0].get("id")
        
        pages.append({"id": p["id"], "title": title, "parent_id": parent_id})
    has_more, cursor = resp.get("has_more"), resp.get("next_cursor")

print(f"Total pages: {len(pages)}")
for p in pages:
    print(f"{p['title']} (parent: {p['parent_id']})")
