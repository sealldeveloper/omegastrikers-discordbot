import discord
import os
import random
import asyncio
import re
from typing import Dict, Set, List
from dotenv import load_dotenv

load_dotenv()
GUILD_ID = int(os.getenv('GUILD_ID'))

CHARACTERS = {
    "Ai.Mi": "https://omegastrikers.wiki.gg/images/c/c4/Ai.Mi_splash.png",
    "Asher": "https://omegastrikers.wiki.gg/images/f/f0/Asher_splash.png",
    "Atlas": "https://omegastrikers.wiki.gg/images/1/14/Atlas_splash.png",
    "Drek'ar": "https://omegastrikers.wiki.gg/images/9/9d/Drek%27ar_splash.png",
    "Dubu": "https://omegastrikers.wiki.gg/images/2/28/Dubu_splash.png",
    "Era": "https://omegastrikers.wiki.gg/images/b/ba/Era_splash.png",
    "Estelle": "https://omegastrikers.wiki.gg/images/c/c6/Estelle_splash.png",
    "Finii": "https://omegastrikers.wiki.gg/images/5/53/Finii_splash.png",
    "Juliette": "https://omegastrikers.wiki.gg/images/e/e4/Juliette_splash.png",
    "Juno": "https://omegastrikers.wiki.gg/images/6/6e/Juno_splash.png",
    "Kai": "https://omegastrikers.wiki.gg/images/5/51/Kai_splash.png",
    "Kazan": "https://omegastrikers.wiki.gg/images/2/23/Kazan_splash.png",
    "Luna": "https://omegastrikers.wiki.gg/images/3/3b/Luna_splash.png",
    "Mako": "https://omegastrikers.wiki.gg/images/1/1f/Mako_splash.png",
    "Nao": "https://omegastrikers.wiki.gg/images/1/11/Nao_Splash.png",
    "Octavia": "https://omegastrikers.wiki.gg/images/c/c1/Octavia_splash.png",
    "Rasmus": "https://omegastrikers.wiki.gg/images/4/49/Rasmus_splash.png",
    "Rune": "https://omegastrikers.wiki.gg/images/0/09/Rune_splash.png",
    "Vyce": "https://omegastrikers.wiki.gg/images/3/30/Vyce_splash.png",
    "X": "https://omegastrikers.wiki.gg/images/c/cc/X_splash.png",
    "Zentaro": "https://omegastrikers.wiki.gg/images/8/81/Zentaro_splash.png"
}

MAPS = {
    "Ai.Mi's App": "https://liquipedia.net/commons/images/thumb/1/1f/Omega_Strikers_Map_AiMi_App.jpg/340px-Omega_Strikers_Map_AiMi_App.jpg",
    "Atlas's Lab": "https://liquipedia.net/commons/images/thumb/0/05/Omega_Strikers_Map_Atlas_Lab.jpg/339px-Omega_Strikers_Map_Atlas_Lab.jpg",
    "Gates of Obscura": "https://liquipedia.net/commons/images/thumb/a/a3/Omega_Strikers_Map_Gates_of_Obscura_reworked.jpg/320px-Omega_Strikers_Map_Gates_of_Obscura_reworked.jpg",
    "Inky's Splash Zone": "https://liquipedia.net/commons/images/thumb/e/e2/Omega_Strikers_Map_Inky%27s_Splash_Zone.jpg/315px-Omega_Strikers_Map_Inky%27s_Splash_Zone.jpg",
    "Night Market": "https://liquipedia.net/commons/images/thumb/f/f4/Omega_Strikers_Map_Night_Market.jpg/339px-Omega_Strikers_Map_Night_Market.jpg",
    "Taiko Temple": "https://liquipedia.net/commons/images/thumb/1/15/Omega_Strikers_Map_Taiko_Temple.jpg/320px-Omega_Strikers_Map_Taiko_Temple.jpg",
    "Ahten City": "https://liquipedia.net/commons/images/thumb/d/de/Omega_Strikers_Map_Ahten_City.jpg/339px-Omega_Strikers_Map_Ahten_City.jpg",
    "Clarion Test Chamber": "https://liquipedia.net/commons/images/thumb/c/c4/Omega_Strikers_Map_Clarion_Test_Chamber.jpg/600px-Omega_Strikers_Map_Clarion_Test_Chamber.jpg",
    "Demon Dais": "https://liquipedia.net/commons/images/thumb/e/eb/Omega_Strikers_Map_Demon_Dais.jpg/600px-Omega_Strikers_Map_Demon_Dais.jpg",
    "Oni Village": "https://liquipedia.net/commons/images/thumb/b/b2/Omega_Strikers_Map_Oni_Village.jpg/600px-Omega_Strikers_Map_Oni_Village.jpg"
}

