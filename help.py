import discord
from discord.ext import commands
import settings
from datetime import datetime

class HelpCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name='commands')
    async def commands_command(self, ctx):
        """Display all available commands"""
        embed = discord.Embed(
            title="Bot Commands",
            url="https://dexscreener.com/solana/2kb3i5ulkhucjuwq3poxhpuggqbwywttk5eG9E5WnLG6",
            color=0x00ff00,
            timestamp=datetime.now()
        )
        
        commands_info = {
            "!tetsuo": "Show current TETSUO price information (60s cooldown)",
            "!sol": "Show current Solana price information (60s cooldown)",
            "!chart tetsuo [timeframe]": "Show TETSUO price chart (15s cooldown). Timeframes: 15m, 30m, 1h, 4h, 1d",
            "!chart sol [timeframe]": "Show Solana price chart (15s cooldown). Timeframes: 15m, 30m, 1h, 4h, 1d",
            "!help": "Show this help message"
        }
        
        for cmd, desc in commands_info.items():
            embed.add_field(name=cmd, value=desc, inline=False)
                
        await ctx.send(embed=embed)

    @commands.command(name='help')
    async def help_command(self, ctx):
        """Display all available commands"""
        await self.commands_command(ctx)  # Reuse the commands command

async def setup(bot):
    await bot.add_cog(HelpCommands(bot))