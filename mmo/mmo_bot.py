# -*- coding: utf-8 -*- 
# coding: UTF-8
import datetime,asyncio,psycopg2,re,random,discord,os
from collections import defaultdict
from discord.ext import commands

ROLE_PER_SERVER = defaultdict(list)
ROLE_LEVEL_PER_SERVER = defaultdict(dict)

Database =os.environ.get("DATABASE_URL")

def db_read(server_id):
    server_id = int(server_id)
    con = psycopg2.connect(Database)
    c = con.cursor()
    c.execute('SELECT lower,upper,role_id FROM roles WHERE server_id=%s ORDER BY lower;',(server_id,))
    con.commit()
    ans = c.fetchall()
    for row in ans:
        yield (row[0],row[1],row[2])
    else:
        con.commit()
        c.close()
        con.close()

def db_reset(server_id):
    server_id = int(server_id)
    con = psycopg2.connect(Database)
    c = con.cursor()
    c.execute("delete from roles where server_id=%s;",(server_id,))
    con.commit()
    c.close()
    con.close()
    return True  

def db_write(server_id,lower,upper,role_id):
    server_id = int(server_id)
    lower = int(lower)
    upper = int(upper)
    role_id = int(role_id)
    con = psycopg2.connect(Database)
    c = con.cursor()
    if lower > upper:
        lower,upper = upper,lower
    c.execute('SELECT * FROM roles WHERE server_id=%s AND lower<=%s AND upper>=%s;',(server_id,lower,lower))
    if len(c.fetchall()) > 0:
        return -1  # "役職の範囲が重なっています"
    c.execute('SELECT * FROM roles WHERE server_id=%s AND lower<=%s AND upper>=%s;',(server_id,upper,upper))
    if len(c.fetchall()) > 0:
        return -2  # "役職の範囲が重なっています"
    c.execute('SELECT * FROM roles WHERE server_id=%s AND role_id=%s;',(server_id,role_id))
    if len(c.fetchall()) > 0:
        return -3  # "役職はもう既にあります"
    c.execute("INSERT INTO roles(server_id, lower, upper, role_id) VALUES(%s,%s,%s,%s);",
              (server_id,lower,upper,role_id))
    con.commit()
    con.commit()
    c.close()
    con.close()
    return True

def db_get_message(author_id):
    author_id = int(author_id)
    con = psycopg2.connect(Database)
    c = con.cursor()
    c.execute('SELECT * FROM get WHERE author_id=%s;',(author_id,))
    if c.fetchall():
        con.commit()
        c.close()
        con.close()
        return True

def db_get_author(author_id):
    author_id = int(author_id)
    con = psycopg2.connect(Database)
    c = con.cursor()
    c.execute("INSERT INTO get(author_id) VALUES(%s);",(author_id,))
    con.commit()
    c.close()
    con.close()
    return True

def db_create(syougoo_name,author_id):
    syougoo_name = str(syougoo_name)
    author_id = int(author_id)
    con = psycopg2.connect(Database)
    c = con.cursor()
    c.execute('SELECT * FROM syougou WHERE author_id=%s;',(author_id,))
    if c.fetchall():
        return -1
    c.execute("INSERT INTO syougou(syougoo_name, author_id) VALUES(%s,%s);",(syougoo_name,author_id))
    con.commit()
    c.close()
    con.close()
    return True

def db_syougou(author_id):
    author_id = int(author_id)
    con = psycopg2.connect(Database)
    c = con.cursor()
    c.execute('SELECT syougoo_name, author_id FROM syougou WHERE author_id=%s;',(author_id,))
    ans = c.fetchall()
    for row in ans:
        yield (row[0],row[1])
    else:
        con.commit()
        c.close()
        con.close()

def db_reset_syougou(author_id):
    author_id = int(author_id)
    con = psycopg2.connect(Database)
    c = con.cursor()
    c.execute("delete from syougou where author_id=%s;",(author_id,))
    con.commit()
    c.close()
    con.close()
    return True


no = '👎'
ok = '👍'
left = '⏪'
right = '⏩'
counts = 0
    
