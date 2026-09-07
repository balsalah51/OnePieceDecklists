"""Persistent favorite-leader flair picker."""

from __future__ import annotations

import discord

from .config import LEADERS, FLAIR_BODY, COLOR_UNICODE, emoji_name, leader_by_key, role_name


FLAIR_PREFIX = "opdl:flair:"
CLEAR_ID = "opdl:flair:clear"


def guild_emoji(guild: discord.Guild | None, leader: dict) -> discord.Emoji | str:
    name = emoji_name(leader)
    if guild is not None:
        found = discord.utils.get(guild.emojis, name=name)
        if found:
            return found
    return COLOR_UNICODE.get(leader["color"], "⭐")


class FlairButton(discord.ui.Button):
    def __init__(self, leader: dict, emoji: discord.Emoji | str, row: int):
        super().__init__(
            custom_id=f"{FLAIR_PREFIX}{leader['key']}",
            label=leader["short"][:80],
            style=discord.ButtonStyle.secondary,
            emoji=emoji,
            row=row,
        )
        self.leader_key = leader["key"]

    async def callback(self, interaction: discord.Interaction) -> None:
        leader = leader_by_key(self.leader_key)
        if leader is None or interaction.guild is None or not isinstance(interaction.user, discord.Member):
            await interaction.response.send_message("Could not assign that flair here.", ephemeral=True)
            return
        await apply_flair(interaction, leader)


class ClearFlairButton(discord.ui.Button):
    def __init__(self, row: int = 4):
        super().__init__(
            custom_id=CLEAR_ID,
            label="Clear flair",
            style=discord.ButtonStyle.danger,
            row=row,
        )

    async def callback(self, interaction: discord.Interaction) -> None:
        if interaction.guild is None or not isinstance(interaction.user, discord.Member):
            await interaction.response.send_message("No guild.", ephemeral=True)
            return
        removed = await strip_leader_roles(interaction.user)
        if removed:
            await interaction.response.send_message("Flair cleared.", ephemeral=True)
        else:
            await interaction.response.send_message("You did not have a leader flair.", ephemeral=True)


class FlairView(discord.ui.View):
    def __init__(self, guild: discord.Guild | None = None):
        super().__init__(timeout=None)
        for i, leader in enumerate(LEADERS):
            self.add_item(FlairButton(leader, guild_emoji(guild, leader), row=i // 5))
        self.add_item(ClearFlairButton(row=min(4, (len(LEADERS) // 5) + (1 if len(LEADERS) % 5 else 0))))


async def strip_leader_roles(member: discord.Member) -> list[discord.Role]:
    wanted = {role_name(L) for L in LEADERS}
    have = [role for role in member.roles if role.name in wanted]
    if have:
        await member.remove_roles(*have, reason="OPDL leader flair")
    return have


async def apply_flair(interaction: discord.Interaction, leader: dict) -> None:
    assert interaction.guild is not None
    member = interaction.user
    assert isinstance(member, discord.Member)
    role = discord.utils.get(interaction.guild.roles, name=role_name(leader))
    if role is None:
        await interaction.response.send_message(
            f"Role `{role_name(leader)}` is missing. An admin needs `/opdl-setup`.",
            ephemeral=True,
        )
        return
    await strip_leader_roles(member)
    await member.add_roles(role, reason="OPDL leader flair")
    emoji = guild_emoji(interaction.guild, leader)
    mention = str(emoji) if not isinstance(emoji, str) else emoji
    await interaction.response.send_message(
        f"{mention} Flair set to **{leader['name']}** (`{leader['id']}`).",
        ephemeral=True,
    )


def flair_embed(guild: discord.Guild | None = None) -> discord.Embed:
    embed = discord.Embed(
        title="Pick your favorite OP leader",
        description=FLAIR_BODY,
        color=0xB71C1C,
    )
    lines = []
    for leader in LEADERS:
        emoji = guild_emoji(guild, leader)
        mark = str(emoji)
        lines.append(f"{mark} **{leader['name']}** · `{leader['id']}`")
    embed.add_field(name="Leaders on the site", value="\n".join(lines), inline=False)
    embed.set_footer(text="OPDL flair · one favorite at a time")
    return embed
