#!/usr/bin/env python3
"""
notion_sync.py (v4 - Image Downloader)
======================================
Notion API를 직접 사용하여 모든 콘텐츠를 마크다운으로 변환하며,
이미지 파일을 로컬로 다운로드하여 해당 문서 폴더에 저장합니다.
"""
import os
import re
import shutil
import json
import urllib.request
import urllib.parse
from notion_client import Client
from dotenv import load_dotenv

load_dotenv()

NOTION_TOKEN = os.getenv("NOTION_TOKEN")
DATABASE_ID = os.getenv("NOTION_DATABASE_ID")

if not NOTION_TOKEN or not DATABASE_ID:
    print("Error: .env 파일에 NOTION_TOKEN과 NOTION_DATABASE_ID를 설정해주세요.")
    exit(1)

notion = Client(auth=NOTION_TOKEN)

# ─────────────────────────────────────────────
# 경로 설정 (스크립트 위치 기준)
# ─────────────────────────────────────────────
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DOCS_DIR = os.path.join(BASE_DIR, "docs")
TOML_PATH = os.path.join(BASE_DIR, "zensical.toml")
NAV_JSON_PATH = os.path.join(DOCS_DIR, "navigation.json")
ENV_PATH = os.path.join(BASE_DIR, ".env")

load_dotenv(ENV_PATH)

# 이미지 다운로드를 위한 헤더
HTTP_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36"
}

# ─────────────────────────────────────────────
# 유틸리티 함수
# ─────────────────────────────────────────────
def make_safe_name(text):
    text = text.strip()
    text = re.sub(r'[\\/:*?"<>|]', '_', text)
    text = re.sub(r'\s+', '_', text)
    text = text.strip('_')
    return text or "untitled"

def download_image(url, dest_path):
    """URL에서 이미지를 다운로드하여 저장합니다."""
    try:
        req = urllib.request.Request(url, headers=HTTP_HEADERS)
        with urllib.request.urlopen(req, timeout=10) as response, open(dest_path, 'wb') as out_file:
            shutil.copyfileobj(response, out_file)
        return True
    except Exception as e:
        print(f"      ⚠️ 이미지 다운로드 실패: {e}")
        return False

# ─────────────────────────────────────────────
# Rich Text → Markdown 변환
# ─────────────────────────────────────────────
def rich_text_to_md(rich_text_list):
    parts = []
    for rt in rich_text_list:
        text = rt.get("plain_text", "").replace('\n', '<br>\n')
        ann = rt.get("annotations", {})
        href = rt.get("href")

        if not ann.get("code"):
            text = text.replace("[", "\\[").replace("]", "\\]")

        if ann.get("code"): text = f"`{text}`"
        if ann.get("bold"): text = f"**{text}**"
        if ann.get("italic"): text = f"*{text}*"
        if ann.get("strikethrough"): text = f"~~{text}~~"
        if ann.get("underline"): text = f"<u>{text}</u>"
        if href: text = f"[{text}]({href})"
        parts.append(text)
    return "".join(parts)

