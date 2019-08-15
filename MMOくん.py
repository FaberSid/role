# -*- coding: utf-8 -*- 
# coding: UTF-8
import asyncio,discord,random,psycopg2,re,os
from discord.ext import commands
    
def db_get_role(author_id,role_name):
    author_id = int(author_id)
    role_name = str(role_name)
    con = psycopg2.connect(os.environ.get("DATABASE_URL"))
    if role_name == "@everyone":
        return
    c = con.cursor()
    c.execute("INSERT INTO get_role(author_id, role_name) VALUES(%s,%s);",(author_id,role_name))
    con.commit()
    c.close()
    con.close()
    return True

def db_join_member(author_id):
    author_id = int(author_id)
    con = psycopg2.connect(os.environ.get("DATABASE_URL"))
    c = con.cursor()
    c.execute("""SELECT author_id, role_name FROM get_role WHERE author_id='%s';""",(author_id,))
    ans = c.fetchall()
    for row in ans:
        yield (row[0],row[1])
    else:
        con.commit()
        c.close()
        con.close()

def db_reset_role(author_id):
    author_id = int(author_id)
    con = psycopg2.connect(os.environ.get("DATABASE_URL"))
    c = con.cursor()
    c.execute("delete from get_role where author_id=%s;",(author_id,))
    con.commit()
    c.close()
    con.close()
    return True
    
    
class MyBot(commands.Bot):
    def __init__(self, command_prefix):
        super().__init__(command_prefix)

        self.remove_command('help')
        for cog in ['mmo.mmo_bot','mmo.main']:
            try:
                self.load_extension(cog)
            except Exception:
                pass
        print("ALL COMMAND ARE INPUTED!!")

    async def on_ready(self):
        await self.change_presence(activity=discord.Game(name="&help"))
        print("Bot get start!!!")

    async def on_member_join(self,member):
        if not member.guild.id == 337524390155780107:
            return
        if self.user == member:
            return
        await member.send("`{0}さんようこそ{1}へ！\nこの鯖はMMOくんとTAOくん専門の鯖です！\n今後ともよろしくお願いします！`".format(member.name,member.guild.name))
        up = discord.Color(random.randint(0,0xFFFFFF))
        embed = discord.Embed(title="よろしくお願いします～",
            description=f"""
            `現在の鯖の人数: `{len(member.guild.members)}
    
            `MMOのstatusを表示させる場合は: `{self.get_channel(337860614846283780).mention}
    
            `TAOのstatusを表示させる場合は: `{self.get_channel(528113643330600971).mention}
    
    
            `statusの表示のさせ方`
            `MMOの場合が!!status
            TAOの場合は::stか::statusです！`
    
            {self.get_channel(528113643330600971).mention}でTAOのstatusを表示させると
            自動で役職がもらえるよ！
    
            `自己紹介よろしくお願いします。`
            {self.get_channel(537228631097737216).mention}で自己紹介お願いします～
            """,
            color=up)
        embed.set_author(name=member.name + "さんがこの鯖に入りました！")
        embed.set_thumbnail(url="https://cdn.discordapp.com/avatars/{0.id}/{0.avatar}.png?size=1024".format(member))
        await self.get_channel(338173860719362060).send(embed=embed)
        embed = discord.Embed(title="もしこのBOTが起動してなく役職を付与されなかったら...",
            description=f"""
            `この鯖で発言権限を得るためには『暇人』役職が必要です。`
            もしこのBOTが起動してなく役職が付与されてない場合は
            このBOTが起動しているときに{self.get_channel(535957520666066954).mention}で『役職付与』と打ってください。
            """,
            color=up)
        await self.get_channel(338173860719362060).send(embed=embed)
        role = discord.utils.get(member.guild.roles,name="暇人")
        await member.add_roles(role)
        await self.get_channel(338173860719362060).send("{}さんに役職を付与しました。".format(member.mention))
        await self.get_channel(537227342104494082).edit(name="総メンバー数: {}".format(len(member.guild.members)))
        await self.get_channel(537227343207333888).edit(name="ユーザー数: {}".format(len([member for member in member.guild.members if not member.bot])))
        await self.get_channel(537227343844868096).edit(name="ボットの数: {}".format(len([member for member in member.guild.members if member.bot])))
    
        for row in db_join_member(int(member.id)):
            if int(row[0]) == int(member.id):
                role = discord.utils.get(member.guild.roles,name=str(row[1]))
                await member.add_roles(role)
                await asyncio.sleep(1)
        if db_reset_role(int(member.id)) == True:return
    
    async def on_member_remove(self,member):
        if not member.guild.id == 337524390155780107:
            return
        embed = discord.Embed(title="ありがとうございました！",description=f"{member.name}さんが\nこの鯖から退出しました...；；\n\n現在の鯖の人数: {len(member.guild.members)}名")
        embed.set_thumbnail(url="https://cdn.discordapp.com/avatars/{0.id}/{0.avatar}.png?size=1024".format(member))
        await self.get_channel(338173860719362060).send(embed=embed)
        await self.get_channel(537227342104494082).edit(name="総メンバー数: {}".format(len(member.guild.members)))
        await self.get_channel(537227343207333888).edit(name="ユーザー数: {}".format(len([member for member in member.guild.members if not member.bot])))
        await self.get_channel(537227343844868096).edit(name="ボットの数: {}".format(len([member for member in member.guild.members if member.bot])))
    
        for role in member.roles:
            ans = db_get_role(int(member.id),role.name)
            if ans == True:
                pass
    async def on_command_error(self,ctx, error):
        try:
            if isinstance(error, commands.CommandNotFound):
                try:
                    msg = discord.Embed(description=f"{ctx.message.author.mention}さん\n{ctx.message.content}というコマンドはありません！",color=0xC41415)
                    return await ctx.send(embed=msg)
                except RuntimeError:
                    pass
            elif isinstance(error,commands.CommandOnCooldown):
                msg = discord.Embed(description='{}さん！\nこのコマンドは{:.2f}秒後に使用可能です！'.format(ctx.message.author.mention, error.retry_after), color=0xC41415)
                return await ctx.send(embed=msg)
            elif isinstance(error, commands.MissingPermissions): 
                msg = discord.Embed(description=f"{ctx.message.author.mention}さん\nあなたはこのコマンドを使用するには権限がありません！",color=0xC41415)
                return await ctx.send(embed=msg)
        except discord.Forbidden: pass
    
if __name__ == '__main__':
    bot = MyBot(command_prefix='&')
    bot.run(os.environ.get("TOKEN"), bot=True, reconnect=True)