class auto_bot(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name='help',description='このBOTのすべての機能を書いた',hidden=True)
    async def ok(self,ctx):
        help_message = [f"```[&members 役職名] | その役職が誰に付与されているのかを全て表示します\n[&all-role] | 鯖の全ての役職を表示します\n[&self-role] | 自分が付与されている役職を表示します\n[&all-server] | このBOTを導入している鯖を全て表示します\n\n[&ban-list] | その鯖でBANされている人たちを表示します\n[&tsukishima] | 月島が出現した際にメンションされる役職を自動的に付与してくれます。\n[&happy-cat] | 月島役職付与の狂乱ネコ版```\n```月島出現ログというチャンネルを作成したらこの鯖で月島が出たときに通知が来るよ！\nついでにメンションも飛ぶから逃さなくても済む！\n幸せの猫遭遇ログという狂乱のネコ版のログ報告の機能もあるよ！```\n`1ページ目/2ページ中`",
                        f"```注意:これらのコマンドは管理者権限がないと操作できません。```\n```[&level lower upper 役職名] | [例: &level 1 10 aaa]\nこれで自分のTAOでのレベルが1~10の時に役職名:『aaa』が自動付与されます。\n[&list] | 今設定されている役職の全てを表示されます\n[&reset] | 設定されている役職の全てをリセットします```\n```役職更新ログというチャンネルを作成したら色んな人が役職を\n更新した際にそのチャンネルにログが残るようになります。```\n`2ページ目/2ページ目`"]
        index = 0
        while True:
            embed = discord.Embed(title=f"{self.bot.user}の使い方:",description="あれ??なんで動かないの??と思ったら開発者にお申し付けください。" + help_message[index])
            embed.set_thumbnail(url=self.bot.user.avatar_url)
            embed.add_field(name="各種リンク",
                            value="[このBOTの招待](<https://discordapp.com/oauth2/authorize?client_id=550248294551650305&permissions=8&scope=bot>) ,[このBOTの公式サーバー](<https://discord.gg/4YB8gXv>)",
                            inline=False)
            embed.set_footer(text="制作者:兄じゃぁぁぁ#3454 | 編集者: FaberSid#2459さん ,midorist#5677さん",)
            msg = await ctx.send(embed=embed)
            l = index != 0
            r = index != len(help_message) - 1
            if l:await msg.add_reaction(left)
            if r:await msg.add_reaction(right)
            try:
                def predicate(message,l,r):
                    def check(reaction,user):
                        if reaction.message.id != message.id or user == self.bot.user:return False
                        if l and reaction.emoji == left or r and reaction.emoji == right:return True
                    return check
                react = await self.bot.wait_for('reaction_add',timeout=20,check=predicate(msg,l,r))
                if react[0].emoji == left:index -= 1
                elif react[0].emoji == right:index += 1
                await msg.delete()
            except asyncio.TimeoutError: return

    @commands.command(name='give-role',description='このBOTのすべての機能を書いた',hidden=True)
    async def role_add(self,ctx):
        if not ctx.message.channel.id == 535957520666066954:
            await ctx.message.delete()
            return await ctx.send(f"このコマンドは{self.bot.get_channel(535957520666066954).mention}でしか使うことが出来ません")
            
        role = discord.utils.get(ctx.message.guild.roles,name="暇人")
        if role in ctx.message.author.roles:
            embed = discord.Embed(description=f"{ctx.message.author.mention}さん\nあなたはもう既にこの役職を持っています！！")
            embed.set_thumbnail(url=f"https://cdn.discordapp.com/avatars/{ctx.message.author.id}/{ctx.message.author.avatar}.png?size=1024")
            return await ctx.send(embed=embed)
            
        await ctx.message.author.add_roles(role)
        return await ctx.send(f"{ctx.message.author.mention}さんに『暇人』役職を付与しました。")

    @commands.command(name='members',description='このBOTのすべての機能を書いた',hidden=True)
    async def list_of_role(self,ctx,*,role_name=""):
        if not role_name:
            msg = discord.Embed(description=f"{ctx.message.author.mention}さん\n役職名はちゃんと入力して下さい！",color=0xC41415)
            return await ctx.send(embed=msg)
        elif not discord.utils.get(ctx.message.guild.roles,name=role_name):
            msg = discord.Embed(description=f"{ctx.message.author.mention}さん\nその名前の役職は存在してないそうですよ？",color=0xC41415)
            return await ctx.send(embed=msg)
        else:
            async def send(member_data):
                page = 1
                embed = discord.Embed(title=f"『{role_name}』役職を持っているメンバー！！",description="".join(member_data[(page - 1) * 20:page * 20]))
                msg =  await ctx.send(embed=embed)
                while True:
                    l = page != 1
                    r = page < len(member_data) / 20
                    if l:
                        await msg.add_reaction(left)
                    if r:
                        await msg.add_reaction(right)
                    try:
                        def predicate(message,l,r):
                            def check(reaction,user):
                                if reaction.message.id != message.id or user == self.bot.user:
                                    return False
                                if l and reaction.emoji == left or r and reaction.emoji == right:
                                    return True
                                return False
                            return check
                        react,user = await self.bot.wait_for('reaction_add',timeout=10,check=predicate(msg,l,r))
                        if react.emoji == left:
                            page -= 1
                        elif react.emoji == right:
                            page += 1
                        embeds = discord.Embed(title=f"『{role_name}』役職を持っているメンバー！！",description="".join(member_data[(page - 1) * 20:page * 20]))
                        await msg.edit(embed=embeds)
                        await msg.remove_reaction(left, self.bot.user)
                        await msg.remove_reaction(right, self.bot.user)
                        await msg.remove_reaction(react.emoji, user)
                    except asyncio.TimeoutError:  # Timeout時間までにボタンが押されなければ終了する
                        return

            i = 1
            member_data = []
            role = discord.utils.get(ctx.message.guild.roles,name=role_name)
            for member in ctx.message.guild.members:
                if role in member.roles:
                    member_data.append("".join("{0}人目:『{1}』\n".format(i,member.name)))
                    i += 1
            else:
                return await send(member_data)

    @commands.command(name='all-role',description='このBOTのすべての機能を書いた',hidden=True)
    async def all_role(self,ctx):
        def slice(li,n):
            while li:
                yield li[:n]
                li = li[n:]
        page = 1
        for roles in slice(ctx.message.guild.roles[::-1],250):
            role = [f'{i}: {role.mention}' for (i,role) in enumerate(roles,start=1)]
            userembed = discord.Embed(description="\n".join(role[(page - 1) * 50:page * 50]))
            userembed.set_thumbnail(url=ctx.message.guild.icon_url)
            userembed.set_author(name=ctx.message.guild.name + "の全役職情報:")
            userembed.set_footer(text="この鯖の役職の合計の数は[{}]です！".format(str(len(ctx.message.guild.roles))))
            msg = await ctx.send(embed=userembed)
            while True:
                l = page != 1
                r = page < len(role) / 50
                if l:
                    await msg.add_reaction(left)
                if r:
                    await msg.add_reaction(right)
                try: 
                    def predicate(message,l,r):
                        def check(reaction,user):
                            if reaction.message.id != message.id or user == self.bot.user:return False
                            if l and reaction.emoji == left or r and reaction.emoji == right:return True
                        return check
                    react,user = await self.bot.wait_for('reaction_add',timeout=10,check=predicate(msg,l,r))
                    if react.emoji == left:
                        page -= 1
                    elif react.emoji == right:
                        page += 1
                    for roles in slice(ctx.message.guild.roles[::-1],250):
                        role = [f'{i}: {role.mention}' for (i,role) in enumerate(roles,start=1)]
                    embed = discord.Embed(description="\n".join(role[(page - 1) * 50:page * 50]))
                    embed.set_thumbnail(url=ctx.message.guild.icon_url)
                    embed.set_author(name=ctx.message.guild.name + "の全役職情報:")
                    embed.set_footer(text="この鯖の役職の合計の数は[{}]です！".format(str(len(ctx.message.guild.roles))))
                    await msg.edit(embed=embed)
                    await msg.remove_reaction(left, self.bot.user)
                    await msg.remove_reaction(right, self.bot.user)
                    await msg.remove_reaction(react.emoji, user)
                except asyncio.TimeoutError:  # Timeout時間までにボタンが押されなければ終了する
                    return

    @commands.command(name='self-role',description='このBOTのすべての機能を書いた',hidden=True)
    async def author_role(self,ctx):
        page = 1
        role = [r.mention for r in ctx.message.author.roles][::-1]
        embed = discord.Embed(title=f"{ctx.message.author}に付与されてる役職一覧:",description="\n".join(role[(page - 1) * 25:page * 25]))
        embed.set_thumbnail(url="https://cdn.discordapp.com/avatars/{0.id}/{0.avatar}.png?size=1024".format(ctx.message.author))
        msg = await ctx.send(embed=embed)
        while True:
            l = page != 1
            r = page < len(role) / 20
            if l:
                await msg.add_reaction(left)
            if r:
                await msg.add_reaction(right)
            try:
                def predicate(message,l,r):
                    def check(reaction,user):
                        if reaction.message.id != message.id or user == self.bot.user:return False
                        if l and reaction.emoji == left or r and reaction.emoji == right:return True
                    return check
                react,user = await self.bot.wait_for('reaction_add',timeout=10,check=predicate(msg,l,r))
                if react.emoji == left:
                    page -= 1
                elif react.emoji == right:
                    page += 1
                role = [r.mention for r in ctx.message.author.roles][::-1]
                embeds = discord.Embed(title=f"{ctx.message.author}に付与されてる役職一覧:",description="\n".join(role[(page - 1) * 25:page * 25]))
                embeds.set_thumbnail(url="https://cdn.discordapp.com/avatars/{0.id}/{0.avatar}.png?size=1024".format(ctx.message.author))
                await msg.edit(embed=embeds)
                await msg.remove_reaction(left, self.bot.user)
                await msg.remove_reaction(right, self.bot.user)
                await msg.remove_reaction(react.emoji, user)
            except asyncio.TimeoutError:  # Timeout時間までにボタンが押されなければ終了する
                return

    @commands.command(name='all-server',description='鯖一覧取得',pass_context=True)
    async def servers(self,ctx):
        i = 1  # 10位ごとのソート用添え字
        msg = ""
        ranking_msgs = []
        for servers in self.bot.guilds:
            msg += f'{i}: `{servers.name}`\n'
            if i % 50 == 0:  # iが10になったら(10位ごとに格納するので)
                ranking_msgs.append(msg)
                i = 0  # 初期化
                msg = ""  # 初期化
            i += 1
        index = 0  # ranking_msgs用添え字
        while True:
            msg = discord.Embed(description=ranking_msgs[index])
            msg.set_author(name="全鯖一覧:")
            msg = await ctx.send(embed=msg)
            l = index != 0
            r = index != len(ranking_msgs) - 1
            if l:
                await msg.add_reaction(left)
            if r:
                await msg.add_reaction(right)
            try:
                def predicate(message,l,r):
                    def check(reaction,user):
                        if reaction.message.id != message.id or user == self.bot.user:return False
                        if l and reaction.emoji == left or r and reaction.emoji == right:return True
                    return check
                react = await self.bot.wait_for('reaction_add',timeout=20,check=predicate(msg,l,r))
            except asyncio.TimeoutError:  # Timeout時間までにボタンが押されなければ終了する
                return
            if react[0].emoji == left:  # react[0]は押された絵文字
                index -= 1
            elif react[0].emoji == right:
                index += 1
            await msg.delete()

    @commands.command(name='ban-list',description='鯖一覧取得',pass_context=True)
    async def ban(self,ctx):
        async def send(member_data):
            index = 0
            embed = discord.Embed(title="Banされた人たちリスト:",description=member_data[index])
            embed.set_thumbnail(url=ctx.message.guild.icon_url)
            msg = await ctx.send(embed=embed)
            while True:
                l = index != 0
                r = index < len(member_data) -1
                if l:
                    await msg.add_reaction(left)
                if r:
                    await msg.add_reaction(right)
                try:
                    def predicate(message,l,r):
                        def check(reaction,user):
                            if reaction.message.id != message.id or user == self.bot.user:
                                return False
                            if l and reaction.emoji == left or r and reaction.emoji == right:
                                return True
                            return False
                        return check
                    react,user = await self.bot.wait_for('reaction_add',timeout=10,check=predicate(msg,l,r))
                    if react.emoji == left:
                        index -= 1
                    elif react.emoji == right:
                        index += 1
                    msgs = discord.Embed(title="Banされた人たちリスト:",description=member_data[index])
                    msgs.set_thumbnail(url=ctx.message.guild.icon_url)
                    await msg.edit(embed=msgs)
                    await msg.remove_reaction(left, self.bot.user)
                    await msg.remove_reaction(right, self.bot.user)
                    await msg.remove_reaction(react.emoji, user)
                except asyncio.TimeoutError:  # Timeout時間までにボタンが押されなければ終了する
                    return
                
        member_data=[]
        msg = ""
        bannedUsers = await ctx.message.guild.bans()
        i=1
        for ban in bannedUsers:
            msg += f'{i}:`{ban[1].name}#{ban[1].discriminator} | ID:{ban[1].id}`\n'
            if i % 20 == 0:  # iが10になったら(10位ごとに格納するので)
                member_data.append(msg)
                i = 0  # 初期化
                msg = ""  # 初期化
            i += 1
        else:
            if i < 20 and not i == 0:
                member_data.append(msg)
            return await send(member_data)

    @commands.command(name='get',description='鯖一覧取得',pass_context=True)
    async def get(self,ctx):
        await ctx.message.delete()
        if not ctx.message.author.id == 304932786286886912:
            msg = discord.Embed(description=f"{ctx.message.author.mention}さん\nこのコマンドは指定ユーザーしか扱えません！",color=0xC41415)
            return await ctx.send(embed=msg)
        counter = 0
        for i in ctx.message.guild.channels:
            if i.type == discord.ChannelType.text:
                async for log in i.history(limit=99999999999):
                    if log.guild.id == ctx.message.guild.id:
                        counter += 1
                await self.bot.get_channel(550674420222394378).edit(name="総メッセージ数: {}".format(counter))

    @commands.command(name='tsukishima',description='鯖一覧取得',pass_context=True)
    async def tsukishima(self,ctx):
        role = discord.utils.get(ctx.message.guild.roles,name="月島報告OK")
        if not role in ctx.message.guild.roles:
            await ctx.message.guild.create_role(name="月島報告OK",mentionable=True)
            return await ctx.send("この鯖には月島報告OKの役職がなかったので勝手に作成したよ！\nもう一度コマンド打ってね！")
        await ctx.message.author.add_roles(role)
        return await ctx.send(f"{role.name}役職を{ctx.message.author.mention}さんに付与しました。")

    @commands.command(name='happy-cat',description='鯖一覧取得',pass_context=True)
    async def cats(self,ctx):
        role = discord.utils.get(ctx.message.guild.roles,name="幸せの猫遭遇報告OK")
        if not role in ctx.message.guild.roles:
            await ctx.message.guild.create_role(name="幸せの猫遭遇報告OK",mentionable=True)
            return await ctx.send("この鯖には幸せの猫遭遇報告OKの役職がなかったので勝手に作成したよ！\nもう一度コマンド打ってね！")
        await ctx.message.author.add_roles(role)
        return await ctx.send(f"{role.name}役職を{ctx.message.author.mention}さんに付与しました。")

    @commands.command(name='list',description='鯖一覧取得',pass_context=True)
    @commands.has_permissions(administrator=True)
    async def lists(self,ctx):
        if len(list(db_read(ctx.message.guild.id))) == 0:
            embed = discord.Embed(description="この鯖にはレベル役職が登録されてません。")
            return await ctx.send(embed=embed)
                
        i = 0
        reply = ""
        for row in db_read(ctx.message.guild.id):
            if i % 25 == 0:
                if i > 0:
                    embed = discord.Embed(description=reply)
                    embed.set_author(name="現在の役職リストはこちら")
                    await ctx.send(embed=embed)
                reply = "`[{}]: Lv{}~{}:『{}』`\n".format(i + 1,row[0],row[1],discord.utils.get(ctx.message.guild.roles,id=row[2]).name)
            else:
                reply += "`[{}]: Lv{}~{}:『{}』`\n".format(i + 1,row[0],row[1],discord.utils.get(ctx.message.guild.roles,id=row[2]).name)
            i += 1
        if i % 25 >= 0 or i <= 25:
            embed = discord.Embed(description=reply)
            embed.set_author(name="現在の役職リストはこちら")
            await ctx.send(embed=embed)

    @commands.command(name='reset',description='鯖一覧取得',pass_context=True)
    @commands.has_permissions(administrator=True)
    async def reset(self,ctx):
        embeds = discord.Embed(
            description=f"{ctx.message.author.mention}さん\nレベル役職の設定をすべてリセットしてもいいですか？")
        msg = await ctx.send(embed=embeds)
        await msg.add_reaction(no)
        await msg.add_reaction(ok)
        try:
            def predicate1(message,author):
                def check(reaction,users):
                    if reaction.message.id != message.id or users == self.bot.user or author != users:
                        return False
                    if reaction.emoji == ok or reaction.emoji == no:
                        return True
                    return False
                return check
            react = await self.bot.wait_for('reaction_add',timeout=20,check=predicate1(msg,ctx.message.author))
            if react[0].emoji == ok:
                db_reset(int(ctx.message.guild.id))
                embed = discord.Embed(description=f"{ctx.message.author.mention}はレベル役職の設定を全てリセットしました。")
                return await ctx.send(embed=embed)
            elif react[0].emoji == no:
                embeds = discord.Embed(
                    description=f"{ctx.message.author.mention}はレベル役職の設定をリセットしませんでした！")
                return await ctx.send(embed=embeds)
        except asyncio.TimeoutError:
            embeds = discord.Embed(
                description=f"{ctx.message.author.mention}はレベル役職の設定をリセットしませんでした！")
            return await ctx.send(embed=embeds)


    @commands.command(name='level',description='鯖一覧取得',pass_context=True)
    @commands.has_permissions(administrator=True)
    async def role_level(self,ctx,*args):
        if not args[0] or not args[1]:
            embed = discord.Embed(description=f"{ctx.message.author.mention}さん！\n数値を入力してください！\n例:[&level 1 10 aaa]")
            return await ctx.send(embed=embed)
        if not args[2]:
            embed = discord.Embed(description=f"{ctx.message.author.mention}さん！\n役職の名前を入力してください！\n例:[&level 1 10 aaa]")
            return await ctx.send(embed=embed)
        role = discord.utils.get(ctx.message.guild.roles,name=args[2])
        if not role:
            embed = discord.Embed(description=f"{ctx.message.author.mention}さん！\nどうやらこの名前の役職はこの鯖には存在しないようです！")
            return await ctx.send(embed=embed)
        embeds = discord.Embed(description="```『{}』役職が[{}~{}Lv]の間に設定しようとしています！\n大丈夫ですか？```".format(role.name,int(args[0]),int(args[1])))
        msg = await ctx.send(embed=embeds)
        await msg.add_reaction(no)
        await msg.add_reaction(ok)
        try:
            def predicate1(message,author):
                def check(reaction,users):
                    if reaction.message.id != message.id or users == self.bot.user or author != users:
                        return False
                    if reaction.emoji == ok or reaction.emoji == no:
                        return True
                    return False
                return check
            react = await self.bot.wait_for('reaction_add',timeout=20,check=predicate1(msg,ctx.message.author))
            if react[0].emoji == ok:
                ans = db_write(int(ctx.message.guild.id),int(args[0]),int(args[1]),role.id)
                if ans == True:
                    embed = discord.Embed(description="`『{}』役職が[{}~{}Lv]の間に設定されました。`".format(role.name,int(args[0]),int(args[1])))
                    return await ctx.send(embed=embed)
                elif ans == -1 or ans == -2:
                    embed = discord.Embed(description=f"{ctx.message.author.mention}さん\nこの役職のレベルの範囲は既に設定されています...")
                    return await ctx.send(embed=embed)
                elif ans == -3:
                    embed = discord.Embed(description=f"{ctx.message.author.mention}さん\nこの役職は既に設定されています...")
                    return await ctx.send(embed=embed)
                else:
                    embed = discord.Embed(description="`ERROR:未対応の戻り値`")
                    return await ctx.send(embed=embed)
            elif react[0].emoji == no:
                embeds = discord.Embed(
                    description=f"{ctx.message.author.mention}はレベル役職を設定しませんでした！")
                return await ctx.send(embed=embeds)
        except asyncio.TimeoutError:
            embeds = discord.Embed(
                description=f"{ctx.message.author.mention}はレベル役職を設定しませんでした！")
        return await ctx.send(embed=embeds)
        
    @commands.Cog.listener()
    async def on_message(self, message):
        if len(message.embeds) != 0:
            try:
                if message.embeds[0].title[-7:] == "のステータス:":
                    for f in message.embeds[0].fields:
                        if f.name == "Lv":
                            level = int(f.value)
                    member = discord.utils.get(message.guild.members,display_name= message.embeds[0].title[:-7])
                    role_range = []
                    role_level = {}
                    for lower,upper,role_id in db_read(message.guild.id):
                        role = discord.utils.get(message.guild.roles,id=role_id)
                        if role is None:
                            continue
                        role_range.append((lambda x: lower <= x < upper,role.name))
                        max_role = role.name
                        role_level[role_id] = (lower,upper)
                    role_id = next((role_id for role_id,lu in role_level.items() if (lambda x: lu[0] <= x <= lu[1])(level)),
                                   None)
                    role = discord.utils.get(message.guild.roles,id=role_id)
                    next_level = 0
                    for _,upper in sorted(role_level.values()):
                        if upper > level:
                            next_level = upper + 1
                            break
                    if max([upper for _,upper in role_level.values()]) < level:
                        await asyncio.sleep(1)
                        return await message.channel.send("```凄い！あなたはこの鯖の役職付与範囲を超えてしまった！\nぜひ運営に役職を追加して貰ってください！\nこの鯖の最高レベル役職は『{}』です。```".format(max_role))
                    if role in member.roles:
                        await asyncio.sleep(1)
                        return await message.channel.send("`次のレベル役職まで後{}Lvです！`".format(int(next_level - level)))
                    else:
                        await asyncio.sleep(1)
                        await member.add_roles(role)
                        await message.channel.send("`役職名:『{0}』を付与しました。\n次のレベル役職まで後{1}Lvです！`".format(role,int(next_level - level)))
                        embed = discord.Embed(title=str(member.name) + "さんが役職を更新しました！",description=f"```役職名:『{role}』```",color=discord.Color(random.randint(0,0xFFFFFF)))
                        embed.set_thumbnail(url="https://cdn.discordapp.com/avatars/{0.id}/{0.avatar}.png?size=1024".format(member))
                        embed.set_author(name=message.guild.me.name)
                        for channel in message.guild.channels:
                            if channel.name == '役職更新ログ':
                                return await channel.send(embed=embed)
            except TypeError:
                pass
            except AttributeError:
                pass
            except ValueError:
                pass
            try:
                lists = re.findall(r'([0-9]+)',f"{message.embeds[0].title}")
                if message.embeds[0].title == f"【超激レア】月島が待ち構えている...！\nLv.{lists[0]}  HP:{lists[1]}":
                    channels = self.bot.get_channel(message.channel.id)
                    url = f"https://discordapp.com/channels/{message.guild.id}/{message.channel.id}/{message.id}"
                    embed = discord.Embed(description=f"""{channels.mention}で月島が出現しました！\n`[Lv.{int(lists[0])}]`の月島が出現しました！\n敵の体力は`[HP:{int(lists[1])}]`\n\nゲットできる経験値数は`[{(int(lists[0]) * 100)}]`です！\n\n[**この月島への直通リンク**](<{url}>)""",)
                    embed.set_thumbnail(url="https://media.discordapp.net/attachments/526274496894730241/566274379546099745/900bd3f186c08f128b846cf2823c7403.png")
                    embed.set_footer(text=f"出現時刻: {datetime.datetime.utcnow() + datetime.timedelta(hours=9)}")
                    role = discord.utils.get(message.guild.roles,name="月島報告OK")
                    if not role in message.guild.roles:
                        await message.guild.create_role(name="月島報告OK",mentionable=True)
                        await message.channel.send("この鯖には月島報告OKの役職がなかったから勝手に作成したよ！")
                    for channel in message.guild.channels:
                        if channel.name == '月島出現ログ':
                            await channel.send(embed=embed)
                            return await channel.send(f"{role.mention}～月島出たらしいぜ！")
                            
                if message.embeds[0].title == f"【超激レア】狂乱ネコしろまるが待ち構えている...！\nLv.{lists[0]}  HP:{lists[1]}":
                    channels = self.bot.get_channel(message.channel.id)
                    url = f"https://discordapp.com/channels/{message.guild.id}/{message.channel.id}/{message.id}"
                    embed = discord.Embed(description=f"""{channels.mention}で狂乱ネコしろまるが出現しました！\n`[Lv.{int(lists[0])}]`の狂乱ネコしろまるが出現しました！\n敵の体力は`[HP:{int(lists[1])}]`\n\nゲットできる経験値数は`[{(int(lists[0]) * 100)}]`です！\n\n[**この狂乱ネコしろまるへの直通リンク**](<{url}>)""",)
                    embed.set_thumbnail(url="https://cdn.discordapp.com/attachments/366373818064830465/611144211336658945/image0.png")
                    embed.set_footer(text=f"出現時刻: {datetime.datetime.utcnow() + datetime.timedelta(hours=9)}")
                    role = discord.utils.get(message.guild.roles,name="幸せの猫遭遇報告OK")
                    if not role in message.guild.roles:
                        await message.guild.create_role(name="幸せの猫遭遇報告OK",mentionable=True)
                        await message.channel.send("この鯖には幸せの猫遭遇報告OKの役職がなかったから勝手に作成したよ！")
                    for channel in message.guild.channels:
                        if channel.name == '幸せの猫遭遇ログ':
                            await channel.send(embed=embed)
                            return await channel.send(f"{role.mention}！幸せのネコが出たってよ！")

            except IndexError:
                return

        if message.content.find("discord.gg/") != -1:
            if message.guild.id == 337524390155780107 and not message.channel.id == 421954703509946368 and not not message.channel.name == "tao-global":
                channel = self.bot.get_channel(421954703509946368)
                await message.delete()
                embed = discord.Embed(title="このチャンネルでは宣伝は禁止です！",description="{0}さん\nもし鯖の宣伝をしたいなら{1}でやってください！".format(message.author.mention,channel.mention))
                return await message.channel.send(embed=embed)
                

        if [channel for channel in message.guild.channels if message.channel.name == "tao-global"]:
            if message.author == self.bot.user:
                return
            if message.author.bot:
                if not message.author.id == 526620171658330112:
                    return
                if len(message.embeds) != 0:
                    if message.embeds[0].title != "のステータス:":
                        return
                    for f in message.embeds[0].fields.name:
                        if f == "Lv":
                            levels = str(f.value)
                        if f == "HP":
                            hp = str(f.value)
                        if f == "ATK":
                            atk = str(f.value)
                        if f == "EXP":
                            exp = str(f.value)
                        if f == "次のLvまで":
                            to_next_level = str(f.value)
                        if f == "プレイヤーランク":
                            prank = str(f.value)
                        if f == "所持アイテム":
                            items = str(f.value)
                        if f == "戦闘状況:":
                            sentou = str(f.value)
                    embeds = discord.Embed()
                    embeds.set_author(name="{}のステータス:".format(message.embeds[0].title[:-7]))
                    embeds.add_field(name="Lv",value=levels)
                    embeds.add_field(name="HP",value=hp)
                    embeds.add_field(name="ATK",value=atk)
                    embeds.add_field(name="EXP",value=exp)
                    embeds.add_field(name="次のLvまで",value=to_next_level)
                    embeds.add_field(name="プレイヤーランク",value=prank)
                    embeds.add_field(name="所持アイテム",value=items)
                    embeds.set_thumbnail(url=message.embeds[0].thumbnail.url)
                    embeds.add_field(name="戦闘状況:",value=sentou)
                    await asyncio.gather(*(c.send(embed=embeds) for c in self.bot.get_all_channels() if c.name == 'tao-global'))
                    await asyncio.sleep(3)
                    return await message.delete()
                       
                if len(message.embeds) != 0:
                    if message.embeds[0].author and message.embeds[0].author.name:
                        if message.embeds[0].title[-11:] != "のペットのステータス:":
                            return
                        for f in message.embeds[0].fields.name:
                            if f == "PETの名前:":
                                name = str(f.value)
                            if f == "Lv":
                                levels = str(f.value)
                            if f == "ATK":
                                atk = str(f.value)
                            if f == "攻撃確率":
                                exp = str(f.value)
                        embeds = discord.Embed()
                        embeds.set_author(name="{}のステータス:".format(message.embeds[0].title[:-11]))
                        embeds.add_field(name="PETの名前:",value=name)
                        embeds.add_field(name="Lv",value=levels)
                        embeds.add_field(name="ATK",value=atk)
                        embeds.add_field(name="攻撃確率",value=exp)
                        embeds.set_thumbnail(url=message.embeds[0].thumbnail.url)
                        embeds.add_field(name="戦闘状況:",value=sentou)
                        await asyncio.gather(*(c.send(embed=embeds) for c in self.bot.get_all_channels() if c.name == 'tao-global'))
                        await asyncio.sleep(3)
                        return await message.delete()
                        
            if db_get_message(int(message.author.id)) == True:
                return await message.delete()
            else:
                global counts
                try:
                    check = await self.bot.wait_for('message',check=lambda messages: messages.author == message.author,timeout=4)
                    if check:
                        counts += 1
                        if counts > 7:
                            if db_get_author(int(message.author.id)) == True:
                                embed = discord.Embed(description=f"{message.author.mention}さんはスパムをしたためこのチャンネルで発言できません。")
                                await asyncio.gather(*(c.send(embed=embed) for c in self.bot.get_all_channels() if c.name == 'tao-global'))
                                return
                except asyncio.TimeoutError:
                    pass
                if message.attachments:
                    for row in db_syougou(int(message.author.id)):
                        embed = discord.Embed(title="発言者:" + str(message.author))
                        embed.set_image(url=message.attachments[0].url)
                        embed.set_thumbnail(url="https://cdn.discordapp.com/avatars/{0.id}/{0.avatar}.png?size=1024".format(message.author))
                        embed.set_author(name=message.guild.name,icon_url=message.guild.icon_url)
                        embed.set_footer(text=f"称号:『{str(row[0])}』")
                        await asyncio.gather(*(c.send(embed=embed) for c in self.bot.get_all_channels() if c.name == 'tao-global'))
                        await asyncio.sleep(7)
                        return await message.delete()
                    else:
                        embed = discord.Embed(title="発言者:" + str(message.author))
                        embed.set_image(url=message.attachments[0].url)
                        embed.set_thumbnail(url="https://cdn.discordapp.com/avatars/{0.id}/{0.avatar}.png?size=1024".format(message.author))
                        embed.set_author(name=message.guild.name,icon_url=message.guild.icon_url)
                        embed.set_footer(text="称号:『特になし』")
                        await asyncio.gather(*(c.send(embed=embed) for c in self.bot.get_all_channels() if c.name == 'tao-global'))
                        await asyncio.sleep(7)
                        return await message.delete()
    
                await message.delete()
                if message.content.startswith("称号作成 "):
                    if message.author.id == 304932786286886912:
                        ans = db_create(str(message.content.split()[1]),int(message.content.split()[2]))
                        if ans == True:
                            embeds = discord.Embed(description=f"<@{message.content.split()[2]}>さんに『{message.content.split()[1]}』称号を付与しました。")
                            return await asyncio.gather(*(c.send(embed=embeds) for c in self.bot.get_all_channels() if c.name == 'tao-global'))
                        if ans == -1:
                            up = discord.Color(random.randint(0,0xFFFFFF))
                            embeds = discord.Embed(description=f"<@{message.content.split()[2]}>さんは既に称号を持っています。",)
                            return await asyncio.gather(*(c.send(embed=embeds) for c in self.bot.get_all_channels() if c.name == 'tao-global'))
                            
                    else:
                        embeds = discord.Embed(description=f"{message.author.mention}さん！\n称号作成コマンドはBOTの管理者しか使えないよ！")
                        return await asyncio.gather(*(c.send(embed=embeds) for c in self.bot.get_all_channels() if c.name == 'tao-global'))
    
                if message.content.startswith("称号剥奪 "):
                    if message.author.id == 304932786286886912:
                        if db_reset_syougou(int(message.content.split()[1])) == True:
                            embed = discord.Embed(description=f"<@{message.content.split()[1]}>さんの称号を剥奪いたしました。")
                            return await asyncio.gather(*(c.send(embed=embed) for c in self.bot.get_all_channels() if c.name == 'tao-global'))
    
                    else:
                        embed = discord.Embed(description=f"{message.author.mention}さん！\n称号剥奪コマンドはこのBOTの管理者しか使えないよ！")
                        return await asyncio.gather(*(c.send(embed=embed) for c in self.bot.get_all_channels() if c.name == 'tao-global'))
                        
                if message.content == "グローバルリスト":
                    async def send(server_data):
                        embed = discord.Embed(title="tao-globalに接続してる鯖リスト:",description=server_data)
                        return await asyncio.gather(*(c.send(embed=embed) for c in self.bot.get_all_channels() if c.name == 'tao-global'))
                    i=1
                    server_data = ""
                    for server in self.bot.servers:
                        if [self.bot.get_all_channels() for channel in server.channels if channel.name == "tao-global"]:
                            server_data += "{0}:『{1}』\n".format(i,server.name)
                            i += 1
                    return await send(server_data)
    
                if message.content == "この鯖の詳細":
                    online = 0
                    for i in message.guild.members:
                        if str(i.status) == 'online' or str(i.status) == 'idle' or str(i.status) == 'dnd':
                            online += 1
                    userembed = discord.Embed(title=message.guild.name + "の情報:")
                    userembed.set_thumbnail(url=message.guild.icon_url)
                    userembed.add_field(name="サーバーID:",value=message.guild.id)
                    userembed.add_field(name="サーバーオーナ:",value=message.guild.owner)
                    userembed.add_field(name="サーバーリュージョン:",value=message.guild.region)
                    userembed.add_field(name="メンバー数:",value=len(message.guild.members))
                    userembed.add_field(name="チャンネル数:",value=len(message.guild.channels))
                    userembed.add_field(name="役職数:",value=str(len(message.guild.roles)))
                    userembed.add_field(name="現在オンラインの数:",value=online)
                    userembed.add_field(name="鯖に追加した絵文字の数:",value=str(len(message.guild.emojis)))
                    userembed.add_field(name="サーバー最上位役職:",value=message.guild.role_hierarchy[0])
                    userembed.set_footer(text="サーバー作成日: " + message.guild.created_at.__format__(' %Y/%m/%d %H:%M:%S'))
                    return await asyncio.gather(*(c.send(embed=userembed) for c in self.bot.get_all_channels() if c.name == 'tao-global'))
    
                for row in db_syougou(int(message.author.id)):
                    embed = discord.Embed(title="発言者:" + str(message.author),description=message.content)
                    embed.set_thumbnail(url="https://cdn.discordapp.com/avatars/{0.id}/{0.avatar}.png?size=1024".format(message.author))
                    embed.set_footer(text=f"称号:『{str(row[0])}』")
                    embed.set_author(name=message.guild.name,icon_url=message.guild.icon_url)
                    return await asyncio.gather(*(c.send(embed=embed) for c in self.bot.get_all_channels() if c.name == 'tao-global'))
                else:
                    embed = discord.Embed(title="発言者:" + str(message.author),description=message.content)
                    embed.set_thumbnail(url="https://cdn.discordapp.com/avatars/{0.id}/{0.avatar}.png?size=1024".format(message.author))
                    embed.set_footer(text=f"称号:『特になし』")
                    embed.set_author(name=message.guild.name,icon_url=message.guild.icon_url)
                    return await asyncio.gather(*(c.send(embed=embed) for c in self.bot.get_all_channels() if c.name == 'tao-global'))

            
def setup(bot):
    bot.add_cog(auto_bot(bot))
