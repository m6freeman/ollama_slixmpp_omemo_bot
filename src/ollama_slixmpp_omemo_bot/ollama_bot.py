import re
from typing import Dict, Optional

import ollama
from slixmpp import ClientXMPP, JID
from slixmpp.exceptions import IqTimeout, IqError
from slixmpp.stanza import Message
from slixmpp.types import JidStr, MessageTypes
from slixmpp.xmlstream.handler import CoroutineCallback
from slixmpp.xmlstream.matcher import MatchXPath
from slixmpp_omemo import (
    EncryptionPrepareException,
    MissingOwnKey,
    NoAvailableSession,
    UndecidedException,
    UntrustedException,
)
from omemo.exceptions import MissingBundleException


LEVEL_DEBUG: int = 0
LEVEL_ERROR: int = 1


class OllamaBot(ClientXMPP):
    eme_ns: str = "eu.siacs.conversations.axolotl"
    cmd_prefix: str = "!"
    debug_level: int = LEVEL_DEBUG

    def __init__(self, jid: JidStr, password: str):
        ClientXMPP.__init__(self, jid, password)
        self.prefix_re: re.Pattern = re.compile(r"^%s" % self.cmd_prefix)
        self.cmd_re: re.Pattern = re.compile(
            r"^%s(?P<command>\w+)(?:\s+(?P<args>.*))?" % self.cmd_prefix
        )
        self.add_event_handler("session_start", self.start)
        self.register_handler(
            CoroutineCallback(
                "Messages",
                MatchXPath(f"{{{self.default_ns}}}message"),
                self.message_handler,
            )
        )

    def start(self, _: Dict) -> None:
        self.send_presence()
        self.get_roster()

    def is_command(self, body: str) -> bool:
        return self.prefix_re.match(body) is not None

    async def handle_command(
        self, mto: JID, mtype: Optional[MessageTypes], body: Optional[str]
    ) -> None:
        match = self.cmd_re.match(body)
        if match is None:
            return None
        groups = match.groupdict()
        cmd: str = groups["command"]
        # args = groups['args']
        if cmd == "help":
            await self.cmd_help(mto, mtype)
        elif cmd == "verbose":
            await self.cmd_verbose(mto, mtype)
        elif cmd == "error":
            await self.cmd_error(mto, mtype)
        return None

    async def cmd_help(self, mto: JID, mtype: Optional[MessageTypes]) -> None:
        body = (
            "I'm the slixmpp-omemo ollama bot! "
            "The following commands are available:\n"
            f"{self.cmd_prefix}verbose Send message or reply with log messages\n"
            f"{self.cmd_prefix}error Send message or reply only on error\n"
        )
        return await self.encrypted_reply(mto, mtype, body)

    async def cmd_verbose(self, mto: JID, mtype: Optional[MessageTypes]) -> None:
        self.debug_level: int = LEVEL_DEBUG
        body: str = """Debug level set to 'verbose'."""
        return await self.encrypted_reply(mto, mtype, body)

    async def cmd_error(self, mto: JID, mtype: Optional[MessageTypes]) -> None:
        self.debug_level: int = LEVEL_ERROR
        body: str = """Debug level set to 'error'."""
        return await self.encrypted_reply(mto, mtype, body)

    async def message_handler(
        self, msg: Message, allow_untrusted: bool = False
    ) -> None:
        mfrom: JID = msg["from"]
        mto: JID = msg["from"]
        mtype: Optional[MessageTypes] = msg["type"]
        if mtype not in ("chat", "normal"):
            return None
        if not self["xep_0384"].is_encrypted(msg):
            if self.debug_level == LEVEL_DEBUG:
                await self.plain_reply(
                    mto, mtype, f"Echo unencrypted message: {msg['body']}"
                )
            return None
        try:
            encrypted = msg["omemo_encrypted"]
            body: Optional[str] = await self["xep_0384"].decrypt_message(
                encrypted, mfrom, allow_untrusted
            )
            if body is not None:
                decoded: Optional[str] = body.decode("utf8")
                if self.is_command(decoded):
                    await self.handle_command(mto, mtype, decoded)
                elif self.debug_level == LEVEL_DEBUG:
                    ollama_server_response: Optional[str] = (
                        self.message_to_ollama_server(decoded)
                    )
                    await self.encrypted_reply(
                        mto, mtype, f"{ollama_server_response or ''}"
                    )
        except MissingOwnKey:
            await self.plain_reply(
                mto,
                mtype,
                "Error: Message not encrypted for me.",
            )
        except NoAvailableSession:
            await self.encrypted_reply(
                mto,
                mtype,
                "Error: Message uses an encrypted " "session I don't know about.",
            )
        except (UndecidedException, UntrustedException) as exn:
            await self.plain_reply(
                mto,
                mtype,
                f"Error: Your device '{exn.device}' is not in my trusted devices.",
            )
            await self.message_handler(msg, allow_untrusted=True)
        except EncryptionPrepareException:
            await self.plain_reply(
                mto, mtype, "Error: I was not able to decrypt the message."
            )
        except Exception as exn:
            await self.plain_reply(
                mto,
                mtype,
                "Error: Exception occured while attempting decryption.\n%r" % exn,
            )
            raise
        return None

    async def plain_reply(self, mto: JID, mtype: Optional[MessageTypes], body):
        msg = self.make_message(mto=mto, mtype=mtype)
        msg["body"] = body
        return msg.send()

    async def encrypted_reply(self, mto: JID, mtype: Optional[MessageTypes], body):
        msg = self.make_message(mto=mto, mtype=mtype)
        msg["eme"]["namespace"] = self.eme_ns
        msg["eme"]["name"] = self["xep_0380"].mechanisms[self.eme_ns]
        expect_problems: Optional[dict[JID, list[int]]] = {}
        while True:
            try:
                recipients = [mto]
                encrypt = await self["xep_0384"].encrypt_message(
                    body, recipients, expect_problems
                )
                msg.append(encrypt)
                return msg.send()
            except UndecidedException as exn:
                await self["xep_0384"].trust(exn.bare_jid, exn.device, exn.ik)
            except EncryptionPrepareException as exn:
                for error in exn.errors:
                    if isinstance(error, MissingBundleException):
                        await self.plain_reply(
                            mto,
                            mtype,
                            f'Could not find keys for device "{error.device}"'
                            f' of recipient "{error.bare_jid}". Skipping.',
                        )
                        jid: JID = JID(error.bare_jid)
                        device_list = expect_problems.setdefault(jid, [])
                        device_list.append(error.device)
            except (IqError, IqTimeout) as exn:
                await self.plain_reply(
                    mto,
                    mtype,
                    "An error occured while fetching information on a recipient.\n%r"
                    % exn,
                )
                return None
            except Exception as exn:
                await self.plain_reply(
                    mto,
                    mtype,
                    "An error occured while attempting to encrypt.\n%r" % exn,
                )
                raise

    def message_to_ollama_server(self, msg: Optional[str]) -> Optional[str]:
        if msg is not None:
            response = ollama.chat(
                model="llama3",
                messages=[
                    {
                        "role": "user",
                        "content": f"{msg}",
                    },
                ],
            )
            return response["message"]["content"]
