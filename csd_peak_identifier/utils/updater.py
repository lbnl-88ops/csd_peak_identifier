import requests
import packaging.version
from csd_peak_identifier.gui.constants import VERSION, GITHUB_RELEASES_URL

def check_for_updates():
    """
    Checks the GitHub API for the latest release.
    Returns (latest_version, release_url) if a newer version is available,
    otherwise returns (None, None).
    """
    # Use the /releases endpoint which includes pre-releases
    releases_url = GITHUB_RELEASES_URL.replace("/latest", "")
    try:
        response = requests.get(releases_url, timeout=5)
        response.raise_for_status()
        releases = response.json()
        
        if not releases:
            return None, None
            
        # The first release in the list is the most recent
        for data in releases:
            if data.get("prerelease", False):
                continue  # Skip pre-releases unless we want to support a "beta channel" later
                
            latest_tag = data.get("tag_name", "").lstrip("v")
            release_url = data.get("html_url", "")
            
            if not latest_tag:
                continue
                
            current_v = packaging.version.parse(VERSION)
            latest_v = packaging.version.parse(latest_tag)
            
            if latest_v > current_v:
                return latest_tag, release_url
            
            # Since releases are sorted by date, if the first non-prerelease 
            # isn't newer, no subsequent one will be.
            break
            
    except Exception as e:
        print(f"Error checking for updates: {e}")
        
    return None, None
