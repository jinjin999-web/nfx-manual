import re

def parse_markdown_to_blocks(md_content):
    blocks = []
    lines = md_content.split('\n')
    
    current_block = None
    
    def add_block(b):
        if b: blocks.append(b)
        
    for line in lines:
        line_s = line.strip()
        if not line_s:
            continue
            
        if line.startswith('# '):
            blocks.append({"object": "block", "type": "heading_1", "heading_1": {"rich_text": [{"type": "text", "text": {"content": line[2:].strip()}}]}})
        elif line.startswith('## '):
            blocks.append({"object": "block", "type": "heading_2", "heading_2": {"rich_text": [{"type": "text", "text": {"content": line[3:].strip()}}]}})
        elif line.startswith('### '):
            blocks.append({"object": "block", "type": "heading_3", "heading_3": {"rich_text": [{"type": "text", "text": {"content": line[4:].strip()}}]}})
        elif line.startswith('- ') or line.startswith('* '):
            blocks.append({"object": "block", "type": "bulleted_list_item", "bulleted_list_item": {"rich_text": [{"type": "text", "text": {"content": line[2:].strip()}}]}})
        elif re.match(r'^\d+\.\s', line):
            content = re.sub(r'^\d+\.\s', '', line).strip()
            blocks.append({"object": "block", "type": "numbered_list_item", "numbered_list_item": {"rich_text": [{"type": "text", "text": {"content": content}}]}})
        elif line.startswith('> '):
            blocks.append({"object": "block", "type": "quote", "quote": {"rich_text": [{"type": "text", "text": {"content": line[2:].strip()}}]}})
        elif line.startswith('```'):
            # simple code block handling can be complex due to multiline
            # for now let's just make a paragraph if it's too complex
            pass
        else:
            # Paragraph
            blocks.append({"object": "block", "type": "paragraph", "paragraph": {"rich_text": [{"type": "text", "text": {"content": line}}]}})
            
    return blocks
