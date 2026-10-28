import json
import re
import urllib.parse
from typing import Dict, Any, Optional

import ddgs
import httpx


def extract_youtube_video_id(url: str) -> Optional[str]:
    """Extract 11-character YouTube video ID from various YouTube URL formats."""
    if not url:
        return None
    match = re.search(r'(?:v=|\/embed\/|youtu\.be\/|\/v\/|\/shorts\/)([a-zA-Z0-9_-]{11})', url)
    return match.group(1) if match else None


def is_music_query(query: str) -> bool:
    """Check if query is asking to play music, a song, or audio/video."""
    q = query.lower().strip()
    keywords = [
        "play ", "song", "music", "listen", "youtube", "video",
        "track", "audio", "lofi", "tune", "band", "singer", "album"
    ]
    return any(k in q for k in keywords)


def search_youtube(query: str) -> Dict[str, Any]:
    """
    Search YouTube for a song or video title and return embed metadata.
    """
    clean = query.strip()
    # Strip common prefixes like 'play ', 'listen to '
    clean_search = re.sub(r'^(?:play|listen to|put on|stream)\s+', '', clean, flags=re.IGNORECASE).strip()
    if not clean_search:
        clean_search = clean

    # 1. Direct YouTube search query scraping (fast & reliable)
    try:
        encoded = urllib.parse.quote_plus(clean_search)
        yt_url = f"https://www.youtube.com/results?search_query={encoded}"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
        }
        with httpx.Client(headers=headers, timeout=5.0) as client:
            resp = client.get(yt_url)
            if resp.status_code == 200:
                # Extract first valid video ID and title
                matches = re.findall(
                    r'\"videoId\":\"([a-zA-Z0-9_-]{11})\".*?\"title\":\{\"runs\":\[\{\"text\":\"(.*?)\"\}\]',
                    resp.text
                )
                if matches:
                    vid, title = matches[0]
                    return {
                        "title": title,
                        "url": f"https://www.youtube.com/watch?v={vid}",
                        "embed_url": f"https://www.youtube.com/embed/{vid}?autoplay=1&enablejsapi=1",
                        "type": "music",
                        "query": clean,
                        "domain": "youtube.com",
                        "summary": f"YouTube video for '{title}'"
                    }
    except Exception:
        pass

    # 2. Fallback to DDGS text search
    try:
        search = ddgs.DDGS()
        results = list(search.text(f"{clean_search} youtube", max_results=5))
        for r in results:
            href = r.get("href", "")
            vid = extract_youtube_video_id(href)
            if vid:
                title = r.get("title", clean_search)
                # Clean up title suffix like " - YouTube"
                title = re.sub(r'\s*-\s*YouTube.*$', '', title, flags=re.IGNORECASE)
                return {
                    "title": title,
                    "url": f"https://www.youtube.com/watch?v={vid}",
                    "embed_url": f"https://www.youtube.com/embed/{vid}?autoplay=1&enablejsapi=1",
                    "type": "music",
                    "query": clean,
                    "domain": "youtube.com",
                    "summary": r.get("body", f"YouTube video for '{title}'")
                }
    except Exception:
        pass

    # 3. Final fallback embed
    encoded = urllib.parse.quote_plus(clean_search)
    return {
        "title": f"YouTube: {clean_search}",
        "url": f"https://www.youtube.com/results?search_query={encoded}",
        "embed_url": f"https://www.youtube.com/embed?listType=search&list={encoded}",
        "type": "music",
        "query": clean,
        "domain": "youtube.com",
        "summary": f"Search results for '{clean_search}' on YouTube"
    }


