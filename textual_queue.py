""" Download progress, calls functions from functions.py and batch_download.py as Workers """

import spotify_client, spotipy, yt_dlp
import functions

from rich.text import Text
from textual import work
from textual.binding import Binding
from textual.containers import Vertical
from textual.screen import Screen
from textual.widgets import DataTable, Footer, LoadingIndicator, Static, ProgressBar


# what each status should look like
STYLES = {"queued": "dim", "downloading": "yellow", "done": "green",
          "failed": "red", "cancelled": "dim"}   # module level, above the class


class QueueScreen(Screen):

    BINDINGS = [("c", "cancel_downloads", "Cancel"), ("escape", "back", "Back")]

    # cancel off by default and map failed songs to a list of strings
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.cancel_requested = False
        self.failures: list[str] = []
        self.counts = {"done": 0, "failed": 0, "cancelled": 0}
        self.finished = False


    def compose(self):
        
        yield Vertical(
            Static("Downloading Songs...", id="status"),
            ProgressBar(total=len(self.app.selected_tracks), show_eta=True, id="overall"),
            DataTable(id="queue_table", cursor_type="row"),
            Static("", id="failures"),
        )
        yield Footer()


    def on_mount(self):

        # create table and 
        table = self.query_one("#queue_table", DataTable)
        table.add_column("Title", key="title")
        table.add_column("Artist", key="artist")
        table.add_column("Album", key="album")

        # from tracks.py, in the action_download func, we have the "selected_tracks" variable that is a set() of playlists, unpack, enum and add metadata to each track
        for i, t in enumerate(self.app.selected_tracks):
            table.add_row(
                Text(t["track_name"]),
                Text(", ".join(t["artist_names"],)),
                Text("queued"),
                key=str(i),
            )

        # donw show failures until there are some to show
        self.query_one("#failures", Static).display = False
        self.run_queue()


    # running the downlaod queue in an exclusive worker thread, loop over tracks; skip if self.cancel_request is called
    @work(thread=True, exclusive=True)
    def run_queue(self):

        # call the settings global dict from menu.py and use that to initialise settings and change if needed
        settings = self.app.settings    
        output_dir = settings["output_path"]

        # loop over tracks and skip if cancel_requested is called
        for i, track in enumerate(self.app.selected_tracks):
            if self.cancel_requested:
                self.app.call_from_thread(self.set_status, i, "cancelled")
                continue

            # elif set the downloading status, and try to download the songs
            self.app.call_from_thread(self.set_status, i, "downloading")
            try:
                functions.download_spotify_song(
                    settings["format"], track, output_dir,
                    settings["cookie_file"], settings["platform"]
                )
            except Exception as e:
                self.app.call_from_thread(self.set_status, i, "failed", str(e))
            else:
                self.app.call_from_thread(self.set_status, i, "done")

        self.app.call_from_thread(self.finish)


    # update a row cell's status and overall progress bar, for main trhead only
    def set_status(self, idx: int, status: str, note: str = ""):

        # set the label for the current album in the data table row, use the status string and note to show the actual status of the download and update that cell
        # each failure is stored as "name: reason"
        table = self.query_one("#queue_table", DataTable)
        label = f"{status}: {note}" if note else status
        table.update_cell(str(idx), "status", Text(label, style=STYLES[status]))

        #check status and move on if no issues, else append failed ones to "failed" list with track number and actual "track_name"
        if status in self.counts:
            self.counts += 1
            self.query_one("#overall", ProgressBar).advance(1)
        if status == "failed":
            name = self.app.selected_tracks[idx]["track_name"]
            self.failures.append(f"{name}: {note}")


    # signifies end of queue show N done and X failed, enable functionality to go Back and list of failures 
    def finish(self):

        # finish the current queue, shoe the user a summary of done and faile, if cancelled, append the number of cancelled with counts to the count dict,
        # update status then show sumamry and give option to go back 
        self.finished =  True
        c = self.counts
        summary = f"Finished: {c['done']} done, {c['failed']} failed"
        if c["cancelled"]:
            summary += f", {c['cancelled']}, cancelled"
            self.query_one("#status", Static).update(Text(summary + " (esc to go back)"))

        # if any failed, create a status update, join on list if failues and show fstring of strs inside, and show notif
        box = self.query_one("#failures", Static)
        box.update(Text("Failed:\n" + "\n".join(self.failures), style="red"))
        box.display = True


    def action_cancel_downloads(self):

        # if finished returns true, return, otherwise set cancel_requested to true and query status to update
        if self.finished:
            return
        self.cancel_requested = True
        self.query_one("#status", Static).update(Text("Cancelling after the current track..."))


    def action_back(self):

        # if finished is false, update to notify user to let the downloads finish or cancel, then pop screen to return
        if not self.app.finished:
            self.query_one("#status", Static).update(Text("Still downloading, press c to cancel first.", style="yellow"))
            return

        # will need to return back to menu, or the previous screen.
        self.app.pop_screen()
