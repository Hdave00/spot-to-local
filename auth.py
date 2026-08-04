# Using spotipy, SpotifyOAuth opens the browser but doesn't catch the redirect itself because by default it expects the user to manually 
# paste the redirected URL back into the terminal. For an "auto-login" experience, 
# we make a temp HTTP loopback server, which grabs the code param and hands it to spotipy programmatically

"""Spotify OAuth via local loopback server. The HTTP
server here exists for the few seconds it takes to catch the redirect."""

import threading
import webbrowser
from http.server import BaseHTTPRequestHandler, HTTPSServer
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

    """ Spins up a one-shot local server on the redirect URI's host/port,
    opens the browser, blocks until Spotify redirects back, then shuts down. """

    # save the url parse, host and port, to pass to the HTTPSserver for the class to handle the request for the auth code
    parsed = urlparse(redirect_uri)
    host, port = parsed.hostname, parsed.port

    # server variable to store the host and port of the https server and the properties of the callbackhandler class, keep the auth_code and auth_error none
    server = HTTPSServer((host, port), _CallbackHandler)
    server.auth_code = None
    server.auth_error = None

    # handle_request() serves only one request and then should return, give user 2 mins to complete the login in the browser
    thread = threading.Thread(target=server.handle_request)
    thread.start()
    thread.join(timeout=120)

    return server.auth_code

#TODO, functions to get the spotify Oauth, to return a ready usable spotipy client and finally a logout function to log the client out  