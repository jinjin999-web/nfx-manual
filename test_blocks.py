import os, json
from notion_client import Client
from dotenv import load_dotenv

load_dotenv()
notion = Client(auth=os.getenv("NOTION_TOKEN"))

# GUI Manual page id is '12fb5e52-ebbb-81d3-9ba8-cbcd3d9e830f' 
# Let's get the id from db
db_id = os.getenv("NOTION_DATABASE_ID")
resp = notion.databases.query(database_id=db_id)
page_id = None
for p in resp["results"]:
    title = p["properties"]["이름"]["title"][0]["plain_text"]
    if title == "midas NFX GUI Manual":
        page_id = p["id"]

blocks = notion.blocks.children.list(block_id=page_id)
print(json.dumps(blocks, indent=2))
