# OPDL Discord bot

Python bot that lays out the [One Piece Decklists](https://onepiecedecklists.com) Discord: generic rooms, an **OP17** category, a channel per leader on the site, pinned consensus lists, and a flair page with a little One Piece face for each leader.

Invite the bot, run `/opdl-setup` once, then `/opdl-consensus` whenever the site lists refresh.

## What it creates

**Information** (read-only pages)

- `#welcome`
- `#rules`
- `#announcements`
- `#flair` — button picker, one favorite leader at a time

**Community**

- `#general` `#deck-help` `#tournament-talk` `#shop-orders` `#off-topic`

**OP17 · World's Strongest Warriors**

- `#op17-meta`
- `#edward-newgate` `#shanks` `#rocks-d-xebec` `#kaido` `#monkey-d-luffy` `#charlotte-linlin`

**Format staples** (every other leader page on the site)

- `#rg-luffy` `#nami` `#mihawk` `#portgas-d-ace` `#op13-ace` `#imu` `#enel` `#charlotte-katakuri`

Each leader channel gets a pinned consensus 50-card list averaged from `data/consensus-decks.json`. Later metas (OP18, …) are another category in `opdl_bot/config.py`.

## Flair faces

The bot crops the portrait off each leader card (the same Limitless art as the site) into a 128px Discord emoji, then puts that face on the flair buttons and roles. Unique per leader, so OP17 Luffy and RG Luffy do not share a sticker.

If the bot is already in another One Piece Discord, matching custom emojis in that guild can be reused; unique names from the public [emoji.gg](https://emoji.gg) Discord catalog are also checked. Card crops are the fallback so every site leader still gets a face.

## One-time Discord setup

1. Open [Discord Developer Portal](https://discord.com/developers/applications) → New Application → **OPDL**.
2. Bot → Add Bot. Copy the token.
3. Bot → Privileged Gateway Intents → turn **Server Members Intent** on.
4. OAuth2 → URL Generator:
   - Scopes: `bot`, `applications.commands`
   - Permissions: Manage Channels, Manage Roles, Manage Emojis and Stickers, Send Messages, Embed Links, Attach Files, Manage Messages, Read Message History, Add Reactions, Mention Everyone, View Channels
5. Open the generated URL, pick the OPDL server, authorize.
6. Drag the **OPDL** role above the `Leader · …` roles after first setup so flair can be assigned.

## Run locally

```bash
cd discord-bot
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# paste DISCORD_TOKEN (and optional DISCORD_GUILD_ID)
python bot.py --plan      # print layout, no Discord
python bot.py --emojis    # crop faces into assets/emojis
python bot.py             # connect
```

In the server, as an admin:

- `/opdl-setup` — categories, channels, roles, emojis, welcome/rules/announcements/flair, consensus pins
- `/opdl-consensus` — rewrite the pinned lists from the current site data
- `/opdl-flair` — rebuild the flair page
- `/opdl-leader shanks` — pin one list in the current channel

Re-running setup is safe: existing channels are reused and pins are edited in place.

## Hosting

Any always-on Python host works (a small VPS, Railway, Fly). The process is `python bot.py`. Keep `DISCORD_TOKEN` in the host's secret store, not in git.

`state.json` is written next to the bot after setup so channel IDs survive restarts. It is gitignored.
