import discord
from discord.ext import tasks, commands
import requests
import asyncio
import os
from datetime import datetime, timedelta

class PriceBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        super().__init__(command_prefix='!', intents=intents)
        
        self.token = 'YOUR_BOT_TOKEN_HERE'  # Replace with your bot token
        self.token_api_url = 'https://api.dexscreener.com/latest/dex/tokens/8i51XNNpGaKaj4G4nDdmQh95v4FKAxw8mhtaRoKd9tE8'
        self.sol_api_url = 'https://api.dexscreener.com/latest/dex/pairs/osmosis/1960'
        self.last_price_command = {}  # Store last command usage per channel
        self.last_sol_command = {}    # Store last SOL command usage per channel
        self.price_cooldown = 300  # Cooldown in seconds

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
        arrow = "↗" if price_change >= 0 else "↘"
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
        
        command_dict = self.bot.last_price_command if command_type == 'price' else self.bot.last_sol_command
        
        if channel_id in command_dict:
            time_diff = (current_time - command_dict[channel_id]).total_seconds()
            if time_diff < self.bot.price_cooldown:
                remaining_time = int(self.bot.price_cooldown - time_diff)
                await ctx.send(f'? This command is on cooldown. Please wait {remaining_time} seconds before trying again.')
                return False
        return True

    @commands.command(name='tetsuo')
    async def price_command(self, ctx):
        if not await self.check_cooldown(ctx, 'price'):
            return
        
        price_data = self.bot.get_price_data(self.bot.token_api_url)
        if price_data is not None:
            # Determine arrow and color
            arrow = "↑" if price_data['price_change'] >= 0 else "↓"
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
            await ctx.send("❌ Unable to fetch price data. Please try again later.")


    @commands.command(name='sol')
    async def sol_price_command(self, ctx):
        if not await self.check_cooldown(ctx, 'sol'):
            return
        
        price_data = self.bot.get_price_data(self.bot.sol_api_url)
        if price_data is not None:
            # Determine arrow and color
            arrow = "↑" if price_data['price_change'] >= 0 else "↓"
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
            await ctx.send("❌ Unable to fetch SOL price data. Please try again later.")


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
