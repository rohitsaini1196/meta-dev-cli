# CLAUDE.md — Agent Guide for meta-dev-cli

This file is read automatically by Claude Code and compatible AI agents. It describes how to use the `meta` CLI to manage Meta Developer Apps and WhatsApp Cloud API resources.

---

## What This Tool Does

`meta` is a CLI for the Meta Graph API (v20.0). It manages:
- Meta developer app selection
- WhatsApp Business Account configuration
- Sending WhatsApp messages
- Listing phone numbers and message templates
- Configuring webhooks

All commands support `--json` for structured output. Use it when parsing results programmatically.

---

## Check Current State First

Before running any commands, check what's already configured:

```bash
meta config show --json
```

Returns:
```json
{
  "access_token": "EAAG...",
  "default_app_id": "123456789",
  "waba_id": "987654321",
  "phone_number_id": "555666777"
}
```

Fields with `null` need to be configured. Work through setup in order.

---

## Setup Workflow (run once)

### Step 1 — Authenticate

```bash
meta login --token <access_token>
```

Token must be a Meta Graph API User token or System User token. Tokens from the Graph API Explorer expire in ~1 hour. System User tokens don't expire.

Required permissions:
- `whatsapp_business_messaging`
- `whatsapp_business_management`

**Verify it worked:**
```bash
meta config show --json | python3 -c "import json,sys; d=json.load(sys.stdin); print('ok' if d['access_token'] else 'fail')"
```

---

### Step 2 — Set Default App

```bash
meta apps use <app_id>
```

The App ID is a numeric string (e.g. `974600134898061`).

To find it if you don't have it: go to https://developers.facebook.com/apps — it's shown in the app card.

Note: `meta apps list` may fail with a permissions error. In that case, obtain the App ID from the dashboard and use `meta apps use <id>` directly.

---

### Step 3 — Configure WhatsApp

```bash
meta wa setup --waba-id <waba_id> --phone-number-id <phone_number_id>
```

To find these IDs, list phone numbers (requires Step 2):
```bash
meta wa phone-numbers --json
```

This returns a list. Pick the phone number you want to send from and note its `id` (phone_number_id). The WABA ID comes from the Meta Developer Dashboard: app → WhatsApp → API Setup.

---

## Sending Messages

### Text message

```bash
meta wa send +14155552671 "Hello from the CLI" --json
```

Returns:
```json
{
  "message_id": "wamid.HBgLMTQxNTU...",
  "status": "sent",
  "to": "14155552671"
}
```

### Test message (hello_world template)

```bash
meta wa send-test +14155552671 --json
```

Returns:
```json
{
  "message_id": "wamid.HBgLMTQxNTU...",
  "status": "sent",
  "template": "hello_world",
  "to": "14155552671"
}
```

Phone numbers: include country code, with or without `+`. Formatting (spaces, dashes, parentheses) is stripped automatically.

---

## Listing Resources

### Phone numbers

```bash
meta wa phone-numbers --json
```

```json
{
  "data": [
    {
      "id": "555666777",
      "display_phone_number": "+1 415 555 2671",
      "verified_name": "My Business",
      "quality_rating": null,
      "status": "CONNECTED"
    }
  ]
}
```

### Message templates

```bash
meta wa templates list --json
```

```json
{
  "data": [
    {
      "id": "111222333",
      "name": "hello_world",
      "status": "APPROVED",
      "category": "UTILITY",
      "language": "en_US"
    }
  ]
}
```

### Apps

```bash
meta apps list --json
```

```json
{
  "data": [
    {
      "id": "974600134898061",
      "name": "MyApp",
      "category": null,
      "description": null
    }
  ]
}
```

### Current app info

```bash
meta apps info --json
```

---

## Webhook Configuration

```bash
# Set webhook (auto-generates verify token if not provided)
meta wa webhook set https://example.com/webhook --json

# Test that your server handles the verification handshake
meta wa webhook test
```

Webhook URL must be `https://`. The verify token is shown after setting — configure it on your server to respond to Meta's GET verification request.

---

## Error Patterns and Recovery

| Error message | Cause | Fix |
|---|---|---|
| `No access token found.` | Not logged in | `meta login --token <token>` |
| `No default app selected.` | App not set | `meta apps use <app-id>` |
| `No WhatsApp Business Account ID configured.` | WABA not set | `meta wa setup --waba-id <id> --phone-number-id <id>` |
| `No sender phone number ID configured.` | Phone not set | `meta wa setup --waba-id <id> --phone-number-id <id>` |
| `Invalid token` (code 190) | Token expired or wrong | `meta login --token <new-token>` |
| `(#100) Tried accessing nonexisting field (apps)` | Missing `user_applications` permission | Get App ID from dashboard, use `meta apps use <id>` directly |
| `Invalid phone number` | Bad phone format | Use E.164 format: `+14155552671` |

Exit code is `1` on any error, `0` on success.

---

## All Commands Quick Reference

```
meta login [--token TOKEN]

meta apps list [--json]
meta apps use <app-id>
meta apps info [--json]

meta wa phone-numbers [--json]
meta wa setup --waba-id <id> --phone-number-id <id>
meta wa send <phone> <message> [--json]
meta wa send-test <phone> [--json]
meta wa templates list [--json]
meta wa webhook set <url> [--verify-token TOKEN]
meta wa webhook test

meta config show [--json] [--reveal]
meta config reset [--force]
```

---

## Config File

`~/.meta-cli/config.json` — permissions `600` (owner only).

```json
{
  "access_token": "EAAG...",
  "default_app_id": "974600134898061",
  "waba_id": "1288248205964604",
  "phone_number_id": "1103232902865858"
}
```

Do not commit or log this file. Do not include it in shell history.

---

## Graph API Details

- Base URL: `https://graph.facebook.com/v20.0`
- Auth: `Authorization: Bearer <access_token>`
- Timeout: 30s per request
- Retry: up to 3 attempts on rate limits (codes 4, 17, 613) with exponential backoff

---

## Typical Agent Workflow

```python
# 1. Check what's configured
result = run("meta config show --json")
config = json.loads(result.stdout)

# 2. Run setup steps for anything missing
if not config["access_token"]:
    run(f"meta login --token {token}")

if not config["default_app_id"]:
    run(f"meta apps use {app_id}")

if not config["waba_id"] or not config["phone_number_id"]:
    run(f"meta wa setup --waba-id {waba_id} --phone-number-id {phone_number_id}")

# 3. Send a message
result = run(f'meta wa send {phone} "{message}" --json')
msg = json.loads(result.stdout)
print(msg["message_id"])
```
