import discord
from discord.ext import commands
from discord import app_commands
import json
import os
import asyncio
from datetime import datetime, timedelta

OWNER_ID = 1345769207588978708
CONFIG_FILE = "config.json"
CASES_FILE = "cases.json"
APPEAL_SERVER = "https://discord.gg/eNSaCCZk9f"

intents = discord.Intents.default()
intents.members = True
intents.message_content = True
intents.guilds = True

bot = commands.Bot(command_prefix="!", intents=intents)

def load_json(file):
    if os.path.exists(file):
        with open(file, "r") as f:
            return json.load(f)
    return {}

def save_json(file, data):
    with open(file, "w") as f:
        json.dump(data, f, indent=2)

def has_mod_role(interaction: discord.Interaction):
    data = load_json(CONFIG_FILE)
    roles = data.get(str(interaction.guild.id), [])
    return any(r.id in roles for r in interaction.user.roles)

def next_case_id(guild_id, user_id):
    data = load_json(CASES_FILE)
    key = f"{guild_id}:{user_id}"
    data[key] = data.get(key, 0) + 1
    save_json(CASES_FILE, data)
    return data[key]

def punishment_embed(punishment, moderator, reason, case_id):
    e = discord.Embed(
        title=f"❗️ You were {punishment}",
        description="You received a punishment from our server staff for breaking the rules.\nPlease review the details below. 👇🏻",
        color=discord.Color.red(),
        timestamp=datetime.utcnow()
    )
    e.add_field(name="➡️ Punishment", value=punishment, inline=False)
    e.add_field(name="➡️ Moderator", value=moderator, inline=False)
    e.add_field(name="➡️ Time", value=f"<t:{int(datetime.utcnow().timestamp())}:F>", inline=False)
    e.add_field(name="➡️ Case ID", value=str(case_id), inline=False)
    e.add_field(name="➡️ Reason", value=reason, inline=False)
    if punishment in ["mute", "ban"]:
        e.add_field(name="APPEAL SERVER", value=APPEAL_SERVER, inline=False)
    return e

@bot.event
async def on_ready():
    await bot.tree.sync()
    print(f"Logged in as {bot.user}")

@bot.tree.command(name="config")
async def config(interaction: discord.Interaction, roles: str):
    if interaction.user.id != OWNER_ID:
        await interaction.response.send_message("Access denied.", ephemeral=True)
        return
    role_ids = [int(r.strip("<@&>")) for r in roles.split()]
    data = load_json(CONFIG_FILE)
    data[str(interaction.guild.id)] = role_ids
    save_json(CONFIG_FILE, data)
    await interaction.response.send_message("Moderation roles configured.", ephemeral=True)

@bot.tree.command(name="warn")
async def warn(interaction: discord.Interaction, member: discord.Member, reason: str):
    if not has_mod_role(interaction):
        return
    case_id = next_case_id(interaction.guild.id, member.id)
    embed = punishment_embed("warned", interaction.user.name, reason, case_id)
    await member.send(embed=embed)
    await interaction.response.send_message(f"{member.mention} warned.")

@bot.tree.command(name="mute")
async def mute(interaction: discord.Interaction, member: discord.Member, minutes: int, reason: str):
    if not has_mod_role(interaction):
        return
    await member.timeout(timedelta(minutes=minutes))
    case_id = next_case_id(interaction.guild.id, member.id)
    embed = punishment_embed("muted", interaction.user.name, reason, case_id)
    await member.send(embed=embed)
    await interaction.response.send_message(f"{member.mention} muted.")

@bot.tree.command(name="unmute")
async def unmute(interaction: discord.Interaction, member: discord.Member):
    if not has_mod_role(interaction):
        return
    await member.timeout(None)
    await interaction.response.send_message(f"{member.mention} unmuted.")

