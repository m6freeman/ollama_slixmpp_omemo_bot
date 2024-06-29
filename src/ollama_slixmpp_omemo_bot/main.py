# -*- coding: utf-8 -*-
import os
import sys
import logging
from getpass import getpass
from argparse import ArgumentParser

import slixmpp_omemo

from ollama_bot import OllamaBot

log = logging.getLogger(__name__)

if __name__ == "__main__":
    parser = ArgumentParser(description=OllamaBot.__doc__)
    parser.add_argument(
        "-q",
        "--quiet",
        help="set logging to ERROR",
        action="store_const",
        dest="loglevel",
        const=logging.ERROR,
        default=logging.INFO,
    )
    parser.add_argument(
        "-d",
        "--debug",
        help="set logging to DEBUG",
        action="store_const",
        dest="loglevel",
        const=logging.DEBUG,
        default=logging.INFO,
    )
    parser.add_argument("-j", "--jid", dest="jid", help="JID to use")
    parser.add_argument("-p", "--password", dest="password", help="password to use")
    DATA_DIR = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        "omemo",
    )
    parser.add_argument(
        "--data-dir", dest="data_dir", help="data directory", default=DATA_DIR
    )
    args = parser.parse_args()
    logging.basicConfig(level=args.loglevel, format="%(levelname)-8s %(message)s")
    if args.jid is None:
        args.jid = input("JID: ")
    if args.password is None:
        args.password = getpass("Password: ")
    os.makedirs(args.data_dir, exist_ok=True)
    xmpp = OllamaBot(args.jid, args.password)
    xmpp.register_plugin("xep_0030")  # Service Discovery
    xmpp.register_plugin("xep_0199")  # XMPP Ping
    xmpp.register_plugin("xep_0380")  # Explicit Message Encryption
    try:
        xmpp.register_plugin(
            "xep_0384",
            {
                "data_dir": args.data_dir,
            },
            module=slixmpp_omemo,
        )
    except slixmpp_omemo.PluginCouldNotLoad:
        log.exception("And error occured when loading the omemo plugin.")
        sys.exit(1)
    xmpp.connect()
    xmpp.process()