# Global dictionary to track active drafts per channel
active_drafts: Dict[int, Set[str]] = {}

# Global dictionary to track draft start messages for editing
draft_messages: Dict[int, discord.Message] = {}

# Global dictionary to track banned characters per channel
banned_characters: Dict[int, Set[str]] = {}

# Global dictionary to store detected codes by channel (current and historical)
detected_codes: Dict[int, List[str]] = {}

# Global dictionary to track channels waiting for next NeatQueue message after "Teams Finalized"
awaiting_team_data: Set[int] = set()

# Global dictionary to store team data by channel
team_data: Dict[int, str] = {}


class Bot(discord.Client):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        super().__init__(intents=intents)
        self.tree = discord.app_commands.CommandTree(self)
        self.synced = False

bot = Bot()

async def striker_autocomplete(
    interaction: discord.Interaction,
    current: str,
) -> list[discord.app_commands.Choice[str]]:
    # Filter strikers based on current input
    matching_strikers = [
        striker for striker in CHARACTERS.keys()
        if current.lower() in striker.lower()
    ]
    # Return up to 25 choices (Discord limit)
    return [
        discord.app_commands.Choice(name=striker, value=striker)
        for striker in matching_strikers[:25]
    ]

async def banned_striker_autocomplete(
    interaction: discord.Interaction,
    current: str,
) -> list[discord.app_commands.Choice[str]]:
    # Get banned strikers for this channel
    channel_id = interaction.channel.id
    channel_banned = banned_characters.get(channel_id, set())
    
    # Filter banned strikers based on current input
    matching_strikers = [
        striker for striker in channel_banned
        if current.lower() in striker.lower()
    ]
    # Return up to 25 choices (Discord limit)
    return [
        discord.app_commands.Choice(name=striker, value=striker)
        for striker in matching_strikers[:25]
    ]

async def auto_end_draft(channel_id: int, delay: int = 600):
    await asyncio.sleep(delay)
    
    if channel_id in active_drafts:
        drafted_count = len(active_drafts[channel_id])
        del active_drafts[channel_id]
        
        # Clean up banned characters for this channel
        if channel_id in banned_characters:
            del banned_characters[channel_id]
        
        # Edit the original message if it exists
        if channel_id in draft_messages:
            original_message = draft_messages[channel_id]
            del draft_messages[channel_id]
            
            embed = discord.Embed(
                title="⏰ Draft Auto-Ended!",
                description=f"Draft session automatically ended after {delay // 60} minutes. {drafted_count} strikers were drafted.",
                color=0xff8c00
            )
            embed.add_field(name="Status", value="Ready for a new draft session", inline=False)
            embed.set_footer(text="Made by seall.dev", icon_url="https://seall.dev/logo.png")
            
            try:
                await original_message.edit(embed=embed)
            except discord.NotFound:
                # If message was deleted, send a new one
                channel = bot.get_channel(channel_id)
                if channel:
                    await channel.send(embed=embed)

@bot.event
async def on_ready():
    print(f'{bot.user} has connected to Discord!')
    print(f'Attempting to sync commands to guild {GUILD_ID}')
    if not bot.synced:
        try:
            synced = await bot.tree.sync(guild=discord.Object(id=GUILD_ID))
            print(f'Synced {len(synced)} command(s) to guild {GUILD_ID}')
            bot.synced = True
        except Exception as e:
            print(f'Failed to sync commands: {e}')
            import traceback
            traceback.print_exc()
    print('Bot is ready!')

