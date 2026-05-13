import discord
from discord.ext import commands, tasks
from datetime import time, timezone

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)

DAILY_ROLE_ID = 1501856394490413106
YOUR_BOT_TOKEN = "YOUR_TOKEN_HERE"


message_counts = {}
previous_winner = {}

@bot.event
async def on_ready():
    print(f"✅ Bot is online as {bot.user}")
    daily_reset.start()

@bot.event
async def on_message(message):
    if message.author.bot:
        return
    if not message.guild:
        return
   
    guild_id = message.guild.id
    user_id = message.author.id
   
    if guild_id not in message_counts:
        message_counts[guild_id] = {}
   
    message_counts[guild_id][user_id] = message_counts[guild_id].get(user_id, 0) + 1

    await bot.process_commands(message) 

@tasks.loop(time=time(hour=0, tzinfo=timezone.utc))  # Runs at midnight UTC
async def daily_reset():
    for guild in bot.guilds:
        await process_daily_winner(guild)

async def process_daily_winner(guild):
    guild_id = guild.id
    if guild_id not in message_counts or not message_counts[guild_id]:
        return
    
    counts = message_counts[guild_id]
    winner_id = max(counts, key=counts.get)
    winner = guild.get_member(winner_id)
    role = guild.get_role(DAILY_ROLE_ID)
    
    if not winner or not role:
        return
    
    # Remove from old winner
    if guild_id in previous_winner:
        old_member = guild.get_member(previous_winner[guild_id])
        if old_member:
            try:
                await old_member.remove_roles(role)
            except:
                pass
    
    # Give to new winner
    try:
        await winner.add_roles(role)
        print(f"🏆 New daily winner in {guild.name}: {winner} ({counts[winner_id]} messages)")
        
        # Optional announcement
        for channel in guild.text_channels:
            if channel.permissions_for(guild.me).send_messages:
                await channel.send(f"🏆 **Daily Message Champion** is **{winner.mention}** with **{counts[winner_id]}** messages!")
                break
    except:
        pass
    
    previous_winner[guild_id] = winner_id
    message_counts[guild_id] = {}   # Reset counter

@bot.command()
async def todaytop(ctx):
    """Shows today's top chatters"""
    guild_id = ctx.guild.id
    if guild_id not in message_counts or not message_counts[guild_id]:
        await ctx.send("No messages recorded yet today!")
        return
    
    sorted_users = sorted(message_counts[guild_id].items(), key=lambda x: x[1], reverse=True)[:5]
    text = "**Today's Top Chatters:**\n"
    for rank, (user_id, count) in enumerate(sorted_users, 1):
        member = ctx.guild.get_member(user_id)
        name = member.display_name if member else "Unknown"
        text += f"{rank}. **{name}** — {count} messages\n"
    await ctx.send(text)

bot.run(YOUR_BOT_TOKEN)
