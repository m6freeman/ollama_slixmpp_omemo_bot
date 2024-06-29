from getpass import getpass
import pytest
from src.ollama_slixmpp_omemo_bot import ollama_bot


class TestOllamaSlixmppOmemoBot:
    def setup_method(self):
        """Assemble common resources to be acted upon"""

    def test_authentication(self):
        jid = input("JID: ")
        pw = getpass()
        assert ollama_bot.OllamaBot(jid, pw).jid == jid
