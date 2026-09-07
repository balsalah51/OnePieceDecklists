"""Create categories, channels, roles, emojis, and pinned pages. Idempotent."""

from __future__ import annotations

import json
from typing import Any

import discord

from .config import (
    ANNOUNCEMENTS_BODY,
    ASSETS_DIR,
    COLOR_HEX,
    GENERIC_CATEGORIES,
    INVITE_URL,
    LEADERS,
    METAS,
    RULES_BODY,
    SITE_URL,
    STATE_PATH,
    WELCOME_BODY,
    channel_name,
    emoji_name,
    leaders_for_meta,
    role_name,
    site_url,
)
from .data import format_consensus_embed, format_text_list, load_card_cache, load_consensus
from .emojis import ensure_all_faces
from .flair import FlairView, flair_embed

CONSENSUS_FOOTER_PREFIX = "OPDL consensus ·"


def load_state() -> dict:
    if STATE_PATH.exists():
        return json.loads(STATE_PATH.read_text())
    return {"guilds": {}}


def save_state(state: dict) -> None:
    STATE_PATH.write_text(json.dumps(state, indent=2) + "\n")


def guild_state(state: dict, guild_id: int) -> dict:
    guilds = state.setdefault("guilds", {})
    key = str(guild_id)
    return guilds.setdefault(key, {"channels": {}, "roles": {}, "emojis": {}, "messages": {}})


def find_category(guild: discord.Guild, name: str) -> discord.CategoryChannel | None:
    return discord.utils.get(guild.categories, name=name)


def find_channel(guild: discord.Guild, name: str) -> discord.abc.GuildChannel | None:
    return discord.utils.get(guild.channels, name=name)


async def ensure_category(guild: discord.Guild, name: str) -> discord.CategoryChannel:
    existing = find_category(guild, name)
    if existing:
        return existing
    return await guild.create_category(name, reason="OPDL setup")


def readonly_overwrites(guild: discord.Guild) -> dict:
    bot_member = guild.me
    overwrites: dict[discord.Role | discord.Member, discord.PermissionOverwrite] = {
        guild.default_role: discord.PermissionOverwrite(
            view_channel=True,
            read_message_history=True,
            send_messages=False,
            add_reactions=True,
        ),
    }
    if bot_member is not None:
        overwrites[bot_member] = discord.PermissionOverwrite(
            view_channel=True,
            read_message_history=True,
            send_messages=True,
            manage_messages=True,
            embed_links=True,
            attach_files=True,
            mention_everyone=True,
        )
    return overwrites


def chat_overwrites(guild: discord.Guild) -> dict:
    return {
        guild.default_role: discord.PermissionOverwrite(
            view_channel=True,
            read_message_history=True,
            send_messages=True,
        )
    }


async def ensure_text_channel(
    guild: discord.Guild,
    *,
    name: str,
    category: discord.CategoryChannel,
    topic: str,
    readonly: bool,
    news: bool = False,
) -> discord.TextChannel:
    existing = find_channel(guild, name)
    overwrites = readonly_overwrites(guild) if readonly else chat_overwrites(guild)
    if isinstance(existing, discord.TextChannel):
        kwargs: dict[str, Any] = {"overwrites": overwrites}
        if existing.category_id != category.id:
            kwargs["category"] = category
        if (existing.topic or "") != topic:
            kwargs["topic"] = topic[:1024]
        await existing.edit(**kwargs, reason="OPDL setup")
        return existing
    kwargs = {
        "name": name,
        "category": category,
        "topic": topic[:1024],
        "overwrites": overwrites,
        "reason": "OPDL setup",
    }
    if news:
        try:
            return await guild.create_text_channel(**kwargs, news=True)
        except discord.HTTPException:
            pass
    return await guild.create_text_channel(**kwargs)


async def ensure_role(guild: discord.Guild, leader: dict) -> discord.Role:
    name = role_name(leader)
    existing = discord.utils.get(guild.roles, name=name)
    color = discord.Color(COLOR_HEX[leader["color"]])
    if existing:
        if existing.color.value != color.value:
            await existing.edit(colour=color, reason="OPDL setup")
        return existing
    return await guild.create_role(
        name=name,
        colour=color,
        mentionable=True,
        hoist=False,
        reason="OPDL setup",
    )


async def ensure_leader_emoji(guild: discord.Guild, leader: dict) -> discord.Emoji | None:
    name = emoji_name(leader)
    existing = discord.utils.get(guild.emojis, name=name)
    if existing:
        return existing
    path = ASSETS_DIR / f"{name}.png"
    if not path.exists():
        return None
    try:
        return await guild.create_custom_emoji(name=name, image=path.read_bytes(), reason="OPDL leader face")
    except discord.HTTPException:
        return discord.utils.get(guild.emojis, name=name)


async def upsert_pinned(
    channel: discord.TextChannel,
    *,
    marker: str,
    embeds: list[discord.Embed],
    content: str | None = None,
    view: discord.ui.View | None = None,
) -> discord.Message:
    async for message in channel.history(limit=40):
        if message.author.id != channel.guild.me.id:
            continue
        footers = [emb.footer.text or "" for emb in message.embeds]
        if any(marker in (text or "") for text in footers) or (message.content and marker in message.content):
            await message.edit(content=content, embeds=embeds, view=view)
            if not message.pinned:
                try:
                    await message.pin(reason="OPDL page")
                except discord.HTTPException:
                    pass
            return message
    sent = await channel.send(content=content, embeds=embeds, view=view)
    try:
        await sent.pin(reason="OPDL page")
    except discord.HTTPException:
        pass
    return sent


