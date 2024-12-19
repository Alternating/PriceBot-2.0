# By Alternating - test

import discord
from discord.ext import tasks, commands
import requests
import asyncio
import os
from datetime import datetime
import settings
from chart_scraper import capture_chart_async
import yfinance as yf
from dotenv import load_dotenv

class PriceBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        super().__init__(command_prefix='!', intents=intents, help_command=None)  # Disable default help
        
        # Initialize command cooldowns
        self.command_cooldowns = {}
        
        # Add commands
        self.add_commands()
        
    def add_commands(self):
        # Add all commands
        self.add_command(self.tetsuo_price)
        self.add_command(self.sol_price)
        self.add_command(self.chart_command)
        self.add_command(self.help_command)
        self.add_command(self.admin_help)
        self.add_command(self.update_cookie)
        
    async def setup_hook(self):
        self.update_price.start()

    async def on_ready(self):
        print(f'Logged in as {self.user.name} ({self.user.id})')
        print('------')

    @tasks.loop(seconds=settings.PRICE_COOLDOWN)
    async def update_price(self):
        """Update bot's nickname with current price"""
        try:
            # Fetch TETSUO price data
            response = requests.get(settings.TETSUO['dex_api'])
            data = response.json()
            
            if data and 'pairs' in data and len(data['pairs']) > 0:
                pair = data['pairs'][0]
                price = float(pair['priceUsd'])
                price_change = float(pair['priceChange']['h24']) if 'priceChange' in pair else 0
                
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
                
                # Update bot's status based on price change
                status = discord.Status.online if price_change >= 0 else discord.Status.dnd
                activity = discord.CustomActivity(name=f"24hr| {price_change:+.2f}%")
                await self.change_presence(status=status, activity=activity)
                
        except Exception as e:
            print(f'Error updating price: {str(e)}')

    @update_price.before_loop
    async def before_update_price(self):
        await self.wait_until_ready()

    async def check_cooldown(self, ctx, command_type='price'):
        """Check if command is on cooldown"""
        current_time = datetime.now()
        cooldown_key = f"{ctx.channel.id}_{command_type}"
    
        if cooldown_key in self.command_cooldowns:
            time_diff = (current_time - self.command_cooldowns[cooldown_key]).total_seconds()
            # Use different cooldown times for different commands
            cooldown = settings.CHART_COOLDOWN if command_type == 'chart' else settings.PRICE_COOLDOWN
            if time_diff < cooldown:
                remaining = int(cooldown - time_diff)
                await ctx.send(f'⏳ This command is on cooldown. Please wait {remaining} seconds.')
                return False
            
        self.command_cooldowns[cooldown_key] = current_time
        return True

    @commands.command(name='tetsuo')
    async def tetsuo_price(self, ctx):
        """Display current TETSUO price information"""
        if not await self.check_cooldown(ctx, 'tetsuo'):
            return
            
        try:
            response = requests.get(settings.TETSUO['dex_api'])
            data = response.json()
            
            if data and 'pairs' in data and len(data['pairs']) > 0:
                pair = data['pairs'][0]
                price = float(pair['priceUsd'])
                price_change = float(pair['priceChange']['h24']) if 'priceChange' in pair else 0
                market_cap = float(pair['fdv']) if 'fdv' in pair else None
                volume_24h = float(pair['volume']['h24']) if 'volume' in pair and 'h24' in pair['volume'] else None
                
                # Create embed
                color = 0x00ff00 if price_change >= 0 else 0xff0000
                arrow = "↑" if price_change >= 0 else "↓"
                
                embed = discord.Embed(
                    title="TETSUO Price Information",
                    url="https://dexscreener.com/solana/2kb3i5ulkhucjuwq3poxhpuggqbwywttk5eg9e5wnlg6",
                    color=color,
                    timestamp=datetime.now()
                )
                
                # First row: Price and 24h Change
                embed.add_field(
                    name="Current Price",
                    value=f"{arrow} ${price:.4f}",
                    inline=True
                )
                
                embed.add_field(
                    name="24h Change",
                    value=f"{price_change:+.2f}%",
                    inline=True
                )
                
                # Add empty field to force next row
                embed.add_field(name="\u200b", value="\u200b", inline=True)
                
                # Second row: Market Cap and Volume
                if market_cap:
                    market_cap_formatted = f"${market_cap/1_000_000:.2f}M"
                    embed.add_field(
                        name="Market Cap",
                        value=market_cap_formatted,
                        inline=True
                    )
                else:
                    embed.add_field(name="Market Cap", value="N/A", inline=True)

                if volume_24h:
                    volume_formatted = f"${volume_24h:,.0f}"
                    embed.add_field(
                        name="24h Volume",
                        value=volume_formatted,
                        inline=True
                    )
                else:
                    embed.add_field(name="24h Volume", value="N/A", inline=True)
                
                # Add empty field to maintain grid
                embed.add_field(name="\u200b", value="\u200b", inline=True)
                
                await ctx.send(embed=embed)
                
            else:
                await ctx.send("❌ Unable to fetch price data")
                
        except Exception as e:
            print(f"Error in tetsuo_price: {str(e)}")
            await ctx.send("❌ Error fetching price data")
    
    @commands.command(name='sol')
    async def sol_price(self, ctx):
        """Display current SOL price information"""
        if not await self.check_cooldown(ctx, 'sol'):
            return
            
        try:
            # Get SOL data
            sol = yf.Ticker("SOL-USD")
            info = sol.info
            
            # Use the correct field names from the API
            price = info.get('regularMarketDayHigh') or info.get('dayHigh')  # Current price
            prev_close = info.get('previousClose')
            volume_24h = info.get('volume24Hr')
            market_cap = info.get('marketCap')
            
            # Calculate 24h change percentage
            price_change = ((price - prev_close) / prev_close) * 100
            
            # Create embed
            color = 0x00ff00 if price_change >= 0 else 0xff0000
            arrow = "↑" if price_change >= 0 else "↓"
            
            # Create embed with hyperlinked title
            embed = discord.Embed(
                title="Solana Price Information",
                url="https://dexscreener.com/osmosis/1960",
                color=color,
                timestamp=datetime.now()
            )
            
            # First row: Price and 24h Change
            embed.add_field(
                name="Current Price",
                value=f"{arrow} ${price:.2f}",
                inline=True
            )
            
            embed.add_field(
                name="24h Change",
                value=f"{price_change:+.2f}%",
                inline=True
            )
            
            # Add empty field to force next row
            embed.add_field(name="\u200b", value="\u200b", inline=True)
            
            # Second row: Market Cap and Volume
            market_cap_formatted = f"${market_cap/1_000_000_000:.2f}B"
            embed.add_field(
                name="Market Cap",
                value=market_cap_formatted,
                inline=True
            )

            volume_formatted = f"${volume_24h:,.0f}"
            embed.add_field(
                name="24h Volume",
                value=volume_formatted,
                inline=True
            )
            
            # Add empty field to maintain grid
            embed.add_field(name="\u200b", value="\u200b", inline=True)
            
            await ctx.send(embed=embed)
                
        except Exception as e:
            print(f"Error in sol_price: {str(e)}")
            await ctx.send("❌ Error fetching SOL price data")

    @commands.command(name='chart')
    async def chart_command(self, ctx, token_type: str = None):
        """Display price chart for TETSUO or SOL"""
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
                status_msg = await ctx.send("📊 Generating chart, please wait...")
            
                if token_type == 'sol':
                    # Use SOL-specific scraper
                    from sol_chart_scraper import capture_sol_chart_async
                    chart_path = await capture_sol_chart_async(headless=True)
                else:
                    # Use original chart scraper for TETSUO
                    from chart_scraper import capture_chart_async
                    chart_path = await capture_chart_async('tetsuo')
            
                if chart_path is None:
                    await status_msg.edit(content="❌ Failed to generate chart. Please try again later.")
                    return
            
                embed = discord.Embed(
                    title=f"{'TETSUO' if token_type == 'tetsuo' else 'Solana'} Price Chart (1H)",
                    color=0x00ff00,
                    timestamp=datetime.now()
                )
            
                file = discord.File(chart_path, filename="chart.png")
                embed.set_image(url="attachment://chart.png")
            
                await ctx.send(file=file, embed=embed)
                await status_msg.delete()
            
            except Exception as e:
                await status_msg.edit(content="❌ Failed to generate chart. Please try again later.")
                print(f"Error in chart command: {str(e)}")

    @commands.command(name='help')
    async def help_command(self, ctx):
        """Display all available commands"""
        try:
            # Create embed with matching style
            embed = discord.Embed(
                title="Available Commands",
                url="https://dexscreener.com/solana/2kb3i5ulkhucjuwq3poxhpuggqbwywttk5eg9e5wnlg6",
                color=0x00ff00,
                timestamp=datetime.now()
            )

            # Price Commands
            embed.add_field(
                name="Price Commands",
                value="```\n!tetsuo - Show TETSUO price information\n!sol - Show Solana price information```",
                inline=False
            )

            # Chart Commands
            embed.add_field(
                name="Chart Commands",
                value="```\n!chart tetsuo - Show TETSUO price chart\n!chart sol - Show Solana price chart```",
                inline=False
            )

            # Utility Commands
            embed.add_field(
                name="Utility Commands",
                value="```\n!help - Show this help message```",
                inline=False
            )

            # Add cooldown information
            embed.add_field(
                name="Cooldowns",
                value="```\nPrice commands: 60 second cooldown\nChart commands: 15 second cooldown```",
                inline=False
            )

            await ctx.send(embed=embed)

        except Exception as e:
            print(f"Error in help command: {str(e)}")
            await ctx.send("❌ Error displaying help information")

    @commands.command(name='adminhelp')
    async def admin_help(self, ctx):
        """Display admin commands"""
        # Check if user has 'owner' role
        if not any(role.name.lower() == 'owner' for role in ctx.author.roles):
            await ctx.send("❌ You don't have permission to use this command.")
            return
            
        embed = discord.Embed(
            title="Admin Commands",
            color=0xFF0000,
            description="Here are all the available admin commands:"
        )
        
        admin_commands = {
            "!cookie [value]": "Update the DexScreener session cookie",
        }
        
        for cmd, desc in admin_commands.items():
            embed.add_field(name=cmd, value=desc, inline=False)
            
        await ctx.send(embed=embed)

    @commands.command(name='cookie')
    async def update_cookie(self, ctx, *, cookie_value: str = None):
        """Update DexScreener session cookie"""
        # Check if user has 'owner' role
        if not any(role.name.lower() == 'owner' for role in ctx.author.roles):
            await ctx.send("❌ You don't have permission to use this command.")
            return
            
        if not cookie_value:
            await ctx.send("❌ Please provide a cookie value. Usage: !cookie [value]")
            return
            
        try:
            # Read the current settings file
            with open('settings.py', 'r') as file:
                settings_content = file.read()
            
            # Find and replace the cookie value
            import re
            new_settings = re.sub(
                r'("value": ")([^"]+)(")',
                f'\\1{cookie_value}\\3',
                settings_content
            )
            
            # Write the updated content back to the file
            with open('settings.py', 'w') as file:
                file.write(new_settings)
                
            # Update the current session cookie
            settings.CF_COOKIES[0]['value'] = cookie_value
            
            await ctx.send("✅ Session cookie updated successfully!")
            # Delete the message to keep the cookie private
            await ctx.message.delete()
            
        except Exception as e:
            print(f"Error updating cookie: {str(e)}")
            await ctx.send("❌ Failed to update session cookie.")

def main():
    load_dotenv()
    settings.BOT_TOKEN = os.getenv('DISCORD_TOKEN')
    try:
        bot = PriceBot()
        bot.run(settings.BOT_TOKEN)
    except Exception as e:
        print(f"Error starting bot: {str(e)}")

if __name__ == "__main__":
    main()