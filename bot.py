# By Alternating
import discord
from discord.ext import tasks, commands
import requests
import asyncio
import os
from datetime import datetime
import settings
import charts

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

# command for price check tetsuo

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
    
# command to display sol price data - displays in discord

    @commands.command(name='sol')
    async def sol_price(self, ctx):
        """Display current SOL price information"""
        if not await self.check_cooldown(ctx, 'sol'):
            return
            
        try:
            response = requests.get(settings.SOL['dex_api'])
            data = response.json()
            
            if data and 'pair' in data:
                pair = data['pair']
                price = float(pair['priceUsd'])
                price_change = float(pair['priceChange']['h24']) if 'priceChange' in pair else 0
                market_cap = float(pair['fdv']) if 'fdv' in pair else None
                volume_24h = float(pair['volume']['h24']) if 'volume' in pair and 'h24' in pair['volume'] else None
                
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
                await ctx.send("❌ Unable to fetch SOL price data")
                
        except Exception as e:
            print(f"Error in sol_price: {str(e)}")
            await ctx.send("❌ Error fetching SOL price data")

# chart commands            
            
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
                # Send initial message
                status_msg = await ctx.send("📊 Generating chart, please wait...")
                
                # Generate chart using charts module
                chart_path = await charts.create_price_chart(token_type)
                
                if chart_path is None:
                    await status_msg.edit(content="❌ Failed to generate chart. Please try again later.")
                    return
                
                # Create embed with chart
                embed = discord.Embed(
                    title=f"{'TETSUO' if token_type == 'tetsuo' else 'Solana'} Price Chart (1H)",
                    color=0x00ff00,
                    timestamp=datetime.now()
                )
                
                # Add the chart image to the embed
                file = discord.File(chart_path, filename="chart.png")
                embed.set_image(url="attachment://chart.png")
                
                # Send embed with chart
                await ctx.send(file=file, embed=embed)
                
                # Delete status message and clean up chart file
                await status_msg.delete()
                os.remove(chart_path)
                
            except Exception as e:
                await status_msg.edit(content="❌ Failed to generate chart. Please try again later.")
                print(f"Error in chart command: {str(e)}")

    async def handle_chart_command(self, ctx, token_type: str):
        """Helper method to handle chart generation"""
        if not await self.check_cooldown(ctx, 'chart'):
            return
            
        async with ctx.typing():
            try:
                # Send initial message
                status_msg = await ctx.send("📊 Generating chart, please wait...")
                
                # Generate chart
                chart_path = await charts.create_price_chart(token_type)
                
                if chart_path is None:
                    await status_msg.edit(content="❌ Failed to generate chart. Please try again later.")
                    return
                
                # Create embed
                embed = discord.Embed(
                    title=f"{'TETSUO' if token_type == 'tetsuo' else 'Solana'} Price Chart (1H)",
                    color=0x00ff00,
                    timestamp=datetime.now()
                )
                
                # Add chart to embed
                file = discord.File(chart_path, filename="chart.png")
                embed.set_image(url="attachment://chart.png")
                
                # Send embed with chart
                await ctx.send(file=file, embed=embed)
                
                # Cleanup
                await status_msg.delete()
                os.remove(chart_path)
                
            except Exception as e:
                await status_msg.edit(content="❌ Failed to generate chart. Please try again later.")
                print(f"Error generating chart: {str(e)}")

    @commands.command(name='chart_tetsuo')
    async def chart_tetsuo(self, ctx):
        """Display TETSUO price chart"""
        await self.handle_chart_command(ctx, 'tetsuo')

    @commands.command(name='chart_sol')
    async def chart_sol(self, ctx):
        """Display SOL price chart"""
        await self.handle_chart_command(ctx, 'sol')

def main():
    try:
        bot = PriceBot()
        bot.run(settings.BOT_TOKEN)
    except Exception as e:
        print(f"Error starting bot: {str(e)}")

if __name__ == "__main__":
    main()