# ─────────────────────────────────────────────
# 단일 블록 → Markdown (이미지 다운로드 포함)
# ─────────────────────────────────────────────
def block_to_md(block, target_dir, page_name, image_state, indent=0):
    btype = block.get("type", "")
    data = block.get(btype, {})
    prefix = "    " * indent
    lines = []

    if btype == "paragraph":
        text = rich_text_to_md(data.get("rich_text", []))
        if text:
            lines.append(f"{prefix}{text}\n")
        else:
            lines.append(f"{prefix}<br>\n")

    elif btype in ("heading_1", "heading_2", "heading_3"):
        level = int(btype[-1])
        text = rich_text_to_md(data.get("rich_text", []))
        lines.append(f"{'#' * level} {text}")

    elif btype == "bulleted_list_item":
        text = rich_text_to_md(data.get("rich_text", []))
        lines.append(f"{prefix}- {text}")

    elif btype == "numbered_list_item":
        text = rich_text_to_md(data.get("rich_text", []))
        lines.append(f"{prefix}1. {text}")

    elif btype == "to_do":
        checked = "x" if data.get("checked") else " "
        text = rich_text_to_md(data.get("rich_text", []))
        lines.append(f"{prefix}- [{checked}] {text}")

    elif btype == "toggle":
        text = rich_text_to_md(data.get("rich_text", []))
        lines.append(f"{prefix}**{text}**")

    elif btype == "quote":
        text = rich_text_to_md(data.get("rich_text", []))
        lines.append(f"> {text}")

    elif btype == "callout":
        text = rich_text_to_md(data.get("rich_text", []))
        icon = data.get("icon", {})
        emoji = icon.get("emoji", "💡") if icon else "💡"
        lines.append(f"> {emoji} {text}")

    elif btype == "code":
        lang = data.get("language", "")
        text = "".join(p.get("plain_text", "") for p in data.get("rich_text", []))
        lines.append(f"```{lang}\n{text}\n```")

    elif btype == "image":
        if data.get("type") == "external":
            url = data.get("external", {}).get("url", "")
        else:
            url = data.get("file", {}).get("url", "")
        
        if url:
            # 이미지 저장 폴더 생성 (images_[페이지명])
            img_subdir = f"images_{make_safe_name(page_name)}"
            img_dir_abs = os.path.join(target_dir, img_subdir)
            os.makedirs(img_dir_abs, exist_ok=True)

            # 확장자 추출 (쿼리 파라미터 제거 후)
            clean_url = url.split('?')[0]
            parsed_url = urllib.parse.urlparse(clean_url)
            ext = os.path.splitext(parsed_url.path)[1]
            if not ext or len(ext) > 5: ext = ".png" # 기본값
            
            image_state['count'] += 1
            img_filename = f"image_{image_state['count']}{ext}"
            img_path_abs = os.path.join(img_dir_abs, img_filename)
            img_rel_path = f"{img_subdir}/{img_filename}"

            # 다운로드 실행
            if download_image(url, img_path_abs):
                caption = rich_text_to_md(data.get("caption", []))
                lines.append(f"\n![{caption or 'image'}]({img_rel_path})\n")
            else:
                lines.append(f"<!-- 이미지 다운로드 실패: {url} -->")

    elif btype == "divider":
        lines.append("---")

    elif btype == "table_row":
        cells = data.get("cells", [])
        row_text = " | ".join(rich_text_to_md(cell) for cell in cells)
        lines.append(f"| {row_text} |")

    elif btype == "equation":
        expr = data.get("expression", "")
        lines.append(f"$${expr}$$")

    elif btype in ("child_page", "child_database"):
        title = data.get("title", "")
        lines.append(f"📄 {title}")

    else:
        rt = data.get("rich_text", [])
        if rt:
            text = rich_text_to_md(rt)
            lines.append(f"{prefix}{text}")

    return "\n".join(lines)

# ─────────────────────────────────────────────
# 페이지 블록 재귀 변환
# ─────────────────────────────────────────────
def blocks_to_md(block_id, target_dir, page_name, image_state, indent=0):
    try:
        response = notion.blocks.children.list(block_id=block_id, page_size=100)
    except Exception as e:
        return f"<!-- 블록 로딩 실패: {e} -->"

    blocks = response.get("results", [])
    while response.get("has_more"):
        response = notion.blocks.children.list(block_id=block_id, page_size=100, start_cursor=response.get("next_cursor"))
        blocks.extend(response.get("results", []))

    md_lines = []
    for block in blocks:
        btype = block.get("type", "")
        
        # 테이블 특수 처리
        if btype == "table":
            try:
                t_resp = notion.blocks.children.list(block_id=block["id"], page_size=100)
                rows = t_resp.get("results", [])
                if rows:
                    header = rows[0]
                    cells = header.get("table_row", {}).get("cells", [])
                    md_lines.append(f"| {' | '.join(rich_text_to_md(c) for c in cells)} |")
                    md_lines.append(f"| {' | '.join(['---'] * len(cells))} |")
                    for row in rows[1:]:
                        cells = row.get("table_row", {}).get("cells", [])
                        md_lines.append(f"| {' | '.join(rich_text_to_md(c) for c in cells)} |")
                md_lines.append("")
            except: pass
            continue

        line = block_to_md(block, target_dir, page_name, image_state, indent)
        if line: md_lines.append(line)

        if block.get("has_children") and btype not in ("table",):
            new_indent = indent + (1 if btype in ("bulleted_list_item", "numbered_list_item", "toggle") else 0)
            child_md = blocks_to_md(block["id"], target_dir, page_name, image_state, new_indent)
            if child_md: md_lines.append(child_md)

    return "\n".join(md_lines).strip()

