# Using spotipy, SpotifyOAuth opens the browser but doesn't catch the redirect itself because by default it expects the user to manually 
# paste the redirected URL back into the terminal. For an "auto-login" experience, 
# we make a temp HTTP loopback server, which grabs the code param and hands it to spotipy programmatically

"""Spotify OAuth via local loopback server. The HTTP
server here exists for the few seconds it takes to catch the redirect."""

import threading
import webbrowser
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse, parse_qs

import spotipy
from spotipy.oauth2 import SpotifyOAuth
from spotipy.cache_handler import CacheFileHandler

import config

class _CallbackHandler(BaseHTTPRequestHandler):
    """ Captures the ?code=... param Spotify redirects back with, then dies. """

    # function to handle the GET request to handle the temp HTTPS server and send appropriate headers
    def do_GET(self):

        """ Method to handle get request, successful login and errors. """

        query = parse_qs(urlparse(self.path).query)
        self.server.auth_code = query.get("code", [None])[0]
        self.server.auth_error = query.get("error", [None])[0]

        # now create the headers to be sent
        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.end_headers()

        # if the auth code is as expected, then show the user by injecting html that all is good and they can return to the program, else say login failed
        # encode the message string in utf-8 format
        if self.server.auth_code:
            msg = "<h2> Login successful, you can close this tab and return to the spot-to-local app. </h2>"
        else:
            msg = f"<h2> Login failed: {self.server.auth_error}</h2>"

        self.wfile.write(msg.encode("utf-8"))

    def log_message(self, format, *args):
        pass # silence default request logging


def get_auth_code(redirect_uri: str) -> str | None:

    """ Spins up a one time local server on the redirect URI's host/port,
    opens the browser, blocks until Spotify redirects back, then shuts down. """

    # save the url parse, host and port, to pass to the HTTPserver for the class to handle the request for the auth code
    parsed = urlparse(redirect_uri)
    host, port = parsed.hostname, parsed.port

    # server variable to store the host and port of the https server and the properties of the callbackhandler class, keep the auth_code and auth_error none
    server = HTTPServer((host, port), _CallbackHandler)
    server.auth_code = None
    server.auth_error = None

    # handle_request() serves only one request and then should return, give user 2 mins to complete the login in the browser
    thread = threading.Thread(target=server.handle_request)
    thread.start()
    thread.join(timeout=120)

    return server.auth_code


def get_spotify_oauth() -> SpotifyOAuth:

    """ Returns the user's spofity metadata """

    return SpotifyOAuth(
        client_id=config.CLIENT_ID,
        client_secret=config.CLIENT_SECRET,
        redirect_uri=config.REDIRECT_URI,
        scope=config.SCOPE,
        cache_handler=CacheFileHandler(cache_path=config.TOKEN_CACHE_PATH),
        open_browser=False,  # we control browser-opening ourselves below

    )


def get_authenticated_client() -> spotipy.Spotify:

    """Returns a ready-to-use spotipy client. Uses cached token if valid,
    refreshes silently if expired, otherwise runs the full browser login flow."""

    sp_oauth = get_spotify_oauth()
    token_info = sp_oauth.validate_token(sp_oauth.cache_handler.get_cached_token())

    # check for token_info:
    if not token_info:
        auth_url = sp_oauth.get_authorize_url()

        # since the webbrowser.open method returns either True or False on success or failure (repsectively) to open a webbrowser tab automotically, try-except-raise it
        # NOTE In Textual, we want to actually render that URL as clickable text in the login screen like a static widget rather than relying on stdout, since Textual takes over the terminal display
        try:
            opened = webbrowser.open(auth_url)
        except webbrowser.Error as e:
            raise RuntimeError(
                f"Could not launch a browser automatically: {e}\n"
                f"Open this URL manually to log in: \n{auth_url}"
            )

        if not opened:
            raise RuntimeError(
                f"Browser did not open automatically.\n"
                f"Open this URL manually to log in:\n{auth_url}"
            )

        code = get_auth_code(config.REDIRECT_URI)

        if not code:
            raise RuntimeError("Login was timed out or denied. Please try again.")

        token_info = sp_oauth.get_access_token(code, as_dict=True, check_cache=False)


    # now return the spotipy client with the acces token
    return spotipy.Spotify(auth=token_info["acces_token"])


# Finally, log the user out
def logout():

    """ Clears the cached token, forcing a fresh login next time. """

    import os
    if os.path.exists(config.TOKEN_CACHE_PATH):
        os.remove(config.TOKEN_CACHE_PATH)