@bot.event
async def on_message(message):
    if message.author == bot.user:
        return
    
    # Check for NeatQueue messages (ID: 857633321064595466)
    if message.author.id == 857633321064595466:
        channel_id = message.channel.id
        
        # Check if this is the "Teams Finalized" embed
        if message.embeds:
            for embed in message.embeds:
                if embed.title and "Teams Finalized" in embed.title:
                    awaiting_team_data.add(channel_id)
                    return
        
        # If we're waiting for team data from NeatQueue and this message has content or embeds
        if channel_id in awaiting_team_data:
            if message.content:
                team_data[channel_id] = message.content
            elif message.embeds:
                # Store embed content
                embed_content = ""
                for embed in message.embeds:
                    if embed.title:
                        embed_content += f"**{embed.title}**\n"
                    if embed.description:
                        embed_content += f"{embed.description}\n"
                    for field in embed.fields:
                        embed_content += f"**{field.name}**\n{field.value}\n"
                team_data[channel_id] = embed_content
            
            awaiting_team_data.remove(channel_id)
            return
    
    # Existing code detection logic
    if message.channel.name and message.channel.name.startswith('queue'):
        pattern = r'^[A-Z][a-z]*[A-Z][a-z]*[A-Z][a-z]*$'
        
        if re.match(pattern, message.content.strip()):
            new_code = message.content.strip()
            channel_id = message.channel.id
            
            # Initialize list if channel not seen before
            if channel_id not in detected_codes:
                detected_codes[channel_id] = []
            
            # Add new code if it's not already in the list (deduplication)
            if new_code not in detected_codes[channel_id]:
                detected_codes[channel_id].append(new_code)
            else:
                # Move existing code to end (make it current)
                detected_codes[channel_id].remove(new_code)
                detected_codes[channel_id].append(new_code)

@bot.tree.command(name='startdraft', description='Start a random draft in this channel', guild=discord.Object(id=GUILD_ID))
async def startdraft(interaction: discord.Interaction):
    channel_id = interaction.channel.id
    
    if channel_id in active_drafts:
        await interaction.response.send_message('❌ A draft is already active in this channel! Use /enddraft to end it first.', ephemeral=True)
        return
    
    active_drafts[channel_id] = set()
    
    embed = discord.Embed(
        title="🎲 Draft Started!",
        description="Use `/roll` to select random strikers. No duplicates allowed!\n⏰ Draft will auto-end in 10 minutes.",
        color=0x00ff00
    )
    channel_banned = banned_characters.get(channel_id, set())
    available_count = len(CHARACTERS) - len(channel_banned)
    embed.add_field(name="Available Strikers", value=f"{available_count}/{len(CHARACTERS)} strikers ready to draft", inline=False)
    if channel_banned:
        banned_list = ', '.join(sorted(channel_banned))
        embed.add_field(name="Banned Strikers", value=banned_list, inline=False)
    embed.set_footer(text="Made by seall.dev", icon_url="https://seall.dev/logo.png")
    
    await interaction.response.send_message(embed=embed)
    
    # Store the message for later editing
    message = await interaction.original_response()
    draft_messages[channel_id] = message
    
    # Start the auto-end timer
    asyncio.create_task(auto_end_draft(channel_id, 600))

@bot.tree.command(name='roll', description='Roll for a random striker (no duplicates)', guild=discord.Object(id=GUILD_ID))
async def roll(interaction: discord.Interaction):
    channel_id = interaction.channel.id
    
    if channel_id not in active_drafts:
        await interaction.response.send_message('❌ No active draft in this channel! Use /startdraft to begin.', ephemeral=True)
        return
    
    used_strikers = active_drafts[channel_id]
    channel_banned = banned_characters.get(channel_id, set())
    available_strikers = [name for name in CHARACTERS.keys() if name not in used_strikers and name not in channel_banned]
    
    if not available_strikers:
        await interaction.response.send_message('🎉 All strikers have been drafted! Use /enddraft to reset.', ephemeral=True)
        return
    
    # Defer the response to prevent timeout
    await interaction.response.defer()
    
    selected_striker = random.choice(available_strikers)
    used_strikers.add(selected_striker)
    
    image_url = CHARACTERS[selected_striker]
    
    embed = discord.Embed(
        title=f"🎲 {selected_striker} Drafted!",
        color=0x00ff00
    )
    embed.add_field(
        name="Remaining Strikers", 
        value=f"{len(available_strikers) - 1}/{len(CHARACTERS)}", 
        inline=False
    )
    embed.set_thumbnail(url=image_url)
    embed.set_footer(text="Made by seall.dev", icon_url="https://seall.dev/logo.png")
    
    await interaction.followup.send(embed=embed)

