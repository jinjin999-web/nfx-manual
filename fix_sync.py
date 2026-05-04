import re
with open('notion_sync.py', 'r', encoding='utf-8') as f:
    content = f.read()

new_write_toml = """def write_toml(nav_tree):
    def nav_to_str(items, indent=4):
        lines = []
        pad = " " * indent
        for item in items:
            for key, val in item.items():
                safe_key = key.replace('"', '\\\\"')
                if isinstance(val, list):
                    sub = nav_to_str(val, indent + 4)
                    lines.append(f'{pad}{{ "{safe_key}" = [\\n{sub}\\n{pad}] }}')
                else:
                    lines.append(f'{pad}{{ "{safe_key}" = "{val}" }}')
        return ",\\n".join(lines)

    notion_nav_str = "[\\n" + nav_to_str(nav_tree) + "\\n]"
    project_section = f'''
[project]
site_name = "midas NFX GUI Manual"
site_description = "midas NFX GUI Manual"
docs_dir = "docs"
site_dir = "site"
use_directory_urls = true

nav = {notion_nav_str}

[project.theme]
language = "ko"
variant = "modern"
'''
    with open("zensical.toml", "w", encoding="utf-8") as f:
        f.write(project_section.strip() + "\\n")"""

content = re.sub(r'def write_toml\(nav_tree\):.*?(?=\n\n\n|\Z)', new_write_toml, content, flags=re.DOTALL)

with open('notion_sync.py', 'w', encoding='utf-8') as f:
    f.write(content)
