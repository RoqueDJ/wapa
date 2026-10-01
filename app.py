from flask import Flask
import requests
from bs4 import BeautifulSoup
import re
import json

app = Flask(__name__)

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Linux; Android 13) "
        "AppleWebKit/537.36 "
        "Chrome/140 Safari/537.36"
    ),
    "Referer": "https://wapa.tv/envivo",
}


def scrape_wapa_page():
    """
    Step 1: Scrape https://wapa.tv/envivo
    Extract ALL Field59 player/channel/schedule references and embedded configurations
    """
    print("\n=== STEP 1: Scraping wapa.tv/envivo ===")
    candidates = {
        "field59_players": [],
        "field59_channels": [],
        "embedded_urls": [],
        "script_configs": []
    }
    
    try:
        response = requests.get(
            "https://wapa.tv/envivo",
            headers=HEADERS,
            timeout=15
        )
        response.raise_for_status()
        
        # Find all Field59 player references
        player_matches = re.findall(
            r'player\.field59\.com/v4/channel/([^/\s"\'<>]+)/([^/\s"\'<>]+)',
            response.text
        )
        if player_matches:
            for channel, channel_id in player_matches:
                ref = f"player.field59.com/v4/channel/{channel}/{channel_id}"
                print(f"  Found Field59 player: {ref}")
                candidates["field59_players"].append(ref)
        
        # Find any live.field59.com URLs
        field59_live = re.findall(
            r'https://live\.field59\.com/[^\s"\'<>]+',
            response.text
        )
        for url in field59_live:
            print(f"  Found live.field59.com URL: {url}")
            candidates["embedded_urls"].append(url)
        
        # Extract script contents for deeper inspection
        soup = BeautifulSoup(response.text, 'html.parser')
        scripts = soup.find_all('script')
        
        for idx, script in enumerate(scripts):
            if script.string:
                script_text = script.string
                
                # Look for any URLs in scripts
                urls_in_script = re.findall(r'https://[^\s"\'<>]+', script_text)
                
                if urls_in_script:
                    for url in urls_in_script:
                        if 'field59' in url or 'wapa' in url or 'm3u8' in url or 'live' in url:
                            print(f"  Found URL in script[{idx}]: {url}")
                            candidates["script_configs"].append(url)
        
        print(f"  Total candidates found: {len(candidates['field59_players']) + len(candidates['embedded_urls']) + len(candidates['script_configs'])}")
        return candidates
        
    except Exception as e:
        print(f"  ERROR scraping wapa.tv/envivo: {e}")
        return candidates


def fetch_field59_config(player_ref):
    """
    Step 2: Fetch Field59 channel configuration
    Recursively inspect the JSON for all potential stream sources
    """
    print(f"\n=== STEP 2: Fetching Field59 config: {player_ref} ===")
    
    try:
        url = f"https://{player_ref}"
        response = requests.get(
            url,
            headers=HEADERS,
            timeout=15,
            allow_redirects=True
        )
        
        print(f"  HTTP Status: {response.status_code}")
        
        found_urls = set()
        
        # Try to parse as JSON
        try:
            data = response.json()
            print(f"  Response is JSON (keys: {list(data.keys())[:10]}...)")
            
            # Recursively search for URLs in the JSON
            def extract_urls_from_json(obj, path=""):
                urls = set()
                if isinstance(obj, dict):
                    for key, value in obj.items():
                        if key in ['url', 'playlist', 'stream', 'live', 'media', 'source', 'video', 'channel', 'href', 'src', 'uri']:
                            if isinstance(value, str) and ('http' in value or 'm3u8' in value or 'field59' in value):
                                print(f"    Found in JSON[{key}]: {value}")
                                urls.add(value)
                        urls.update(extract_urls_from_json(value, f"{path}.{key}"))
                elif isinstance(obj, list):
                    for idx, item in enumerate(obj):
                        urls.update(extract_urls_from_json(item, f"{path}[{idx}]"))
                return urls
            
            found_urls.update(extract_urls_from_json(data))
        
        except json.JSONDecodeError:
            print(f"  Response is not JSON, searching text for URLs...")
            # Fall back to regex search
            urls_found = re.findall(r'https://[^\s"\'<>]+', response.text)
            for url in urls_found:
                if 'field59' in url or 'wapa' in url or 'm3u8' in url or 'live' in url:
                    print(f"    Found URL: {url}")
                    found_urls.add(url)
        
        return found_urls
        
    except Exception as e:
        print(f"  ERROR fetching Field59 config: {e}")
        return set()