@bot.tree.command(name="ban")
async def ban(interaction: discord.Interaction, member: discord.Member, reason: str):
    if not has_mod_role(interaction):
        return
    case_id = next_case_id(interaction.guild.id, member.id)
    embed = punishment_embed("banned", interaction.user.name, reason, case_id)
    await member.send(embed=embed)
    await member.ban(reason=reason)
    await interaction.response.send_message(f"{member.mention} banned.")

@bot.tree.command(name="unban")
async def unban(interaction: discord.Interaction, user_id: str):
    if not has_mod_role(interaction):
        return
    user = await bot.fetch_user(int(user_id))
    await interaction.guild.unban(user)
    await interaction.response.send_message(f"{user} unbanned.")

@bot.tree.command(name="kick")
async def kick(interaction: discord.Interaction, member: discord.Member, reason: str):
    if not has_mod_role(interaction):
        return
    case_id = next_case_id(interaction.guild.id, member.id)
    embed = punishment_embed("kicked", interaction.user.name, reason, case_id)
    await member.send(embed=embed)
    await member.kick(reason=reason)
    await interaction.response.send_message(f"{member.mention} kicked.")

@bot.tree.command(name="clear")
async def clear(interaction: discord.Interaction, amount: int):
    if not has_mod_role(interaction):
        return
    await interaction.channel.purge(limit=amount)
    await interaction.response.send_message("Messages deleted.", ephemeral=True)

@bot.tree.command(name="lock")
async def lock(interaction: discord.Interaction):
    if not has_mod_role(interaction):
        return
    await interaction.channel.set_permissions(interaction.guild.default_role, send_messages=False)
    await interaction.response.send_message("Channel locked.")

@bot.tree.command(name="unlock")
async def unlock(interaction: discord.Interaction):
    if not has_mod_role(interaction):
        return
    await interaction.channel.set_permissions(interaction.guild.default_role, send_messages=True)
    await interaction.response.send_message("Channel unlocked.")

@bot.tree.command(name="slowmode")
async def slowmode(interaction: discord.Interaction, seconds: int):
    if not has_mod_role(interaction):
        return
    await interaction.channel.edit(slowmode_delay=seconds)
    await interaction.response.send_message("Slowmode updated.")

@bot.tree.command(name="nick")
async def nick(interaction: discord.Interaction, member: discord.Member, nickname: str):
    if not has_mod_role(interaction):
        return
    await member.edit(nick=nickname)
    await interaction.response.send_message("Nickname changed.")

@bot.tree.command(name="role_add")
async def role_add(interaction: discord.Interaction, member: discord.Member, role: discord.Role):
    if not has_mod_role(interaction):
        return
    await member.add_roles(role)
    await interaction.response.send_message("Role added.")

@bot.tree.command(name="role_remove")
async def role_remove(interaction: discord.Interaction, member: discord.Member, role: discord.Role):
    if not has_mod_role(interaction):
        return
    await member.remove_roles(role)
    await interaction.response.send_message("Role removed.")

@bot.tree.command(name="announce")
async def announce(interaction: discord.Interaction, message: str):
    if not has_mod_role(interaction):
        return
    await interaction.channel.send(message)
    await interaction.response.send_message("Announcement sent.", ephemeral=True)

@bot.tree.command(name="poll")
async def poll(interaction: discord.Interaction, question: str):
    if not has_mod_role(interaction):
        return
    msg = await interaction.channel.send(f"📊 **{question}**")
    await msg.add_reaction("👍")
    await msg.add_reaction("👎")
    await interaction.response.send_message("Poll created.", ephemeral=True)

@bot.command(name="manage-servers")
async def manage_servers(ctx):
    if ctx.author.id != OWNER_ID:
        return
    msg = await ctx.send("Verifying bot...")
    await asyncio.sleep(10)
    await msg.edit(content="Bot is now working (estimated: 10)")
    await asyncio.sleep(1)
    await ctx.send("This bot is now verified as an Airplane Instance.")

token = os.getenv("DISCORD_TOKEN")
if not token:
    raise RuntimeError("DISCORD_TOKEN is missing!")

bot.run(token)
