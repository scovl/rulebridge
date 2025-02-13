import time
import json
import requests
from pathlib import Path
from typing import Optional, Dict
from src.config import CLIENT_ID, CLIENT_KEY, REALM, PROXIES

class TokenManager:
    def __init__(self):
        self.auth_file = Path("config/auth.json")
        self.auth_url = "https://api.stackspot.com/v1/auth"
        self.post_url = "https://api.stackspot.com/v1/completions"
        self.get_url = "https://api.stackspot.com/v1/rules"
        
        self.auth_header = {'Content-Type': 'application/x-www-form-urlencoded'}
        self.data_urlencode = {
            'client_id': CLIENT_ID,
            'client_secret': CLIENT_KEY,
            'realm': REALM,
            'grant_type': 'client_credentials'
        }

    def is_token_expired(self, auth_data: Dict) -> bool:
        obtained_at = auth_data.get('obtained_at', 0)
        expires_in = auth_data.get('expires_in', 0)
        return (time.time() - obtained_at) > expires_in

    def get_token(self) -> Optional[Dict]:
        try:
            response = requests.post(
                self.auth_url,
                headers=self.auth_header,
                data=self.data_urlencode,
                proxies=PROXIES
            )
            
            if response.status_code == 200:
                auth_data = response.json()
                auth_data['obtained_at'] = time.time()
                
                with open(self.auth_file, 'w') as f:
                    json.dump(auth_data, f, indent=2)
                
                return auth_data
            else:
                print(f"Erro ao obter token: {response.status_code}")
                return None
                
        except Exception as e:
            print(f"Erro durante autenticação: {e}")
            return None

    def ensure_valid_token(self) -> Dict:
        try:
            # Check if auth file exists
            if self.auth_file.exists():
                with open(self.auth_file, 'r') as f:
                    auth_data = json.load(f)
                
                # Get new token if current is expired
                if self.is_token_expired(auth_data):
                    auth_data = self.get_token()
            else:
                # Create new token if no auth file
                auth_data = self.get_token()
            
            if auth_data:
                # Build headers with valid token
                return {
                    'Content-Type': 'application/json',
                    'Authorization': f"Bearer {auth_data['access_token']}",
                    'X-Client-Id': CLIENT_ID,
                    'X-Realm': REALM
                }
            else:
                raise Exception("Could not obtain valid token")
                
        except Exception as e:
            print(f"Error ensuring valid token: {e}")
            raise

    # ... métodos de autenticação 