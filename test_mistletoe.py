from mistletoe import Document
from mistletoe.block_token import Heading, Paragraph, List, ListItem, Quote, CodeFence, BlockCode
from mistletoe.span_token import RawText, Strong, Emphasis, InlineCode

def ast_to_blocks(ast_node):
    blocks = []
    for child in ast_node.children:
        if isinstance(child, Heading):
            lvl = min(child.level, 3)
            h_type = f"heading_{lvl}"
            blocks.append({
                "object": "block", "type": h_type,
                h_type: {"rich_text": span_to_rich_text(child.children)}
            })
        elif isinstance(child, Paragraph):
            blocks.append({
                "object": "block", "type": "paragraph",
                "paragraph": {"rich_text": span_to_rich_text(child.children)}
            })
        elif isinstance(child, List):
            is_num = child.start is not None
            b_type = "numbered_list_item" if is_num else "bulleted_list_item"
            for item in child.children:
                if isinstance(item, ListItem):
                    # item.children are usually paragraphs
                    rich_text = []
                    for p in item.children:
                        if hasattr(p, 'children'):
                            rich_text.extend(span_to_rich_text(p.children))
                    blocks.append({
                        "object": "block", "type": b_type,
                        b_type: {"rich_text": rich_text}
                    })
        elif isinstance(child, Quote):
            rich_text = []
            for p in child.children:
                if hasattr(p, 'children'):
                    rich_text.extend(span_to_rich_text(p.children))
            blocks.append({
                "object": "block", "type": "quote",
                "quote": {"rich_text": rich_text}
            })
        elif isinstance(child, (CodeFence, BlockCode)):
            # children usually has RawText
            text = child.children[0].content if child.children else ""
            lang = getattr(child, 'language', 'plain text') or 'plain text'
            blocks.append({
                "object": "block", "type": "code",
                "code": {"rich_text": [{"type": "text", "text": {"content": text}}], "language": lang}
            })
    return blocks

def span_to_rich_text(spans):
    rich_text = []
    for span in spans:
        if isinstance(span, RawText):
            rich_text.append({"type": "text", "text": {"content": span.content}})
        elif isinstance(span, Strong):
            rt = span_to_rich_text(span.children)
            for r in rt: r.setdefault("annotations", {})["bold"] = True
            rich_text.extend(rt)
        elif isinstance(span, Emphasis):
            rt = span_to_rich_text(span.children)
            for r in rt: r.setdefault("annotations", {})["italic"] = True
            rich_text.extend(rt)
        elif isinstance(span, InlineCode):
            rt = span_to_rich_text(span.children)
            for r in rt: r.setdefault("annotations", {})["code"] = True
            rich_text.extend(rt)
        else:
            if hasattr(span, 'content'):
                rich_text.append({"type": "text", "text": {"content": span.content}})
    return rich_text

md = """# Hello
This is a **bold** and *italic* text with `code`.
- Item 1
- Item 2
```python
print("Hello")
```
> A quote
"""
doc = Document(md)
import json
print(json.dumps(ast_to_blocks(doc), indent=2))
