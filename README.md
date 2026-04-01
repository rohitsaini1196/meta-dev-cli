# meta-dev-cli

**CLI for Meta Developer Apps and WhatsApp Cloud API**

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![WhatsApp Cloud API](https://img.shields.io/badge/WhatsApp-Cloud%20API-25D366?logo=whatsapp)](https://developers.facebook.com/docs/whatsapp/cloud-api)

> Unofficial CLI — not affiliated with Meta Platforms, Inc.

Stop clicking through the Meta Developer Dashboard. Manage your Meta apps and WhatsApp Business API entirely from the terminal — send messages, manage templates, configure webhooks, and inspect your setup in seconds.

Works great as a standalone tool, in scripts, and as a tool for **AI agents** (Cursor, Claude Code, Codex, etc.).

---

## Why

Every WhatsApp developer knows the pain:

- Open browser → navigate to developers.facebook.com
- Find the right app → click through to API Setup
- Copy a phone number ID → paste it somewhere
- Send a test message → wait for the dashboard to load

`meta-dev-cli` replaces all of that:

```bash
meta wa send +919876543210 "Hello"
# ✓ Message sent. ID: wamid.HBgL...
```

---

## Install

**Requirements:** Python 3.10+

```bash
git clone https://github.com/your-org/meta-dev-cli
cd meta-dev-cli
pip install -e .
```

---

## 2-Minute Setup

```bash
# 1. Log in with your Meta access token
meta login

# 2. Set your app (find ID at developers.facebook.com/apps)
meta apps use 974600134898061

# 3. Configure WhatsApp (find IDs at app → WhatsApp → API Setup)
meta wa setup --waba-id 1288248205964604 --phone-number-id 1103232902865858

# 4. Send your first message
meta wa send +919876543210 "Hello from the terminal 🚀"
```

---

## Commands

### Auth
```bash
meta login                          # shows setup guide, prompts for token
meta login --token EAAG...          # non-interactive
```

### Apps
```bash
meta apps list                      # list Meta apps (requires user_applications permission)
meta apps use <app-id>              # set default app
meta apps info                      # details of selected app
```

### WhatsApp
```bash
meta wa phone-numbers               # list all numbers in your WABA
meta wa setup --waba-id X --phone-number-id Y   # configure sender
meta wa send <phone> <message>      # send a text message
meta wa send-test <phone>           # send hello_world template
meta wa templates list              # list message templates
meta wa webhook set <url>           # configure webhook
meta wa webhook test                # verify webhook handshake
```

### Config
```bash
meta config show                    # show current config (token masked)
meta config show --json             # machine-readable state
meta config reset                   # clear all config
```

---

## JSON Output

Every command supports `--json`. Perfect for scripts, CI, and AI agents:

```bash
meta wa send +14155552671 "ping" --json
```
```json
{
  "message_id": "wamid.HBgLMTQxNT...",
  "status": "sent",
  "to": "14155552671"
}
```

```bash
meta wa phone-numbers --json
```
```json
{
  "data": [
    {
      "id": "1103232902865858",
      "display_phone_number": "+91 98765 43210",
      "verified_name": "My Business",
      "status": "CONNECTED"
    }
  ]
}
```

```bash
meta config show --json
```
```json
{
  "access_token": "EAAG...",
  "default_app_id": "974600134898061",
  "waba_id": "1288248205964604",
  "phone_number_id": "1103232902865858"
}
```

---

## For AI Agents

`meta-dev-cli` is designed to be called by AI agents (Cursor, Claude Code, GitHub Copilot, Codex, LangChain tools, etc.).

- All commands return structured JSON with `--json`
- Exit code `0` = success, `1` = error
- Errors go to stderr; data goes to stdout
- `meta config show --json` lets an agent detect what's already configured
- `CLAUDE.md` in this repo gives agents a full reference

```python
import subprocess, json

def check_setup():
    result = subprocess.run(["meta", "config", "show", "--json"], capture_output=True, text=True)
    return json.loads(result.stdout)

def send_whatsapp(phone, message):
    result = subprocess.run(
        ["meta", "wa", "send", phone, message, "--json"],
        capture_output=True, text=True
    )
    return json.loads(result.stdout)
```

See [CLAUDE.md](./CLAUDE.md) for the complete agent guide.

---

## Getting a Token

Run `meta login` — it shows a full setup guide. Quick version:

| Use case | Where to get token |
|---|---|
| Development / testing | [Graph API Explorer](https://developers.facebook.com/tools/explorer) → Generate Access Token |
| Production | [Business Settings](https://business.facebook.com/settings) → System Users → Generate Token |

Required permissions: `whatsapp_business_messaging`, `whatsapp_business_management`

---

## Error Handling

All errors show an actionable hint:

```
╭─ Error ──────────────────────────────────────────────────────────╮
│ No WhatsApp Business Account ID configured.                      │
│                                                                  │
│ Find your WABA ID:                                               │
│   1. Go to https://developers.facebook.com/apps                  │
│   2. Select your app → WhatsApp → API Setup                      │
│   3. Copy the 'WhatsApp Business Account ID'                     │
│                                                                  │
│ Then run: meta wa setup --waba-id <id> --phone-number-id <id>    │
╰──────────────────────────────────────────────────────────────────╯
```

---

## Development

```bash
pip install -e ".[dev]"
pytest                    # 35 tests
```

---

## Roadmap

- [ ] `meta wa templates create` — create message templates
- [ ] `meta wa templates status` — track approval status
- [ ] `meta logs` — stream webhook delivery logs
- [ ] `meta profile dev/prod` — switch between environments
- [ ] PyPI release (`pip install meta-dev-cli`)
- [ ] Shell completions (bash/zsh/fish)

---

## Contributing

PRs welcome. Please open an issue first for large changes.

---

## License

MIT — see [LICENSE](./LICENSE).

> This project is not affiliated with, endorsed by, or sponsored by Meta Platforms, Inc.
> WhatsApp is a trademark of Meta Platforms, Inc.
