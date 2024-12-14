# By alternating
import discord
from discord.ext import tasks, commands
import requests
import asyncio
import os
from datetime import datetime, timedelta
from playwright.async_api import async_playwright
import time

class PriceBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        super().__init__(command_prefix='!', intents=intents)
        
        self.token = 'MTMxNzMwMjAwOTYwMjM3NTc1Mw.GBZK2G.397HncPXupiMUW_zw1saiIEA6ewntiVx5qaz8Y'  # Replace with your bot token
        self.token_api_url = 'https://api.dexscreener.com/latest/dex/tokens/8i51XNNpGaKaj4G4nDdmQh95v4FKAxw8mhtaRoKd9tE8'
        self.sol_api_url = 'https://api.dexscreener.com/latest/dex/pairs/osmosis/1960'
        self.tetsuo_address = '8i51XNNpGaKaj4G4nDdmQh95v4FKAxw8mhtaRoKd9tE8'
        self.last_price_command = {}  # Store last command usage per channel
        self.last_sol_command = {}    # Store last SOL command usage per channel
        self.last_chart_command = {}  # Store last chart command usage per channel
        self.price_cooldown = 300     # Cooldown in seconds
        self.chart_cooldown = 300     # Chart command cooldown

    async def setup_hook(self):
        self.update_price.start()
        await self.add_cog(PriceCommands(self))

    async def on_ready(self):
        print(f'Logged in as {self.user.name} ({self.user.id})')
        print('------')

    def get_price_data(self, url):
        """Fetch price, 24h change, and market cap from API"""
        try:
            response = requests.get(url)
            data = response.json()
            
            if url == self.token_api_url:
                if data and 'pairs' in data and len(data['pairs']) > 0:
                    pair = data['pairs'][0]
                    return {
                        'price': float(pair['priceUsd']),
                        'price_change': float(pair['priceChange']['h24']) if 'priceChange' in pair else 0,
                        'market_cap': float(pair['fdv']) if 'fdv' in pair else None
                    }
            else:  # SOL price
                if data and 'pair' in data:
                    pair = data['pair']
                    return {
                        'price': float(pair['priceUsd']),
                        'price_change': float(pair['priceChange']['h24']) if 'priceChange' in pair else 0,
                        'market_cap': float(pair['fdv']) if 'fdv' in pair else None
                    }
            return None
        except Exception as e:
            print(f'Error fetching price: {str(e)}')
            return None

    def format_market_cap(self, market_cap):
        """Format market cap to readable format with appropriate suffix"""
        if market_cap is None:
            return "N/A"
        
        if market_cap >= 1_000_000_000:  # Billions
            return f"${market_cap/1_000_000_000:.2f}B"
        elif market_cap >= 1_000_000:  # Millions
            return f"${market_cap/1_000_000:.2f}M"
        else:  # Thousands
            return f"${market_cap/1_000:.2f}K"

    def format_price_display(self, price, price_change, market_cap):
        """Format price display with arrow, 24hr change, and market cap"""
        arrow = "?" if price_change >= 0 else "?"
        formatted_mcap = self.format_market_cap(market_cap)
        return f"{arrow} ${price:.4f}\n24hr| {price_change:+.2f}%\nMCAP| {formatted_mcap}"

    async def update_bot_status(self, price_change):
        """Update bot's status based on 24h price change"""
        try:
            # Set status based on price change
            status = discord.Status.online if price_change >= 0 else discord.Status.dnd
            
            # Create activity with just the percentage
            activity_text = f"24hr| {price_change:+.2f}%"
            activity = discord.CustomActivity(name=activity_text)
            
            # Update bot's presence
            await self.change_presence(status=status, activity=activity)
            print(f"Updated status to {status} with message: {activity_text}")
        except Exception as e:
            print(f"Error updating status: {str(e)}")

    @tasks.loop(seconds=300)
    async def update_price(self):
        try:
            price_data = self.get_price_data(self.token_api_url)
            if price_data is not None:
                price = price_data['price']
                price_change = price_data['price_change']
                
                # Format nickname with arrow
                arrow = "↗" if price_change >= 0 else "↘"
                new_name = f"{arrow} ${price:.4f}"
                
                # Update bot's nickname in all guilds
                for guild in self.guilds:
                    try:
                        await guild.me.edit(nick=new_name)
                        print(f'Updated price to {new_name}')
                    except discord.errors.Forbidden:
                        print(f'Missing permissions to change nickname in {guild.name}')
                
                # Update bot's status
                await self.update_bot_status(price_change)
            else:
                print('Failed to fetch price data')
                
        except Exception as e:
            print(f'Error updating price: {str(e)}')

    @update_price.before_loop
    async def before_update_price(self):
        await self.wait_until_ready()

class PriceCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def check_cooldown(self, ctx, command_type='price'):
        current_time = datetime.now()
        channel_id = ctx.channel.id
        
        command_dict = {
            'price': self.bot.last_price_command,
            'sol': self.bot.last_sol_command,
            'chart': self.bot.last_chart_command
        }.get(command_type)
        
        if channel_id in command_dict:
            time_diff = (current_time - command_dict[channel_id]).total_seconds()
            cooldown = self.bot.chart_cooldown if command_type == 'chart' else self.bot.price_cooldown
            if time_diff < cooldown:
                remaining_time = int(cooldown - time_diff)
                await ctx.send(f'⏳ This command is on cooldown. Please wait {remaining_time} seconds before trying again.')
                return False
        return True

    async def capture_dexscreener_chart(self, token_address):
        """Captures a screenshot of a DexScreener chart using headless browser mode."""
        async with async_playwright() as p:
            browser = await p.chromium.launch(
                headless=True,
                args=[
                    '--disable-gpu',
                    '--no-sandbox',
                    '--disable-dev-shm-usage',
                    '--disable-setuid-sandbox',
                    '--no-first-run',
                    '--no-zygote',
                    '--deterministic-fetch',
                    '--disable-features=IsolateOrigins',
                    '--disable-site-isolation-trials'
                ]
            )
            
            context = await browser.new_context(
                viewport={'width': 1280, 'height': 800},
                color_scheme='dark'
            )
            
            page = await context.new_page()
            
            try:
                url = f"https://dexscreener.com/solana/{token_address}"
                
                # Navigate to the page and wait for network to be idle
                await page.goto(url, wait_until='networkidle', timeout=60000)
                
                # Wait for the price information to be visible first
                await page.wait_for_selector('[data-price]', timeout=60000)
                
                # Try multiple possible selectors for the chart
                chart_selectors = [
                    '.tv-lightweight-charts',
                    '#chart-container',
                    '[data-qa="chart"]',
                    '.tradingview-chart',
                    '.chart-container'
                ]
                
                chart_element = None
                for selector in chart_selectors:
                    try:
                        chart_element = await page.wait_for_selector(selector, timeout=5000, state='visible')
                        if chart_element:
                            print(f"Found chart with selector: {selector}")
                            break
                    except Exception:
                        continue
                
                if not chart_element:
                    raise Exception("Could not find chart element with any known selector")
                
                # Wait for chart data to load
                await asyncio.sleep(5)
                
                # Try to find and click the 1h button
                timeframe_selectors = [
                    'button:has-text("1h")',
                    '[data-qa="time-resolution-button"]:has-text("1h")',
                    'button[data-resolution="60"]',
                    'button.resolution-button:has-text("1h")'
                ]
                
                for selector in timeframe_selectors:
                    try:
                        button = await page.wait_for_selector(selector, timeout=5000)
                        if button:
                            await button.click()
                            print(f"Clicked timeframe button with selector: {selector}")
                            break
                    except Exception:
                        continue
                
                # Wait for chart to update
                await asyncio.sleep(3)
                
                # Create screenshots directory
                os.makedirs('screenshots', exist_ok=True)
                
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"screenshots/dexscreener_chart_{timestamp}.png"
                
                # Take a screenshot of the entire page first
                await page.screenshot(path=filename)
                
                # Get the chart dimensions for cropping
                chart_box = await chart_element.bounding_box()
                if chart_box:
                    # Add some padding
                    chart_box['x'] = max(0, chart_box['x'] - 10)
                    chart_box['y'] = max(0, chart_box['y'] - 10)
                    chart_box['width'] += 20
                    chart_box['height'] += 20
                    
                    # Take a new screenshot of just the chart area
                    await page.screenshot(
                        path=filename,
                        clip=chart_box
                    )
                
                return filename
                
            except Exception as e:
                print(f"Detailed error during screenshot capture: {str(e)}")
                raise
                
            finally:
                await context.close()
                await browser.close()

    @commands.command(name='chart')
    async def chart_command(self, ctx, token_type: str = None):
        """Command to fetch and display chart for tetsuo or sol"""
        if not token_type:
            await ctx.send("❌ Please specify either 'tetsuo' or 'sol' after the command.")
            return
            
        if not await self.check_cooldown(ctx, 'chart'):
            return
            
        token_type = token_type.lower()
        if token_type not in ['tetsuo', 'sol']:
            await ctx.send("❌ Invalid token type. Please use either 'tetsuo' or 'sol'.")
            return
            
        async with ctx.typing():
            try:
                # Send initial message
                status_msg = await ctx.send("📊 Generating chart, please wait...")
                
                # Get token address based on type
                token_address = self.bot.tetsuo_address if token_type == 'tetsuo' else 'sol'
                
                # Capture chart
                screenshot_path = await self.capture_dexscreener_chart(token_address)
                
                # Create embed with chart
                embed = discord.Embed(
                    title=f"{'Tetsuo' if token_type == 'tetsuo' else 'Solana'} Price Chart (1H)",
                    color=0x00ff00,
                    timestamp=datetime.now()
                )
                
                # Add the chart image to the embed
                file = discord.File(screenshot_path, filename="chart.png")
                embed.set_image(url="attachment://chart.png")
                
                # Update cooldown
                self.bot.last_chart_command[ctx.channel.id] = datetime.now()
                
                # Send embed with chart
                await ctx.send(file=file, embed=embed)
                
                # Delete status message and clean up screenshot
                await status_msg.delete()
                os.remove(screenshot_path)
                
            except Exception as e:
                await status_msg.edit(content="❌ Failed to generate chart. Please try again later.")
                print(f"Error generating chart: {str(e)}")


    @commands.command(name='tetsuo')
    async def price_command(self, ctx):
        if not await self.check_cooldown(ctx, 'price'):
            return
        
        price_data = self.bot.get_price_data(self.bot.token_api_url)
        if price_data is not None:
            # Determine arrow and color
            arrow = "↗" if price_data['price_change'] >= 0 else "↘"
            color = 0x00ff00 if price_data['price_change'] >= 0 else 0xff0000
            
            # Format market cap
            market_cap = self.bot.format_market_cap(price_data['market_cap'])
            
            # Create embed
            embed = discord.Embed(
                title="Token Price Information",
                color=color
            )
            
            # Add fields
            embed.add_field(
                name="Current Price",
                value=f"{arrow} ${price_data['price']:.4f}",
                inline=False
            )
            embed.add_field(
                name="24h Change",
                value=f"{price_data['price_change']:+.2f}%",
                inline=True
            )
            embed.add_field(
                name="Market Cap",
                value=market_cap,
                inline=True
            )
            
            # Add footer with update info
            embed.set_footer(text="Price updates every 60 seconds")
            
            await ctx.send(embed=embed)
            self.bot.last_price_command[ctx.channel.id] = datetime.now()
        else:
            await ctx.send("? Unable to fetch price data. Please try again later.")


    @commands.command(name='sol')
    async def sol_price_command(self, ctx):
        if not await self.check_cooldown(ctx, 'sol'):
            return
        
        price_data = self.bot.get_price_data(self.bot.sol_api_url)
        if price_data is not None:
            # Determine arrow and color
            arrow = "?" if price_data['price_change'] >= 0 else "?"
            color = 0x00ff00 if price_data['price_change'] >= 0 else 0xff0000
            
            # Format market cap
            market_cap = self.bot.format_market_cap(price_data['market_cap'])
            
            # Create embed
            embed = discord.Embed(
                title="Solana Price Information",
                color=color
            )
            
            # Add fields
            embed.add_field(
                name="Current Price",
                value=f"{arrow} ${price_data['price']:.4f}",
                inline=False
            )
            embed.add_field(
                name="24h Change",
                value=f"{price_data['price_change']:+.2f}%",
                inline=True
            )
            embed.add_field(
                name="Market Cap",
                value=market_cap,
                inline=True
            )
            
            # Add footer with update info
            embed.set_footer(text="Price updates every 60 seconds")
            
            await ctx.send(embed=embed)
            self.bot.last_sol_command[ctx.channel.id] = datetime.now()
        else:
            await ctx.send("? Unable to fetch SOL price data. Please try again later.")


def main():
    try:
        bot = PriceBot()
        bot.run(bot.token)
    except Exception as e:
        print(f"Error starting bot: {str(e)}")
        print("Please make sure you have:")
        print("1. Updated discord.py using: pip install -U discord.py")
        print("2. Enabled Message Content Intent in Discord Developer Portal")
        print("3. Added your bot token to the code")

if __name__ == "__main__":
    main()
