#login.py          # triggers auth.py, shows waiting state while browser opens

""" Login screen: triggers the OAuth loopback flow in a background worker
so the TUI doesn't freeze while waiting on the browser. """

from textual.screen import Screen
from textual.containers import Vertical, Center
from textual.widgets import Static, Button, LoadingIndicator
from textual import work
import auth

# we need a new class to show the screen for the login banner and the status message
class LoginScreen(Screen):
    """ Shown on startup, attempts silent login with cached token first, falls back to full browser,
     then to manual retry state. """

    CSS = """
        LoginScreen {
            align: center middle;
        }
        #status {
            margin-top: 1;
            text-align: center;
        }
        #banner {
            text-align: center;
            color: cyan;
            text-style: bold;
        }

    """

    # function to compse the actual screen
    def compose(self):

        # using 'yield' to basically turn it into a generator which returns values one at a time and pause the func execution without losing current state
        yield Center(
            Vertical(
                Static("lsave", id="banner"),
                LoadingIndicator(id="spinner"),
                Static("Checking for existing login...", id="status"),
                Button("Retry Login", id="retry", variant="primary", disabled=True),

            )
        )

    # automatically start login in a background worker, so the user doesnt have to press a login button. NOTE - this is presuming there is a cached token
    def on_mount(self):
        self.attempt_login()


    # now for the second scenario, where the user needs to press a button to login
    def on_button_pressed(self, event: Button.Pressed):

        # if the id of the button pressed it retry, disable the button after the first click, and show loading indicatior
        # this is to avoid sending multiple login requests
        if event.button.id == "retry":
            self.query_one("#retry", Button).disabled = True
            self.query_one("#spinner", LoadingIndicator).display = True
            self.attempt_login()


    # Textuals decorator to run attempt_login in an actual OS thread rather than an async task, because auth.get_authenticated_client() is synchronous, ie
    # the thread.join(timeout=120) in the temp loopback server we make, is not an async/wait coroutine and the exclusive=True ensures more than one click of the
    # retry button, cancels the previous attempts instead of running 2 attempts
    @work(thread=True, exclusive=True)
    def attempt_login(self):

        # try the actual login, show the status by creating a static widget for info
        status = self.query_one("#status", Static)

        # we need the callable from the other thread above which is active and return the result (logged in or not and how)
        # this is because textual apps are apparently not thread safe, call_from_thread safely hops back onto the main UI thread to do the actual .update() call
        try:
            self.app.call_from_thread(
                status.update, "Waiting for Spotify login in your browser..."
            )

            sp = auth.get_authenticated_client()

        except RuntimeError as e:
            self.app.call_from_thread(self._on_login_failed, str(e))
            return
        except Exception as e:
            self.app.call_from_thread(self._on_login_failed, f"Unexpected error: {e}")
            return

        self.app.call_from_thread(self._on_login_success, sp)

        # now we need to make sure we show the right screen/widget when login is successfull or if it fails

        def _on_login_success(self, sp):

            # save the authenticated client on the App instance and switch screen to the playlists the user has in their accounts
            self.app.sp = sp
            self.app.switch_screen("playlists")


        def _on_login_failed(self, message: str):

            # remove the spinner, show the error message, and show retry button for full manual login again
            self.query_one("#spinner", LoadingIndicator).display = False
            self.query_one("#status", Static).update(f"[red]{message}[/red]")
            self.query_one("#retry", Button).disabled = False




