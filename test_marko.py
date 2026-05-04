import marko
from marko.ext.gfm import gfm
from marko.block import Heading, Paragraph, List, ListItem, Quote, FencedCode, BlankLine, ThematicBreak
from marko.inline import RawText, StrongEmphasis, Emphasis, CodeSpan, Image
from marko.ext.gfm.elements import Table, TableRow, TableCell

def span_to_rich_text(element):
    rich_text = []
    if not hasattr(element, 'children'):
        return rich_text
        
    for child in getattr(element, 'children', []):
        if type(child) is RawText:
            rich_text.append({"type": "text", "text": {"content": child.children}})
        elif type(child) is StrongEmphasis:
            rt = span_to_rich_text(child)
            for r in rt: r.setdefault("annotations", {})["bold"] = True
            rich_text.extend(rt)
        elif type(child) is Emphasis:
            rt = span_to_rich_text(child)
            for r in rt: r.setdefault("annotations", {})["italic"] = True
            rich_text.extend(rt)
        elif type(child) is CodeSpan:
            rt = [{"type": "text", "text": {"content": child.children}}]
            for r in rt: r.setdefault("annotations", {})["code"] = True
            rich_text.extend(rt)
        elif type(child) is Image:
            # We cannot easily push images. Output as a placeholder text for differential sync to match
            rich_text.append({"type": "text", "text": {"content": f"![image]({child.dest})"}})
        else:
            rich_text.extend(span_to_rich_text(child))
    return rich_text

def ast_to_blocks(ast_node):
    blocks = []
    for child in ast_node.children:
        if type(child) is BlankLine: continue
        elif type(child) is ThematicBreak:
            blocks.append({"object": "block", "type": "divider", "divider": {}})
        elif type(child) is Heading:
            lvl = min(child.level, 3)
            h_type = f"heading_{lvl}"
            blocks.append({
                "object": "block", "type": h_type,
                h_type: {"rich_text": span_to_rich_text(child)}
            })
        elif type(child) is Paragraph:
            blocks.append({
                "object": "block", "type": "paragraph",
                "paragraph": {"rich_text": span_to_rich_text(child)}
            })
        elif type(child) is List:
            is_num = child.ordered
            b_type = "numbered_list_item" if is_num else "bulleted_list_item"
            for item in child.children:
                if type(item) is ListItem:
                    rich_text = []
                    for p in item.children:
                        rich_text.extend(span_to_rich_text(p))
                    blocks.append({
                        "object": "block", "type": b_type,
                        b_type: {"rich_text": rich_text}
                    })
        elif type(child) is Quote:
            rich_text = []
            for p in child.children:
                rich_text.extend(span_to_rich_text(p))
            blocks.append({
                "object": "block", "type": "quote",
                "quote": {"rich_text": rich_text}
            })
        elif type(child) is FencedCode:
            text = child.children[0].children if child.children else ""
            lang = child.lang or "plain text"
            blocks.append({
                "object": "block", "type": "code",
                "code": {"rich_text": [{"type": "text", "text": {"content": text}}], "language": lang}
            })
        elif type(child) is Table:
            table_width = len(child.children[0].children) if child.children else 1
            has_header = True # GFM tables always have header
            table_block = {
                "object": "block", "type": "table",
                "table": {
                    "table_width": table_width,
                    "has_column_header": has_header,
                    "has_row_header": False,
                    "children": [] # We will append rows
                }
            }
            for row in child.children:
                cells = []
                for cell in row.children:
                    cells.append(span_to_rich_text(cell))
                table_block["table"]["children"].append({
                    "object": "block", "type": "table_row",
                    "table_row": {"cells": cells}
                })
            blocks.append(table_block)
    return blocks

md = """# Hello
This is a **bold** and *italic* text with `code`.
![test_img](local.png)

| 1 | 2 | 3 |
|---|---|---|
| A | B | C |
"""
doc = gfm.parse(md)
import json
print(json.dumps(ast_to_blocks(doc), indent=2))
