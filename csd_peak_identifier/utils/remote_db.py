import requests
import json
from csd_peak_identifier.gui.constants import API_URL

class RemoteDatabaseBackend:
    """
    Handles communication with the remote ECRIS database server.
    Mirrors the DatabaseManager interface.
    """
    def __init__(self, api_url=API_URL):
        self.api_url = api_url.rstrip('/')

    def _get(self, endpoint, params=None):
        try:
            response = requests.get(f"{self.api_url}/db/{endpoint}", params=params, timeout=5)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"Remote DB Get Error ({endpoint}): {e}")
            return None

    def _post(self, endpoint, data):
        try:
            response = requests.post(f"{self.api_url}/db/{endpoint}", json=data, timeout=5)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"Remote DB Post Error ({endpoint}): {e}")
            return None

    def get_all_users(self):
        result = self._get("users")
        return result if result is not None else []

    def add_user(self, username):
        return self._post("users/add", {"username": username})

    def update_last_used(self, username):
        return self._post("users/update_last_used", {"username": username})

    def get_user_stats(self, username):
        result = self._get("stats", {"username": username})
        if result:
            return result.get("eval_count", 0), result.get("pending_count", 0)
        return 0, 0

    def get_random_pending_timestamp(self, username):
        result = self._get("pending_random", {"username": username})
        if result:
            return result.get("csd_timestamp")
        return None

    def get_leaderboard(self):
        result = self._get("leaderboard")
        return result if result is not None else []

    def save_evaluation(self, username, csd_timestamp, analysis_results):
        data = {
            "username": username,
            "csd_timestamp": csd_timestamp,
            "results": analysis_results
        }
        return self._post("evaluations/save", data)