# ─────────────────────────────────────────────
# 내비게이션 및 설정 업데이트
# ─────────────────────────────────────────────
def build_nav_tree(pages_map, path_map, parent_id=None, depth=0):
    if depth > 20: return []
    nav_items = []
    children = [p for p in pages_map.values() if p['parent_id'] == parent_id]
    children.sort(key=lambda x: x['title'] or "")
    for child in children:
        pid = child['id']
        title = child['title'] or "Untitled"
        rel_path = path_map.get(pid)
        if not rel_path: continue
        toml_path = rel_path.replace("\\", "/") + ".md"
        sub_items = build_nav_tree(pages_map, path_map, pid, depth + 1)
        if sub_items:
            nav_items.append({title: sub_items})
        else:
            nav_items.append({title: toml_path})
    return nav_items

def write_toml(nav_tree):
    def nav_to_str(items, indent=4):
        lines = []
        pad = " " * indent
        for item in items:
            for key, val in item.items():
                safe_key = key.replace('"', '\\"')
                if isinstance(val, list):
                    sub = nav_to_str(val, indent + 4)
                    lines.append(f'{pad}{{ "{safe_key}" = [\n{sub}\n{pad}] }}')
                else:
                    lines.append(f'{pad}{{ "{safe_key}" = "{val}" }}')
        return ",\n".join(lines)

    notion_nav_str = "[\n" + nav_to_str(nav_tree) + "\n]"
    project_section = f"""
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
"""
    with open(TOML_PATH, "w", encoding="utf-8") as f:
        f.write(project_section.strip() + "\n")
    print(f"✅ {TOML_PATH} 업데이트 완료")

def update_navigation_json():
    def build_node(dirpath, rel_path):
        entries = sorted(os.listdir(dirpath))
        md_files = [e for e in entries if e.endswith('.md') and os.path.isfile(os.path.join(dirpath, e))]
        subdirs = [e for e in entries if os.path.isdir(os.path.join(dirpath, e)) and not e.startswith('images_')]
        children = []
        for d in subdirs:
            sub_path = os.path.join(dirpath, d)
            sub_rel = f"{rel_path}/{d}" if rel_path else d
            sub_children = build_node(sub_path, sub_rel)
            if sub_children:
                node_id = re.sub(r'[^a-zA-Z0-9가-힣]', '_', sub_rel)[:60]
                children.append({"id": node_id, "title": d.replace('_', ' '), "type": "folder", "children": sub_children})
        for f in md_files:
            title = f[:-3].replace('_', ' ')
            file_url = f"docs/{rel_path}/{f}" if rel_path else f"docs/{f}"
            node_id = re.sub(r'[^a-zA-Z0-9가-힣]', '_', f"{rel_path}/{f}" if rel_path else f)[:60]
            children.append({"id": node_id, "title": title, "type": "file", "fileUrl": file_url})
        return children

    notion_children = build_node(DOCS_DIR, "")
    if os.path.exists(NAV_JSON_PATH):
        with open(NAV_JSON_PATH, "r", encoding="utf-8") as f: nav = json.load(f)
    else: nav = []
    nav = [n for n in nav if n.get("id") != "root_notion"]
    nav.append({"id": "root_notion", "title": "🌐 Notion Manual", "type": "folder", "children": notion_children})
    with open(NAV_JSON_PATH, "w", encoding="utf-8") as f:
        json.dump(nav, f, ensure_ascii=False, indent=4)
    print(f"✅ {NAV_JSON_PATH} 업데이트 완료")

