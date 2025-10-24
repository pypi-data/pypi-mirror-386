"""
Internal module for managing global state.
"""

# Global state
_current_run = None
_token = None
_api_base_url = "https://digilog-server.vercel.app/api/v1"
#_api_base_url = "http://localhost:3000/api/v1" ## For my local testers :)
_foom_config = {}  # Store foom2 configuration

def get_current_run():
    """Get the currently active run."""
    return _current_run

def set_api_base_url(url):
    """Set the API base URL."""
    global _api_base_url
    _api_base_url = url

def get_api_base_url():
    """Get the current API base URL."""
    return _api_base_url

def set_foom_config(server_url=None, api_key=None):
    """Set the foom2 configuration."""
    global _foom_config
    if server_url:
        _foom_config["server_url"] = server_url
    if api_key:
        _foom_config["api_key"] = api_key

def get_foom_config():
    """Get the foom2 configuration."""
    return _foom_config 