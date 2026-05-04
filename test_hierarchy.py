import os, json
from notion_client import Client
from dotenv import load_dotenv

load_dotenv()
notion = Client(auth=os.getenv("NOTION_TOKEN"))
db_id = "351c0436-d1b1-81c4-ba29-f76bb1b2a25c"

resp = notion.databases.query(database_id=db_id)
# find a page that is a parent of another
pages = resp['results']
parent_ids = {p["properties"]["상위 항목"]["relation"][0]["id"] for p in pages if p["properties"].get("상위 항목") and p["properties"]["상위 항목"].get("relation")}

print(f"Number of parents: {len(parent_ids)}")
if parent_ids:
    pid = list(parent_ids)[0]
    blocks = notion.blocks.children.list(block_id=pid)
    print(f"Blocks for parent {pid}:")
    for b in blocks["results"]:
        print(f"- {b['type']}")