@bot.tree.command(name='enddraft', description='End the current draft and reset striker list', guild=discord.Object(id=GUILD_ID))
async def enddraft(interaction: discord.Interaction):
    channel_id = interaction.channel.id
    
    if channel_id not in active_drafts:
        await interaction.response.send_message('❌ No active draft in this channel!', ephemeral=True)
        return
    
    drafted_count = len(active_drafts[channel_id])
    del active_drafts[channel_id]
    
    # Clean up the stored message reference
    if channel_id in draft_messages:
        del draft_messages[channel_id]
    
    # Clean up banned characters for this channel
    if channel_id in banned_characters:
        del banned_characters[channel_id]
    
    embed = discord.Embed(
        title="🏁 Draft Ended!",
        description=f"Draft session completed. {drafted_count} strikers were drafted.",
        color=0xff0000
    )
    embed.add_field(name="Status", value="Ready for a new draft session", inline=False)
    embed.set_footer(text="Made by seall.dev", icon_url="https://seall.dev/logo.png")
    
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name='ban', description='Ban a striker from the current draft', guild=discord.Object(id=GUILD_ID))
@discord.app_commands.autocomplete(striker=striker_autocomplete)
async def ban(interaction: discord.Interaction, striker: str):
    channel_id = interaction.channel.id
    
    # Check if there's an active draft
    if channel_id not in active_drafts:
        await interaction.response.send_message('❌ No active draft in this channel! Use /startdraft to begin.', ephemeral=True)
        return
    
    # Check if the striker exists in the character list
    matching_strikers = [name for name in CHARACTERS.keys() if name.lower() == striker.lower()]
    
    if not matching_strikers:
        available_names = ', '.join(CHARACTERS.keys())
        embed = discord.Embed(
            title="❌ Striker Not Found",
            description=f"'{striker}' is not a valid striker name.",
            color=0xff0000
        )
        embed.add_field(name="Available Strikers", value=available_names, inline=False)
        embed.set_footer(text="Made by seall.dev", icon_url="https://seall.dev/logo.png")
        await interaction.response.send_message(embed=embed, ephemeral=True)
        return
    
    striker_name = matching_strikers[0]
    
    # Initialize banned list for this channel if it doesn't exist
    if channel_id not in banned_characters:
        banned_characters[channel_id] = set()
    
    if striker_name in banned_characters[channel_id]:
        await interaction.response.send_message(f'❌ {striker_name} is already banned in this draft!', ephemeral=True)
        return
    
    banned_characters[channel_id].add(striker_name)
    
    embed = discord.Embed(
        title="🚫 Striker Banned",
        description=f"{striker_name} has been banned from this draft.",
        color=0xff4500
    )
    embed.add_field(
        name="Banned Strikers", 
        value=f"{len(banned_characters[channel_id])} striker(s) currently banned in this draft", 
        inline=False
    )
    embed.set_thumbnail(url=CHARACTERS[striker_name])
    embed.set_footer(text="Made by seall.dev", icon_url="https://seall.dev/logo.png")
    
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name='unban', description='Unban a striker from the current draft', guild=discord.Object(id=GUILD_ID))
@discord.app_commands.autocomplete(striker=banned_striker_autocomplete)
async def unban(interaction: discord.Interaction, striker: str):
    channel_id = interaction.channel.id
    
    # Check if there's an active draft
    if channel_id not in active_drafts:
        await interaction.response.send_message('❌ No active draft in this channel! Use /startdraft to begin.', ephemeral=True)
        return
    
    # Check if the striker exists in the character list
    matching_strikers = [name for name in CHARACTERS.keys() if name.lower() == striker.lower()]
    
    if not matching_strikers:
        available_names = ', '.join(CHARACTERS.keys())
        embed = discord.Embed(
            title="❌ Striker Not Found",
            description=f"'{striker}' is not a valid striker name.",
            color=0xff0000
        )
        embed.add_field(name="Available Strikers", value=available_names, inline=False)
        embed.set_footer(text="Made by seall.dev", icon_url="https://seall.dev/logo.png")
        await interaction.response.send_message(embed=embed, ephemeral=True)
        return
    
    striker_name = matching_strikers[0]
    
    # Check if there are any banned characters for this channel
    if channel_id not in banned_characters or striker_name not in banned_characters[channel_id]:
        await interaction.response.send_message(f'❌ {striker_name} is not currently banned in this draft!', ephemeral=True)
        return
    
    banned_characters[channel_id].remove(striker_name)
    
    embed = discord.Embed(
        title="✅ Striker Unbanned",
        description=f"{striker_name} has been unbanned and is now available in this draft.",
        color=0x00ff00
    )
    embed.add_field(
        name="Banned Strikers", 
        value=f"{len(banned_characters[channel_id])} striker(s) currently banned in this draft", 
        inline=False
    )
    embed.set_thumbnail(url=CHARACTERS[striker_name])
    embed.set_footer(text="Made by seall.dev", icon_url="https://seall.dev/logo.png")
    
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name='draftless-roll', description='Roll a random striker without needing an active draft', guild=discord.Object(id=GUILD_ID))
async def draftless_roll(interaction: discord.Interaction):
    # Draftless roll uses all characters - no bans apply since there's no draft
    available_strikers = list(CHARACTERS.keys())
    
    # Defer the response to prevent timeout
    await interaction.response.defer()
    
    selected_striker = random.choice(available_strikers)
    image_url = CHARACTERS[selected_striker]
    
    embed = discord.Embed(
        title=f"🎲 {selected_striker} Rolled!",
        description="One-off roll (no draft required)",
        color=0x00ff00
    )
    embed.add_field(
        name="Available Pool", 
        value=f"{len(available_strikers)} strikers available", 
        inline=False
    )
    embed.set_thumbnail(url=image_url)
    embed.set_footer(text="Made by seall.dev", icon_url="https://seall.dev/logo.png")
    
    await interaction.followup.send(embed=embed)

