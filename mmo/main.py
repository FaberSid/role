# -*- coding: utf-8 -*- 
# coding: UTF-8
import discord,time,os
from discord.ext import commands

class Main(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.cooldown(1, 60, commands.BucketType.user)
    @commands.command(name='ping',description='BOTの速度を測ることができる',pass_context=True)
    async def pings(self,ctx):
        before = time.monotonic()
        embed = discord.Embed(description="```全自動役職付与BOT全体の反応速度```\nPong!")
        msg = await ctx.send(embed=embed)
        ping = (time.monotonic() - before) * 1000
        embed = discord.Embed(description=f"```全自動役職付与BOT全体の反応速度```\nPong! `{int(ping)}ms`")
        return await msg.edit(embed=embed)
        
    @commands.command(name='restart',description='BOTを再起動',pass_context=True)
    async def restart(self,ctx):
        if not ctx.message.author.id == 304932786286886912:
            msg = discord.Embed(description=f"指定ユーザーしか使えません。",color=0xC41415)
            return await ctx.send(embed=msg)
        msg = discord.Embed(description=f"{ctx.message.author.mention}さんが強制再起動を開始しました！",color=0xC41415)
        await ctx.send(embed=msg)
        print("BOT get restarting...")
        os.system("python NewMMO.py")

def setup(bot):
    bot.add_cog(Main(bot))