# ─────────────────────────────────────────────
# 메인 실행
# ─────────────────────────────────────────────
def sync():
    print(f"🔄 Notion 동기화 시작 (이미지 로컬 다운로드 포함)...\n")
    os.makedirs(DOCS_DIR, exist_ok=True)
    
    state_path = os.path.join(DOCS_DIR, ".sync_state.json")
    sync_state = {}
    if os.path.exists(state_path):
        with open(state_path, "r", encoding="utf-8") as f:
            try:
                sync_state = json.load(f)
            except:
                pass

    pages_map = {}
    has_more, cursor = True, None
    while has_more:
        resp = notion.databases.query(database_id=DATABASE_ID, start_cursor=cursor)
        for page in resp.get("results", []):
            props = page.get("properties", {})
            title = ""
            for n in ["이름", "Name", "title"]:
                if props.get(n, {}).get("type") == "title":
                    title = "".join(p.get("plain_text", "") for p in props[n]["title"]).strip()
                    break
            parent_id = None
            for n in ["상위 항목", "Parent", "parent"]:
                if props.get(n, {}).get("type") == "relation":
                    rel = props[n].get("relation", [])
                    if rel: parent_id = rel[0].get("id")
                    break
            pages_map[page["id"]] = {
                "id": page["id"],
                "title": title,
                "parent_id": parent_id,
                "last_edited_time": page.get("last_edited_time")
            }
        has_more, cursor = resp.get("has_more"), resp.get("next_cursor")

    # 경로 계산
    path_cache = {}
    def get_path(pid, depth=0):
        if depth > 20 or pid in path_cache: return path_cache.get(pid, "")
        data = pages_map.get(pid)
        if not data: return ""
        title = make_safe_name(data['title'])
        parent_id = data['parent_id']
        path = os.path.join(get_path(parent_id, depth+1), title) if parent_id and parent_id in pages_map else title
        path_cache[pid] = path
        return path
    for pid in pages_map: get_path(pid)

    import hashlib
    
    current_rel_paths = set(rel + ".md" for rel in path_cache.values())
    
    # 1. 삭제된 파일 정리
    paths_to_delete = [p for p in sync_state.keys() if p not in current_rel_paths]
    for p in paths_to_delete:
        abs_p = os.path.join(DOCS_DIR, p)
        if os.path.exists(abs_p):
            os.remove(abs_p)
            print(f"  🗑️ 삭제됨: {p}")
        title = os.path.basename(p).replace(".md", "")
        img_dir = os.path.join(os.path.dirname(abs_p), f"images_{make_safe_name(title)}")
        if os.path.exists(img_dir):
            shutil.rmtree(img_dir, ignore_errors=True)
        del sync_state[p]
    
    # 2. 업데이트 및 신규 생성
    total = len(pages_map)
    for idx, (pid, rel) in enumerate(path_cache.items(), 1):
        title = pages_map[pid]['title'] or "Untitled"
        last_edited_time = pages_map[pid]['last_edited_time']
        
        rel_path = rel + ".md"
        abs_path = os.path.join(DOCS_DIR, rel_path)
        
        # 증분 업데이트 확인
        if rel_path in sync_state:
            if sync_state[rel_path].get("last_edited_time") == last_edited_time:
                if os.path.exists(abs_path):
                    continue # 변경 없음, 건너뜀

        target_dir = os.path.dirname(abs_path)
        os.makedirs(target_dir, exist_ok=True)

        print(f"  [{idx}/{total}] 📝 업데이트: {title}")
        image_state = {'count': 0}
        
        # 만약 기존 이미지 폴더가 있다면 비우기 (새로 다운로드하기 위해)
        img_dir_abs = os.path.join(target_dir, f"images_{make_safe_name(title)}")
        if os.path.exists(img_dir_abs):
            shutil.rmtree(img_dir_abs, ignore_errors=True)
            
        md_content = blocks_to_md(pid, target_dir, title, image_state)
        
        file_content = f"# {title}\n\n{md_content}"
        
        with open(abs_path, "w", encoding="utf-8") as f:
            f.write(file_content)
            
        sync_state[rel_path] = {
            "id": pid,
            "last_edited_time": last_edited_time,
            "hash": hashlib.md5(file_content.encode('utf-8')).hexdigest()
        }

    # 기본 index.md 생성
    with open(os.path.join(DOCS_DIR, "index.md"), "w", encoding="utf-8") as f:
        f.write("# midas NFX GUI Manual\n\n좌측 메뉴에서 문서를 선택해주세요.")

    # 상태 저장
    state_path = os.path.join(DOCS_DIR, ".sync_state.json")
    with open(state_path, "w", encoding="utf-8") as f:
        json.dump(sync_state, f, ensure_ascii=False, indent=4)

    nav_tree = build_nav_tree(pages_map, path_cache)
    write_toml(nav_tree)
    update_navigation_json()
    print("\n🎉 전체 동기화 및 이미지 다운로드 완료!")

if __name__ == "__main__":
    sync()