@bot.tree.command(name='randommap', description='Get a random Omega Strikers map', guild=discord.Object(id=GUILD_ID))
async def randommap(interaction: discord.Interaction):
    # Get all available maps
    available_maps = list(MAPS.keys())
    
    # Defer the response to prevent timeout
    await interaction.response.defer()
    
    selected_map = random.choice(available_maps)
    image_url = MAPS[selected_map]
    
    embed = discord.Embed(
        title=f"🗺️ {selected_map}",
        description="Random map selected!",
        color=0x00bfff
    )
    embed.add_field(
        name="Available Maps", 
        value=f"{len(available_maps)} maps in rotation", 
        inline=False
    )
    embed.set_image(url=image_url)
    embed.set_footer(text="Made by seall.dev", icon_url="https://seall.dev/logo.png")
    
    await interaction.followup.send(embed=embed)

@bot.tree.command(name='code', description='Get the detected code from this channel', guild=discord.Object(id=GUILD_ID))
async def code(interaction: discord.Interaction):
    channel_id = interaction.channel.id
    
    if channel_id not in detected_codes or not detected_codes[channel_id]:
        await interaction.response.send_message('❌ No code detected in this channel yet.', ephemeral=True)
        return
    
    codes_list = detected_codes[channel_id]
    current_code = codes_list[-1]  # Last item is the current code
    
    embed = discord.Embed(
        title="🔑 Current Code",
        description=f"```\n{current_code}\n```",
        color=0x00ff00
    )
    
    # Add previous codes if any exist
    if len(codes_list) > 1:
        previous_codes = codes_list[:-1]  # All except the last one
        previous_codes_text = '\n'.join([f"• `{code}`" for code in previous_codes])
        embed.add_field(
            name="📝 Previous Codes",
            value=previous_codes_text,
            inline=False
        )
    
    # Add warning about false positives
    embed.add_field(
        name="⚠️ Note",
        value="Auto-detected codes may include false positives.",
        inline=False
    )
    
    embed.set_footer(text="Made by seall.dev", icon_url="https://seall.dev/logo.png")
    
    await interaction.response.send_message(embed=embed, ephemeral=True)

@bot.tree.command(name='teams', description='Get the latest team data from NeatQueue', guild=discord.Object(id=GUILD_ID))
async def teams(interaction: discord.Interaction):
    channel_id = interaction.channel.id
    
    if channel_id not in team_data:
        await interaction.response.send_message('❌ No team data available in this channel yet.', ephemeral=True)
        return
    
    teams_content = team_data[channel_id]
    
    embed = discord.Embed(
        title="👥 Team Data",
        description=teams_content,
        color=0x0099ff
    )
    embed.set_footer(text="Made by seall.dev", icon_url="https://seall.dev/logo.png")
    
    await interaction.response.send_message(embed=embed, ephemeral=True)

def main():
    load_dotenv()
    token = os.getenv('DISCORD_BOT_TOKEN')
    if not token:
        print('Error: DISCORD_BOT_TOKEN environment variable not set')
        return
    bot.run(token)

if __name__ == "__main__":
    main()
