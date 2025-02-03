import discord
import aiohttp
import asyncio
import os
from dotenv import load_dotenv
from colorama import init, Fore, Style
from datetime import datetime
from zoneinfo import ZoneInfo  # Para sa Philippine time (Python 3.9+)
from keep_alive import keep_alive  # Import keep_alive function

# Initialize colorama para sa colored logs
init(autoreset=True)

# Load environment variables mula sa .env o Replit Secrets
load_dotenv()

# Environment variables
API_URL = os.getenv("API_URL")
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHANNEL_ID = int(os.getenv("CHANNEL_ID"))  # Siguraduhing integer

# Discord intents setup
intents = discord.Intents.default()

# ======= LOGGING FUNCTIONS =======
def log_info(message):
    print(f"{Fore.CYAN}[INFO]{Style.RESET_ALL} {message}")

def log_success(message):
    print(f"{Fore.GREEN}[SUCCESS]{Style.RESET_ALL} {message}")

def log_warning(message):
    print(f"{Fore.YELLOW}[WARNING]{Style.RESET_ALL} {message}")

def log_error(message):
    print(f"{Fore.RED}[ERROR]{Style.RESET_ALL} {message}")

def log_api(message):
    print(f"{Fore.MAGENTA}[API]{Style.RESET_ALL} {message}")

def log_connection(message):
    print(f"{Fore.BLUE}[CONNECTION]{Style.RESET_ALL} {message}")

# Listahan ng kulay na gagamitin para sa embed (magbabago-bago ang kulay)
EMBED_COLORS = [
    discord.Color.blue(),
    discord.Color.green(),
    discord.Color.red(),
    discord.Color.orange(),
    discord.Color.purple()
]

# ======= DISCORD CLIENT CLASS =======
class MyClient(discord.Client):
    async def setup_hook(self):
        # I-schedule ang pag-update ng API data
        self.loop.create_task(self.send_api_updates())

    async def fetch_api_data(self):
        """Asynchronous API request gamit ang aiohttp."""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(API_URL) as response:
                    if response.status == 200:
                        log_api("Fetched API data successfully.")
                        return await response.json()
                    else:
                        log_warning(f"API request failed. Status Code: {response.status}")
        except Exception as e:
            log_error(f"Error fetching API data: {e}")
        return None

    async def send_api_updates(self):
        """Auto-update API data bawat 10 seconds (isang message lang ang ia-update)."""
        await self.wait_until_ready()
        channel = self.get_channel(CHANNEL_ID)

        if channel is None:
            log_error("Channel not found. Check CHANNEL_ID at bot permissions.")
            return

        log_info(f"Starting API updates in channel: {channel.name}")

        message = None  # Placeholder para sa iisang message na ia-update
        update_count = 0  # Gamit para baguhin ang embed color

        while not self.is_closed():
            data = await self.fetch_api_data()
            if data:
                # Kunin ang Philippine time gamit ang zoneinfo (Asia/Manila)
                ph_time = datetime.now(ZoneInfo("Asia/Manila"))
                timestamp_24 = ph_time.strftime("%Y-%m-%d %H:%M:%S")
                timestamp_12 = ph_time.strftime("%Y-%m-%d %I:%M:%S %p")

                # Pumili ng kulay batay sa update_count (magbabago-bago)
                embed_color = EMBED_COLORS[update_count % len(EMBED_COLORS)]
                update_count += 1

                # Create Embed Message gamit ang dynamic color
                embed = discord.Embed(
                    title="📊 Server Stats",
                    description="Real-time server statistics with auto-updates.",
                    color=embed_color
                )
                # "Players Online" na nasa taas para madaling makita
                embed.add_field(name="👥 Players Online", value=data.get('online', 'N/A'), inline=False)
                embed.add_field(name="🏆 Best Player", value=data.get('best_player', 'N/A'), inline=True)
                embed.add_field(name="🌍 Best World", value=data.get('best_world', 'N/A'), inline=True)
                embed.add_field(name="💎 Gems Collected", value=data.get('gems', 'N/A'), inline=True)
                embed.add_field(name="✨ XP Collected", value=data.get('xp', 'N/A'), inline=True)
                embed.add_field(name="🗒️ Crazy Jim's Task", value=data.get('crazy_jim', 'N/A'), inline=True)
                embed.add_field(name="📢 Latest Broadcast", value=data.get('broadcast', 'N/A'), inline=True)
                # Ipakita ang parehong 24H at 12H format
                embed.set_footer(text=f"Last Updated: {timestamp_24} (24H) / {timestamp_12} (12H) (PH Time)")

                try:
                    if message:
                        await message.edit(embed=embed)  # I-edit ang existing message
                        log_success(f"Updated stats in #{channel.name} at {timestamp_24}")
                    else:
                        message = await channel.send(embed=embed)  # I-send ang initial message
                        log_success(f"Sent initial stats to #{channel.name}")
                except Exception as e:
                    log_error(f"Failed to send/update message: {e}")
            else:
                log_warning("No data received from API.")

            await asyncio.sleep(10)  # Update every 10 seconds

# ======= EVENT HANDLERS =======
client = MyClient(intents=intents)

@client.event
async def on_ready():
    # Kapag naka-connect na, i-set ang presence
    await client.change_presence(
        activity=discord.Activity(
            type=discord.ActivityType.listening,
            name="GTPH Server Statistics"
        )
    )
    log_connection(f"Bot connected as {client.user} (ID: {client.user.id})")
    log_info("Bot is now running and fetching API data!")

@client.event
async def on_disconnect():
    log_warning("Bot disconnected from Discord!")

@client.event
async def on_resumed():
    log_connection("Bot successfully reconnected to Discord.")

@client.event
async def on_error(event, *args, **kwargs):
    log_error(f"An error occurred in event: {event}")

# ======= MAIN =======
if __name__ == '__main__':
    try:
        log_info("Starting the bot...")
        keep_alive()  # Start ang keep-alive server gamit ang Waitress (production-ready)
        client.run(BOT_TOKEN)
    except Exception as e:
        log_error(f"Critical error: {e}")