def mention(channel: discord.abc.GuildChannel | None, fallback: str) -> str:
    if channel is None:
        return f"#{fallback}"
    return channel.mention


def color_for(leader: dict) -> int:
    return COLOR_HEX[leader["color"]]


def discord_embed_from_plan(plan: dict, leader: dict) -> discord.Embed:
    embed = discord.Embed(
        title=plan["title"],
        url=plan["url"],
        description=plan["description"][:4096],
        color=color_for(leader),
    )
    embed.set_footer(text=plan["footer"])
    embed.set_thumbnail(url=leader["image"])
    return embed


async def post_info_pages(guild: discord.Guild, channels: dict[str, discord.TextChannel]) -> None:
    welcome = channels.get("welcome")
    rules = channels.get("rules")
    announcements = channels.get("announcements")
    flair = channels.get("flair")
    shop = channels.get("shop-orders")
    general = channels.get("general")
    meta = channels.get("op17-meta")

    if welcome:
        body = WELCOME_BODY.format(
            site=SITE_URL,
            rules=mention(rules, "rules"),
            announcements=mention(announcements, "announcements"),
            flair=mention(flair, "flair"),
            shop=mention(shop, "shop-orders"),
        )
        embed = discord.Embed(title="Welcome", description=body, color=0xB71C1C)
        embed.set_footer(text="OPDL page · welcome")
        await upsert_pinned(welcome, marker="OPDL page · welcome", embeds=[embed])

    if rules:
        body = RULES_BODY.format(
            site=SITE_URL,
            meta=mention(meta, "op17-meta"),
            general=mention(general, "general"),
            shop=mention(shop, "shop-orders"),
        )
        embed = discord.Embed(title="Rules", description=body, color=0xB71C1C)
        embed.set_footer(text="OPDL page · rules")
        await upsert_pinned(rules, marker="OPDL page · rules", embeds=[embed])

    if announcements:
        body = ANNOUNCEMENTS_BODY.format(flair=mention(flair, "flair"))
        embed = discord.Embed(title="Announcements", description=body, color=0xB71C1C)
        embed.add_field(name="Site", value=SITE_URL, inline=True)
        embed.add_field(name="Invite", value=INVITE_URL, inline=True)
        embed.set_footer(text="OPDL page · announcements")
        await upsert_pinned(announcements, marker="OPDL page · announcements", embeds=[embed])

    if flair:
        view = FlairView(guild)
        embed = flair_embed(guild)
        await upsert_pinned(flair, marker="OPDL flair", embeds=[embed], view=view)


async def post_consensus(channel: discord.TextChannel, leader: dict) -> discord.Message:
    cache = load_card_cache()
    consensus = load_consensus()
    plan = format_consensus_embed(leader, cache, consensus)
    embed = discord_embed_from_plan(plan, leader)
    text_list = format_text_list(leader, cache, consensus)
    return await upsert_pinned(
        channel,
        marker=f"{CONSENSUS_FOOTER_PREFIX} {leader['id']}",
        embeds=[embed],
        content=text_list,
    )


async def setup_guild(guild: discord.Guild, *, post_lists: bool = True) -> dict[str, str]:
    """Create the full OPDL layout. Safe to re-run."""
    log: dict[str, str] = {}
    ensure_all_faces()

    channels: dict[str, discord.TextChannel] = {}

    for spec in GENERIC_CATEGORIES:
        category = await ensure_category(guild, spec["name"])
        for ch in spec["channels"]:
            news = ch.get("kind") == "news"
            created = await ensure_text_channel(
                guild,
                name=ch["name"],
                category=category,
                topic=ch["topic"],
                readonly=bool(ch.get("readonly")),
                news=news,
            )
            channels[ch["key"]] = created
            log[ch["name"]] = str(created.id)

    for leader in LEADERS:
        await ensure_role(guild, leader)
        emoji = await ensure_leader_emoji(guild, leader)
        log[f"emoji:{emoji_name(leader)}"] = str(emoji.id) if emoji else "missing"

    for meta in METAS:
        category = await ensure_category(guild, meta["category"])
        discussion = await ensure_text_channel(
            guild,
            name=meta["discussion"],
            category=category,
            topic=meta["topic"],
            readonly=False,
        )
        channels[meta["discussion"]] = discussion
        log[meta["discussion"]] = str(discussion.id)
        for leader in leaders_for_meta(meta["key"]):
            topic = (
                f"{leader['name']} · {leader['id']} · consensus pinned · {site_url(leader)}"
            )
            created = await ensure_text_channel(
                guild,
                name=channel_name(leader),
                category=category,
                topic=topic,
                readonly=False,
            )
            channels[leader["key"]] = created
            log[leader["key"]] = str(created.id)
            if post_lists:
                await post_consensus(created, leader)

    await post_info_pages(guild, channels)

    state = load_state()
    gs = guild_state(state, guild.id)
    gs["channels"] = {k: str(v.id) for k, v in channels.items()}
    save_state(state)
    log["guild"] = str(guild.id)
    return log
