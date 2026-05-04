import inspect
from notion_client import Client
notion = Client(auth="dummy")
print(inspect.signature(notion.blocks.children.append))
