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


def deep_inspect_field59_config():
    """
    Deep inspection of Field59 channel configuration
    Print COMPLETE raw response and all relevant fields
    """
    print("\n" + "="*70)
    print("DEEP FIELD59 CONFIGURATION INSPECTION")
    print("="*70)
    
    field59_url = "https://player.field59.com/v4/channel/wapa/07679d068d54d4a6b52e3a42e27aa151d502b09a"
    
    print(f"\nFetching: {field59_url}\n")
    
    try:
        response = requests.get(
            field59_url,
            headers=HEADERS,
            timeout=15,
            allow_redirects=True
        )
        
        print(f"HTTP Status: {response.status_code}")
        print(f"Content-Type: {response.headers.get('content-type', 'N/A')}")
        print(f"Content-Length: {len(response.text)} bytes")
        
        # Print complete raw response
        print("\n" + "="*70)
        print("COMPLETE RAW RESPONSE:")
        print("="*70)
        print(response.text[:5000])  # First 5000 chars
        if len(response.text) > 5000:
            print(f"\n... (response continues, total {len(response.text)} chars)")
            print("\n... LAST 2000 CHARS:")
            print(response.text[-2000:])
        
        # Attempt to parse as JSON
        print("\n" + "="*70)
        print("PARSED JSON STRUCTURE:")
        print("="*70)
        
        try:
            data = response.json()
            print(json.dumps(data, indent=2))
            
            # Now search for all relevant fields
            print("\n" + "="*70)
            print("RELEVANT FIELDS FOUND:")
            print("="*70)
            
            search_fields = [
                'clip', 'm3u8', 'url', 'stream', 'source', 'live', 
                'media', 'playlist', 'dockey', 'schedule', 'sharing', 
                'video', 'channel', 'event', 'broadcast', 'feed',
                'hls', 'dash', 'manifest', 'uri', 'href', 'path',
                'content', 'assets', 'provider', 'token', 'id'
            ]
            
            def search_json_recursive(obj, depth=0, parent_key=""):
                """Recursively search JSON for relevant fields"""
                indent = "  " * depth
                
                if isinstance(obj, dict):
                    for key, value in obj.items():
                        # Check if this key is relevant
                        if any(search_term in key.lower() for search_term in search_fields):
                            print(f"{indent}[{key}] = {str(value)[:200]}")
                            if len(str(value)) > 200:
                                print(f"{indent}  ... (truncated)")
                        
                        # Recurse into the value
                        search_json_recursive(value, depth + 1, key)
                
                elif isinstance(obj, list):
                    for idx, item in enumerate(obj):
                        if isinstance(item, (dict, list)):
                            print(f"{indent}[{idx}]:")
                            search_json_recursive(item, depth + 1, f"{parent_key}[{idx}]")
            
            search_json_recursive(data)
            
            # Specific deep inspection for stream/playlist
            print("\n" + "="*70)
            print("DEEP DIVE: Stream/Playlist Sources")
            print("="*70)
            
            def find_stream_sources(obj, path=""):
                """Find actual stream endpoints"""
                sources = []
                
                if isinstance(obj, dict):
                    # Check for m3u8, hls, stream URLs
                    for key, value in obj.items():
                        current_path = f"{path}.{key}" if path else key
                        
                        if isinstance(value, str):
                            if '.m3u8' in value or 'stream' in key.lower() or 'playlist' in key.lower():
                                sources.append({
                                    "path": current_path,
                                    "key": key,
                                    "value": value,
                                    "is_m3u8": '.m3u8' in value
                                })
                        
                        sources.extend(find_stream_sources(value, current_path))
                
                elif isinstance(obj, list):
                    for idx, item in enumerate(obj):
                        current_path = f"{path}[{idx}]"
                        sources.extend(find_stream_sources(item, current_path))
                
                return sources
            
            stream_sources = find_stream_sources(data)
            
            if stream_sources:
                print(f"\nFound {len(stream_sources)} stream-related entries:")
                for source in stream_sources:
                    print(f"\n  Path: {source['path']}")
                    print(f"  Key: {source['key']}")
                    print(f"  Value: {source['value']}")
                    print(f"  Is M3U8: {source['is_m3u8']}")
            else:
                print("\nNo direct M3U8/stream URLs found in JSON structure")
            
            # Check for event/schedule information
            print("\n" + "="*70)
            print("EVENT/SCHEDULE INFORMATION:")
            print("="*70)
            
            if 'schedule' in data:
                print(f"Schedule found: {json.dumps(data['schedule'], indent=2)[:1000]}")
            elif 'event' in data:
                print(f"Event found: {json.dumps(data['event'], indent=2)[:1000]}")
            elif 'events' in data:
                print(f"Events found: {json.dumps(data['events'], indent=2)[:1000]}")
            else:
                print("No schedule/event field found")
            
        except json.JSONDecodeError as e:
            print(f"Response is not valid JSON: {e}")
            print("Attempting regex extraction...")
            
            # Regex extraction
            urls = re.findall(r'https://[^\s"\'<>]+', response.text)
            if urls:
                print(f"\nURLs found via regex ({len(urls)} total):")
                for url in urls[:20]:
                    print(f"  - {url}")
        
        return response.text, response.status_code
        
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
        return None, 500


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
    Deep inspection of Field59 channel configuration
    """
    raw_response, status = deep_inspect_field59_config()
    
    output = f"""
FIELD59 CHANNEL CONFIGURATION - DEEP INSPECTION
================================================

This endpoint examined the complete raw response from:
https://player.field59.com/v4/channel/wapa/07679d068d54d4a6b52e3a42e27aa151d502b09a

See server logs for full details.

Key questions answered:
1. What M3U8 URLs are present? (event-specific vs. channel-level?)
2. What stream sources exist in the configuration?
3. Is there schedule/event information indicating current vs. default streams?
4. What alternate endpoints or fallbacks are available?

Check the application logs for the complete raw response and parsed structure.
"""
    
    return output, 200


if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=8080
        )
    
