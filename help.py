import discord
from discord.ext import commands
import settings
import re
from datetime import datetime

class HelpCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name='commands')
    async def commands_command(self, ctx):
        """Display all available commands"""
        embed = discord.Embed(
            title="Bot Commands",
            url="https://dexscreener.com/solana/2kb3i5ulkhucjuwq3poxhpuggqbwywttk5eg9e5wnlg6",
            color=0x00ff00,
            timestamp=datetime.now()
        )
        
        commands_info = {
            "!tetsuo": "Show current TETSUO price information (60s cooldown)",
            "!sol": "Show current Solana price information (60s cooldown)",
            "!chart tetsuo": "Show TETSUO price chart (15s cooldown)",
            "!chart sol": "Show Solana price chart (15s cooldown)",
            "!help": "Show this help message"
        }
        
        for cmd, desc in commands_info.items():
            embed.add_field(name=cmd, value=desc, inline=False)
                
        await ctx.send(embed=embed)

    @commands.command(name='help')
    async def help_command(self, ctx):
        """Display all available commands"""
        await self.commands_command(ctx)  # Reuse the commands command

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

async def setup(bot):
    await bot.add_cog(HelpCommands(bot))