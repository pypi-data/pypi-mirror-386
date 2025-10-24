import ctypes
import sys

from fts.app.config import LOG_FILE
from textual.app import App, ComposeResult
from textual.containers import Vertical, Horizontal
import asyncio

import fts.app.backend.transfer as transfer
from fts.app.backend.contacts import start_discovery_responder
from fts.app.backend.transfer import TransferHandler
from fts.app.frontend.chat import Chat
from fts.app.frontend.contacts import Contacts
from fts.app.frontend.requests import Requests
from fts.app.frontend.sending import Sending
from fts.app.frontend.transfers import Transfers
from fts.app.style.tcss import css
import fts.py as fts


def setup(transfer_ui: Transfers, requests_ui: Requests) -> None:
    fts.logger = LOG_FILE
    start_discovery_responder()
    transfer.transfer_handler = TransferHandler(transfer_ui, requests_ui)

class FTSApp(App):

    #CSS_PATH = [
    #    "style\\main.tcss",
    #    "style\\contacts.tcss",
    #    "style\\transfers.tcss",
    #    "style\\chat.tcss",
    #    "style\\sending.tcss",
    #    "style\\requests.tcss",
    #]

    CSS = css

    def compose(self) -> ComposeResult:
        #yield Header()
        #yield Footer()

        with Vertical():
            with Horizontal(id="toprow"):
                yield Contacts(id="toprowa")
                yield Sending(id="toprowb")
                requests = Requests(id="toprowc")
                yield requests

            with Horizontal(id="bottomrow"):
                yield Chat(id="bottomrowa")
                transfers = Transfers(id="bottomrowb")
                yield transfers

        setup(transfer_ui=transfers, requests_ui=requests)

    async def action_quit(self) -> None:
        transfer.transfer_handler.cancel_all()
        await asyncio.sleep(1)
        await super().action_quit()

def start():
    if sys.platform == "win32":  # Check if running on Windows
        try:
            ctypes.windll.shcore.SetProcessDpiAwareness(1)
        except AttributeError:
            # Handle cases where SetProcessDpiAwareness might not be available
            pass

    FTSApp().run()