
# Ollama Slixmpp Bot with OMEMO

A basic echo-bot built with slixmpp and slixmpp-omemo that relays your messages to a locally running ollama server with end to end encryption.

## Dependancies

- [ollama 0.1.14](https://ollama.com/download/linux)
- [LLM](https://ollama.com/library)
    - [llama3](https://ollama.com/library/llama3)

## Installation

```bash
git clone --bare https://github.com/m6freeman/ollama_slixmpp_omemo_bot
cd repo_name; git worktree add main; cd main
python -m venv .venv; ./.venv/bin/activate
pip install -r requirements.txt
# There is a httpx dependancy conflict. These should be installed in this order.
pip install ollama; pip install ollama-python
```

## Usage

First Terminal instance
```bash
ollama serve
```

Second Terminal instance
```bash
PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION=python python ./src/ollama_slixmpp_omemo_bot/main.py
# Enter JID: service-account@example-server.im
# Enter Password: 
```

With OMEMO and Blind Trust enabled, message service-account@example-server.im from another account.

Recommended and tested clients:
- Conversations
- Profanity
    - You may need to manually trust their fingerprint

## Development

Read the [CONTRIBUTING.md](CONTRIBUTING.md) file.

## Credit

[Slixmpp OMEMO plugin | Copyright (C) 2010  Nathanael C. Fritz | Copyright (C) 2019 Maxime “pep” Buquet <pep@bouah.net>](https://codeberg.org/sxavier/slixmpp-omemo/src/branch/main/examples/echo_client.py)