def check_url_status(url):
    """
    Step 3: Check HTTP status of a URL
    Note which ones are accessible vs. 403 (event-gated)
    """
    print(f"\n  Checking: {url}")
    
    try:
        response = requests.head(
            url,
            headers=HEADERS,
            timeout=10,
            allow_redirects=True
        )
        
        status = response.status_code
        reason = ""
        
        if status == 200:
            reason = "✓ ACCESSIBLE"
        elif status == 403:
            reason = "✗ FORBIDDEN (event-gated?)"
        elif status == 404:
            reason = "✗ NOT FOUND"
        elif status in [301, 302, 307, 308]:
            reason = f"→ REDIRECT ({status})"
        else:
            reason = f"? {status}"
        
        print(f"    Status: {status} {reason}")
        
        # Check if it's a token-based URL
        is_token_url = '/t/' in url and '/wapa/' in url
        if is_token_url:
            print(f"    ⚠ Token-based URL detected (event-specific)")
        
        return {
            "url": url,
            "status": status,
            "accessible": status == 200,
            "is_token_url": is_token_url
        }
        
    except Exception as e:
        print(f"    ERROR: {e}")
        return {
            "url": url,
            "status": None,
            "accessible": False,
            "error": str(e)
        }


def run_investigation():
    """
    Full investigation pipeline
    """
    print("\n" + "="*70)
    print("WAPA/Field59 STREAM INVESTIGATION")
    print("="*70)
    
    results = {
        "wapa_page_findings": {},
        "field59_configs": {},
        "url_status_checks": [],
        "permanent_sources": [],
        "event_gated_sources": [],
        "inaccessible_sources": []
    }
    
    # Step 1: Scrape WAPA page
    candidates = scrape_wapa_page()
    results["wapa_page_findings"] = candidates
    
    # Step 2: Fetch Field59 configs
    all_candidate_urls = set()
    
    for player_ref in candidates["field59_players"]:
        urls = fetch_field59_config(player_ref)
        results["field59_configs"][player_ref] = list(urls)
        all_candidate_urls.update(urls)
    
    # Add directly found URLs
    all_candidate_urls.update(candidates["embedded_urls"])
    all_candidate_urls.update(candidates["script_configs"])
    
    print(f"\n=== STEP 3: Testing all candidate URLs ({len(all_candidate_urls)} total) ===")
    
    # Step 3: Check status of all candidate URLs
    for url in sorted(all_candidate_urls):
        status_info = check_url_status(url)
        results["url_status_checks"].append(status_info)
        
        if status_info.get("accessible"):
            if status_info.get("is_token_url"):
                results["event_gated_sources"].append(url)
            else:
                results["permanent_sources"].append(url)
        elif status_info.get("status") == 403:
            results["event_gated_sources"].append(url)
        else:
            results["inaccessible_sources"].append(url)
    
    # Summary
    print("\n" + "="*70)
    print("INVESTIGATION SUMMARY")
    print("="*70)
    print(f"\nTotal candidate URLs found: {len(all_candidate_urls)}")
    print(f"  - Accessible (200): {len(results['permanent_sources'])}")
    print(f"  - Event-gated/403: {len(results['event_gated_sources'])}")
    print(f"  - Inaccessible: {len(results['inaccessible_sources'])}")
    
    if results["permanent_sources"]:
        print("\n✓ PERMANENT STREAM SOURCES FOUND:")
        for url in results["permanent_sources"]:
            print(f"  - {url}")
    else:
        print("\n✗ NO PERMANENT STREAM SOURCES FOUND")
        print("  All accessible URLs are event-specific or token-based.")
    
    print("\nEvent-gated/403 URLs (require active event):")
    for url in results["event_gated_sources"][:5]:
        print(f"  - {url}")
    if len(results["event_gated_sources"]) > 5:
        print(f"  ... and {len(results['event_gated_sources']) - 5} more")
    
    return results


@app.route("/")
def home():
    return "WAPA 4.1 test server is running."


@app.route("/WAPA-TV-4-1.m3u8")
def wapa():
    try:
        response = requests.get(
            "https://live.field59.com/wapa/wapa1/playlist.m3u8",
            headers=HEADERS,
            timeout=15,
            allow_redirects=False
        )

        return (
            f"URL:\n"
            f"https://live.field59.com/wapa/wapa1/playlist.m3u8\n\n"
            f"HTTP status: {response.status_code}\n\n"
            f"Headers:\n"
            f"{dict(response.headers)}\n\n"
            f"Body:\n"
            f"{response.text[:2000]}"
        ), response.status_code

    except Exception as e:
        return (
            f"ERROR:\n{e}",
            503
        )


@app.route("/investigate")
def investigate():
    """
    Run the full investigation and return results
    """
    results = run_investigation()
    
    # Format for display
    output = f"""WAPA/Field59 Stream Investigation Results
==========================================

WAPA Page Candidates:
  Field59 Players: {len(results['wapa_page_findings']['field59_players'])}
  Embedded URLs: {len(results['wapa_page_findings']['embedded_urls'])}
  Script URLs: {len(results['wapa_page_findings']['script_configs'])}

URL Status Summary:
  Accessible (200): {len(results['permanent_sources'])}
  Event-gated (403): {len(results['event_gated_sources'])}
  Inaccessible: {len(results['inaccessible_sources'])}

Permanent Stream Sources Found: {len(results['permanent_sources']) > 0}

Full Results:
{json.dumps(results, indent=2)}
"""
    return output, 200


if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=8080
        )
    
