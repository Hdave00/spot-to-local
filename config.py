"""config module loading Spotify client credentials from .env and setting up platform storage paths"""

import os
from dotenv import load_dotenv
from platformdirs import user_config_dir, user_cache_dir

APP_NAME = "spottolocal"

load_dotenv()

# spotify app credentials 
# Default (lsave, which is how its called as a spotify dev app), users can override via their own .env, or environment variables without doing any code stuff.
CLIENT_ID = os.getenv("SPOTIFY_CLIENT_ID")
CLIENT_SECRET = os.getenv("SPOTIFY_CLIENT_SECRET")
REDIRECT_URI = os.getenv("SPOTIFY_REDIRECT_URI", "http://127.0.0.1:8888/callback")

# Scopes: read-only access to playlists (public, private, and collaborative)
SCOPE = "playlist-read-private playlist-read-collaborative"

# check for client_id and client_secret, else raise runtime error with a message
if not CLIENT_ID or not CLIENT_SECRET:
    raise RuntimeError(
        "Missing SPOTIFY_CLIENT_ID / SPOTIFY_CLIENT_SECRET. " 
        "Set them in a .env file or as environment variables."
    )

# storage paths, these are OS agnostic and user specific. If a storage path doesn't exist, it will be created.
CONFIG_DIR = user_config_dir(APP_NAME)
CACHE_DIR = user_cache_dir(APP_NAME)
os.makedirs(CONFIG_DIR, exist_ok=True)
os.makedirs(CACHE_DIR, exist_ok=True)

TOKEN_CACHE_PATH = os.path.join(CONFIG_DIR, ".spotify_token_cache")