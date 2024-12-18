# By Alternating

import discord
from discord.ext import tasks, commands
import requests
import asyncio
import os
from datetime import datetime
import settings
from chart_scraper import capture_chart_async
import yfinance as yf

class PriceBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        super().__init__(command_prefix='!', intents=intents)
        
        # Initialize command cooldowns
        self.command_cooldowns = {}
        
    async def setup_hook(self):
        await self.add_cog(PriceCommands(self))
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

class PriceCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def check_cooldown(self, ctx, command_type='price'):
        """Check if command is on cooldown"""
        current_time = datetime.now()
        cooldown_key = f"{ctx.channel.id}_{command_type}"
    
        if cooldown_key in self.bot.command_cooldowns:
            time_diff = (current_time - self.bot.command_cooldowns[cooldown_key]).total_seconds()
            # Use different cooldown times for different commands
            cooldown = settings.CHART_COOLDOWN if command_type == 'chart' else settings.PRICE_COOLDOWN
            if time_diff < cooldown:
                remaining = int(cooldown - time_diff)
                await ctx.send(f'⏳ This command is on cooldown. Please wait {remaining} seconds.')
                return False
            
        self.bot.command_cooldowns[cooldown_key] = current_time
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
            
            embed = discord.Embed(
                title="Solana Price Information",
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

def main():
    try:
        bot = PriceBot()
        bot.run(settings.BOT_TOKEN)
    except Exception as e:
        print(f"Error starting bot: {str(e)}")

if __name__ == "__main__":
    main()