def search_general_web(query: str) -> Dict[str, Any]:
    """
    Search the web for general info or specific websites and return embed metadata.
    """
    clean = query.strip()
    
    # Strip common command prefixes
    clean_search = re.sub(r'^(?:search\s+for|search|find|lookup|browse)\s+', '', clean, flags=re.IGNORECASE).strip()
    if not clean_search:
        clean_search = clean

    # Direct URL check
    if re.match(r'^https?://', clean_search, re.IGNORECASE) or ('.' in clean_search and not ' ' in clean_search and len(clean_search.split('.')) >= 2):
        target_url = clean_search if clean_search.startswith("http") else f"https://{clean_search}"
        parsed = urllib.parse.urlparse(target_url)
        domain = parsed.netloc or "web"
        return {
            "title": f"Web Page: {domain}",
            "url": target_url,
            "embed_url": f"/api/proxy?url={urllib.parse.quote_plus(target_url)}",
            "type": "web",
            "query": clean,
            "domain": domain,
            "summary": f"Direct link to {target_url}"
        }

    # 1. Search with DDGS
    try:
        search = ddgs.DDGS()
        results = list(search.text(clean_search, max_results=5))
        if results:
            top = results[0]
            url = top.get("href", "")
            title = top.get("title", clean_search)
            body = top.get("body", "")
            domain = urllib.parse.urlparse(url).netloc if url else "web"
            return {
                "title": title,
                "url": url,
                "embed_url": f"/api/proxy?url={urllib.parse.quote_plus(url)}",
                "type": "web",
                "query": clean,
                "domain": domain,
                "summary": body
            }
    except Exception:
        pass

    # 2. Wikipedia fallback for informational queries
    try:
        wiki_url = f"https://en.wikipedia.org/w/api.php?action=opensearch&search={urllib.parse.quote_plus(clean_search)}&limit=1&namespace=0&format=json"
        headers = {"User-Agent": "LocalChatAgent/1.0 (local-desktop-agent; contact: agent@local.app)"}
        with httpx.Client(headers=headers, timeout=4.0) as client:
            resp = client.get(wiki_url)
            if resp.status_code == 200:
                data = resp.json()
                if len(data) >= 4 and data[1] and data[3]:
                    w_title = data[1][0]
                    w_url = data[3][0]
                    return {
                        "title": f"{w_title} - Wikipedia",
                        "url": w_url,
                        "embed_url": f"/api/proxy?url={urllib.parse.quote_plus(w_url)}",
                        "type": "web",
                        "query": clean,
                        "domain": "en.wikipedia.org",
                        "summary": f"Wikipedia article on {w_title}"
                    }
    except Exception:
        pass

    # 3. Fallback to DuckDuckGo search page
    encoded = urllib.parse.quote_plus(clean_search)
    ddg_url = f"https://duckduckgo.com/?q={encoded}"
    return {
        "title": f"Search: {clean_search}",
        "url": ddg_url,
        "embed_url": f"/api/proxy?url={urllib.parse.quote_plus(ddg_url)}",
        "type": "web",
        "query": clean,
        "domain": "duckduckgo.com",
        "summary": f"Search results for '{clean_search}'"
    }


def get_web_window_data(query: str) -> Dict[str, Any]:
    """Retrieve structured web window data for a search or music request."""
    if is_music_query(query):
        return search_youtube(query)
    return search_general_web(query)


def web_search(query: str) -> str:
    """
    Search the web or YouTube for music/content and return the web window embed for the conversation.
    Works for general search queries, websites, and music/video requests.

    Args:
        query: Search term, URL, or song/video title.

    Returns:
        Structured response with title, URL, summary, and window widget for the conversation.
    """
    clean_query = query.strip()
    if not clean_query:
        return "Error: Empty search query provided."

    window_data = get_web_window_data(clean_query)
    
    # We embed the :::web-window{...}::: payload so both server and chat renderers can display the window bubble.
    window_json = json.dumps(window_data, ensure_ascii=False)
    
    result_text = (
        f"Found result for '{clean_query}':\n"
        f"- Title: {window_data['title']}\n"
        f"- URL: {window_data['url']}\n"
        f"- Type: {window_data['type']}\n"
        f"- Summary: {window_data.get('summary', '')}\n\n"
        f":::web-window{window_json}:::"
    )
    return result_text
