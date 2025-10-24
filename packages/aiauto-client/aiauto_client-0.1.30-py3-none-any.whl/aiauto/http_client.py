"""HTTP client for Connect RPC communication with Next.js server."""
import requests
from typing import Dict, Any, Optional
from ._config import AIAUTO_API_TARGET


class ConnectRPCClient:
    """Client for calling Connect RPC endpoints via HTTP/JSON."""
    
    def __init__(self, token: str, base_url: Optional[str] = None):
        self.token = token
        # Convert gRPC target to HTTP URL
        if base_url:
            self.base_url = base_url
        else:
            # AIAUTO_API_TARGET is like "api.common.aiauto.pangyo.ainode.ai:443"
            # Convert to "https://api.common.aiauto.pangyo.ainode.ai"
            host = AIAUTO_API_TARGET.split(':')[0]
            self.base_url = f"https://{host}"
        
        self.headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "Connect-Protocol-Version": "1"
        }
    
    def call_rpc(self, method: str, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """Call a Connect RPC method and return the response."""
        url = f"{self.base_url}/api/aiauto.v1.AIAutoService/{method}"
        
        try:
            response = requests.post(url, json=request_data, headers=self.headers)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.HTTPError as e:
            # Connect RPC error format
            if e.response and e.response.headers.get('content-type', '').startswith('application/json'):
                try:
                    error_data = e.response.json()
                    # Connect RPC returns error in 'message' field
                    error_msg = error_data.get('message', '')
                    if error_msg:
                        raise RuntimeError(f"Server error: {error_msg}") from e
                    # Fallback to full error data if no message
                    raise RuntimeError(f"Server error: {error_data}") from e
                except ValueError:
                    # JSON decode failed
                    pass
            # Fallback to basic HTTP error
            raise RuntimeError(f"HTTP {e.response.status_code} error: {e.response.text if e.response else str(e)}") from e
        except requests.exceptions.RequestException as e:
            raise RuntimeError(f"Request failed: {e}") from e


def map_http_error(exc: Exception) -> Exception:
    """Convert HTTP/Connect RPC errors to standard exceptions."""
    # For now, just pass through the exception
    # In the future, we can add more sophisticated error mapping
    return exc