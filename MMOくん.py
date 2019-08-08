# --------------------------------------------------------------------------------------------------------------------
import os
import asyncio
import sys
import psycopg2
import random
import signal
import re

from datetime import datetime
from contextlib import closing
from collections import defaultdict

ROLE_PER_SERVER = defaultdict(list)
ROLE_LEVEL_PER_SERVER = defaultdict(dict)

try:
    from discord.ext import commands
    from discord.ext.commands import Bot
    from discord.voice_client import VoiceClient
    from discord import ChannelType
    import discord
except ImportError:
    print("Discord.py がインストールされていません。\nDiscord.pyをインストールしてください。")
    sys.exit(1)
# -------------------------------------------------------------------------------------------------------------------
client = Bot(command_prefix='&',pm_help=True)
message_counter = 0
left = '⏪'
right = '⏩'

def predicate(message,l,r):
    def check(reaction,user):
        if reaction.message.id != message.id or user == client.user:
            return False
        if l and reaction.emoji == left:
            return True
        if r and reaction.emoji == right:
            return True
        return False
    return check


# -------------------------------------------------------------------------------------------------------------------
@client.event
async def on_server_join(server):
    await client.send_message(server.owner,
                              f"""```
                              {server.owner}さん
                              このBOTを入れてくれてありがとう！
                              このBOTは管理:The.First.Step#3454
                              多大なるサポート:FaberSidさん,midoristさん
                              の協力のもと作成しました！
                              ```""")
    up = discord.Color(random.randint(0,0xFFFFFF))
    embed = discord.Embed(
        title=server.name + "鯖にこのBOTが導入されました",
        description="このBOTはTAOと連動しています",
        color=up
    )
    embed.set_author(
        name="役職自動付与BOT-NEWを導入した鯖情報:"
    )
    embed.set_thumbnail(
        url=server.icon_url
    )
    embed.add_field(
        name="鯖名:",
        value=server.name,
        inline=True
    )
    embed.add_field(
        name="サーバーID:",
        value=server.id,
        inline=True
    )
    embed.add_field(
        name="鯖のチャンネル数:",
        value=len(server.channels),
        inline=True
    )
    embed.add_field(
        name="鯖の人数:",
        value=len(server.members),
        inline=True
    )
    embed.add_field(
        name="役職数:",
        value=str(len(server.roles)),
        inline=True
    )
    embed.add_field(
        name="鯖の主の名前:",
        value=server.owner,
        inline=True
    )
    embed.set_footer(
        text="サーバー作成日: " + server.created_at.__format__(' %Y/%m/%d %H:%M:%S')
    )
    await client.send_message(client.get_channel('529139075165192192'),embed=embed)


# -------------------------------------------------------------------------------------------------------------------
@client.event
async def on_member_join(member):
    if not member.server.id == "337524390155780107":
        return
    if client.user == member:
        return

    await client.send_message(client.get_channel('559284148649328670'),
                              "イベント情報!!\n後`『{}』`人がこの鯖に入ったらなんらかのイベント開始です！".format(
                                  int(50 - len(member.server.members) % 50)))
    await client.send_message(member,
                              "`{0}さんようこそ{1}へ！\nこの鯖はMMOくんとTAOくん専門の鯖です！\n今後ともよろしくお願いします！`".format(member.name,
                                                                                                 member.server.name))
    mmo = client.get_channel('337860614846283780')
    tao = client.get_channel('528113643330600971')
    self = client.get_channel('537228631097737216')
    yakushoku = client.get_channel('535957520666066954')
    up = discord.Color(random.randint(0,0xFFFFFF))
    embed = discord.Embed(
        title="よろしくお願いします～",
        description=f"""
        `現在の鯖の人数: `{len(member.server.members)}

        `MMOのstatusを表示させる場合は: `{mmo.mention}

        `TAOのstatusを表示させる場合は: `{tao.mention}


        `statusの表示のさせ方`
        `MMOの場合が!!status
        TAOの場合は::stか::statusです！`

        {tao.mention}でTAOのstatusを表示させると
        自動で役職がもらえるよ！

        `自己紹介よろしくお願いします。`
        {self.mention}で自己紹介お願いします～
        """,
        color=up
    )
    embed.set_author(
        name=member.name + "さんがこの鯖に入りました！"
    )
    embed.set_thumbnail(
        url="https://cdn.discordapp.com/avatars/{0.id}/{0.avatar}.png?size=1024".format(member)
    )
    await client.send_message(client.get_channel('338173860719362060'),embed=embed)
    embed = discord.Embed(
        title="もしこのBOTが起動してなく役職を付与されなかったら...",
        description=f"""
        `この鯖で発言権限を得るためには『暇人』役職が必要です。`
        もしこのBOTが起動してなく役職が付与されてない場合は
        このBOTが起動しているときに{yakushoku.mention}で『役職付与』と打ってください。
        """,
        color=up
    )
    await client.send_message(client.get_channel('338173860719362060'),embed=embed)
    role = discord.utils.get(member.server.roles,name="暇人")
    await client.add_roles(member,role)
    await client.send_message(client.get_channel('338173860719362060'),"{}さんに役職を付与しました。".format(member.mention))
    await client.edit_channel(client.get_channel("537227342104494082"),
                              name="総メンバー数: {}".format(len(member.server.members)))
    await client.edit_channel(client.get_channel("537227343207333888"),name="ユーザー数: {}".format(
        len([member for member in member.server.members if not member.bot])))
    await client.edit_channel(client.get_channel("537227343844868096"),
                              name="ボットの数: {}".format(len([member for member in member.server.members if member.bot])))

    for row in db_join_member(int(member.id)):
        if int(row[0]) == int(member.id):
            role = discord.utils.get(member.server.roles,name=str(row[1]))
            await client.add_roles(member,role)
            await asyncio.sleep(1)
    else:
        if db_reset_role(int(member.id)) == True:
            return


# -------------------------------------------------------------------------------------------------------------------
@client.event
async def on_member_remove(member):
    if not member.server.id == "337524390155780107":
        return
    up = discord.Color(random.randint(0,0xFFFFFF))
    embed = discord.Embed(
        title="ありがとうございました！",
        description=f"{member.name}さんが\nこの鯖から退出しました...；；\n\n現在の鯖の人数: {len(member.server.members)}名",
        color=up
    )
    embed.set_thumbnail(
        url="https://cdn.discordapp.com/avatars/{0.id}/{0.avatar}.png?size=1024".format(member)
    )
    await client.send_message(client.get_channel('338173860719362060'),embed=embed)
    await client.edit_channel(client.get_channel("537227342104494082"),
                              name="総メンバー数: {}".format(len(member.server.members)))
    await client.edit_channel(client.get_channel("537227343207333888"),name="ユーザー数: {}".format(
        len([member for member in member.server.members if not member.bot])))
    await client.edit_channel(client.get_channel("537227343844868096"),
                              name="ボットの数: {}".format(len([member for member in member.server.members if member.bot])))

    for role in member.roles:
        ans = db_get_role(
            int(member.id),
            role.name)
        if ans == True:
           pass 
    else:
        return


# -------------------------------------------------------------------------------------------------------------------
async def change_status():
    await client.wait_until_ready()

    while not client.is_closed:
        await client.change_presence(game=discord.Game(name="&helpしてね！"))
        await asyncio.sleep(30)


async def change_role():
    await client.wait_until_ready()

    while not client.is_closed:
        server = client.get_server('337524390155780107')
        for role in server.roles:
            if role.id == '562512114166792192':
                up = discord.Color(random.randint(0,0xFFFFFF))
                await client.edit_role(server=server,role=role,colour=up)
                await asyncio.sleep(10)


# -------------------------------------------------------------------------------------------------------------------
@client.event
async def on_message(message):
    if len(message.embeds) != 0:
        embed = message.embeds[0]
        if embed.get("title"):
            pattern = r'([0-9]+)'
            try:
                lists = re.findall(pattern,embed["title"])
                if embed["title"] == f"【超激レア】月島が待ち構えている...！\nLv.{lists[0]}  HP:{lists[1]}":
                    channels = client.get_channel(message.channel.id)
                    url = f"https://discordapp.com/channels/{int(message.server.id)}/{int(message.channel.id)}/{int(message.id)}"
                    embed = discord.Embed(
                        description=f"""{channels.mention}で月島が出現しました！\n`[Lv.{int(lists[0])}]`の月島が出現しました！\n敵の体力は`[HP:{int(lists[1])}]`\n\nゲットできる経験値数は`[{(int(lists[0]) * 100)}]`です！\n\n[**この月島への直通リンク**](<{url}>)""",
                        timestamp=message.timestamp
                    )
                    embed.set_thumbnail(
                        url="https://media.discordapp.net/attachments/526274496894730241/566274379546099745/900bd3f186c08f128b846cf2823c7403.png"
                    )
                    embed.set_footer(
                        text="出現時刻: "
                    )
                    role = discord.utils.get(message.server.roles,name="月島報告OK")
                    if not role in message.server.roles:
                        await client.create_role(message.author.server,name="月島報告OK",mentionable=True)
                        await client.send_message(message.channel,"この鯖には月島報告OKの役職がなかったから勝手に作成したよ！")
                    for channel in message.server.channels:
                        if channel.name == '月島出現ログ':
                            await client.send_message(channel,embed=embed)
                            await client.send_message(channel,f"{role.mention}～月島出たらしいぜ！")
                            return
            except IndexError:
                return

    if message.content.find("discord.gg/") != -1:
        if message.server.id == "337524390155780107":
            if not message.channel.id == "421954703509946368":
                if not message.channel.name == "mmo-global-chat":
                    channel = client.get_channel('421954703509946368')
                    await client.delete_message(message)
                    up = discord.Color(random.randint(0,0xFFFFFF))
                    embed = discord.Embed(
                        title="このチャンネルでは宣伝は禁止です！",
                        description="{0}さん\nもし鯖の宣伝をしたいなら{1}でやってください！\n時間制限無しの宣伝をお願いします！\n\n鯖にTAOかMMOくんが入っていないと宣伝はしてはいけません！".format(
                            message.author.mention,channel.mention),
                        color=up
                    )
                    await client.send_message(message.channel,embed=embed)
                    return

    help_message = [
        f"""[**このBOTの招待**](<https://discordapp.com/oauth2/authorize?client_id=550248294551650305&permissions=8&scope=bot>)\n何かがおかしい...。あれ...？なんで動かないの？\nと思ったら<@304932786286886912>にお申し付けください。\n\n[`1ページ目`]\nこのメッセージを表示。\n\n[`2ページ目`]\nこのBOTのコマンドの機能を表示。\n\n[`3ページ目`]\nTAOと連動するための設定方法を表示！\n\n[`4ページ目`]\nTAO公式鯖でのクランの機能説明。\n\n```このBOTは\n管理者:The.First.Step#3454\n副管理者:FaberSid#2459さん\n副管理者:midorist#5677さん\nの3人で制作しました！```\n\n1ページ目/4ページ中""",
        f"""[`リスト 役職名`]\nリスト　役職名でその役職が何人に\n付与されているのかを表示します。\n\n[`全役職一覧`]\nメッセージが送信された鯖でのすべての役職を\n埋め込みメッセージで送信します。\n\n[`役職一覧`]\n自分が付与されている役職を\n埋め込みメッセージで送信します。\n\n[`全鯖一覧`]\nこのBOTを導入している鯖を全て表示します。\n\n[`バンリスト`]\nその鯖でBANされている人たちを表示します。\n\n[`&taoか&TAO <内容>`]\nこれをしたらTAO鯖に直してほしいところや\nTAOが落ちているということを伝えれます！\n\n2ページ目/4ページ中""",
        f"""
        注意:これらのレベル設定コマンドは管理者権限が

        [`&level lower upper 役職名`]
        これでそのレベルが何処からどこまでの範囲で
        対応したいのかを設定することが出来ます！

        `[例: &level 1 10 aaa]`
        これで自分のTAOでのレベルが1~10の時に
        『aaa』という役職が付与されるようになりました。

        [`&list`]
        これで今設定されているレベル役職の全てを
        表示することが出来ます。

        [`&reset`]
        今のところ設定されているレベル役職の範囲を
        全てリセットいたします。

        (間違えてレベル役職の範囲を設定してしまった場合とかに
        お使いいただけたらなと思っています。)

        [`月島役職付与`]
        月島が出現した際にメンションされる役職を
        自動的に付与してくれるコマンドです！

        ```役職更新ログというチャンネルを作成したら
        もし色んな人が役職を更新した際にその
        チャンネルにログが残るようになります。作ってみてね！```

        ```月島出現ログというチャンネルを作成したら
        他のチャンネルで月島が出たときに月島情報が載るよ！
        ついでにメンションも飛ぶから逃さなくても済む！```

        3ページ目/4ページ中""",
        f"""これらの機能は[**TAO公式鯖**](<https://discord.gg/d7Qqfhy>)に入りクランに参加\nして頂かないとほとんど意味が無いです。 \n\n[`クラン勢力図`]\n他のクランと自分のクランとの比較をしたり、\nメンバーの数を確認したり、総長などは誰なのかを把握出来ます。\n\n[`自クラン勢力図`]\n自分が入っているクランの具体的なメンバーや\n総長などを表示することが出来ます。\n\n[`除外 @メンション 理由`]\n注意:これは総長や副総長ではないと使用できないです。\n自分のクランで悪目立ちしている人や荒らしなどの権限を\n剥奪することが出来ます。理由を書かないと除外できません。\n\n4ページ目/4ページ中""",
    ]

    if message.content == "&help":
        index = 0
        while True:
            up = discord.Color(random.randint(0,0xFFFFFF))
            embed = discord.Embed(
                title="Help一覧:",
                description=help_message[index],
                color=up
            )
            embed.set_thumbnail(
                url="https://cdn.discordapp.com/avatars/{0.id}/{0.avatar}.png?size=1024".format(client.user)
            )
            msg = await client.send_message(message.channel,embed=embed)
            l = index != 0
            r = index != len(help_message) - 1
            if l:
                await client.add_reaction(msg,left)
            if r:
                await client.add_reaction(msg,right)
            react,user = await client.wait_for_reaction(check=predicate(msg,l,r))
            if react.emoji == left:
                index -= 1
            elif react.emoji == right:
                index += 1
            await client.delete_message(msg)

    if message.content == "役職付与":
        if not message.channel.id == "535957520666066954":
            channel = client.get_channel('535957520666066954')
            await client.delete_message(message)
            await client.send_message(message.channel,"このコマンドは{}でしか使うことが出来ません".format(channel.mention))
            return
        role = discord.utils.get(message.server.roles,name="暇人")
        if role in message.author.roles:
            up = discord.Color(random.randint(0,0xFFFFFF))
            embed = discord.Embed(
                description=f"{message.author.mention}さん\nあなたはもう既にこの役職を持っています！！",
                color=up
            )
            embed.set_thumbnail(
                url="https://cdn.discordapp.com/avatars/{0.id}/{0.avatar}.png?size=1024".format(message.author)
            )
            await client.send_message(message.channel,embed=embed)
        else:
            await client.add_roles(message.author,role)
            await client.send_message(message.channel,"{0}さんに『{1}』役職を付与しました。".format(message.author.mention,role))

    if message.content.startswith("リスト"):
        async def send(member_data):
            page = 1
            name = message.content[4:]
            role = discord.utils.get(message.server.roles,name=message.content[4:])
            if not role == None:
                nick_name = f"『{name}』役職を持っているメンバー！！"
            else:
                nick_name = f"{message.author}さん\n『{name}』役職はこの鯖には存在しておりません..."
            embed = discord.Embed(
                title=nick_name,
                description="".join(member_data[(page - 1) * 20:page * 20]),
                timestamp=message.timestamp
            )
            embed.set_author(
                name="メンバー詳細:"
            )
            embed.set_footer(
                text="現在時刻:"
            )
            msg = await client.send_message(message.channel,embed=embed)
            while True:
                l = page != 1
                r = page < len(member_data) / 20
                if l:
                    await client.add_reaction(msg,left)
                if r:
                    await client.add_reaction(msg,right)
                react,user = await client.wait_for_reaction(check=predicate(msg,l,r))
                if react.emoji == left:
                    page -= 1
                elif react.emoji == right:
                    page += 1
                name = message.content[4:]
                role = discord.utils.get(message.server.roles,name=message.content[4:])
                if not role == None:
                    nick_name = f"『{name}』役職を持っているメンバー！！"
                else:
                    nick_name = f"{message.author}さん\n『{name}』役職はこの鯖には存在しておりません..."
                embed = discord.Embed(
                    title=nick_name,
                    description="".join(member_data[(page - 1) * 20:page * 20]),
                    timestamp=message.timestamp
                )
                embed.set_author(
                    name="メンバー詳細:"
                )
                embed.set_footer(
                    text="現在時刻:"
                )
                await client.edit_message(msg,embed=embed)
                await client.clear_reactions(msg)

        i = 1
        member_data = []
        role = discord.utils.get(message.server.roles,name=message.content[4:])
        for member in message.server.members:
            if role is None:
                member_data = []
                await send(member_data)
                return
            if role in member.roles:
                member_data.append("".join(
                    "{0}人目:『{1}』\n".format(i,member.name)))
                i += 1
        else:
            await send(member_data)
            return

    if message.content == "全役職一覧":
        def slice(li,n):
            while li:
                yield li[:n]
                li = li[n:]

        page = 1
        for roles in slice(message.server.role_hierarchy,250):
            role = [f'{i}: {role.mention}' for (i,role) in enumerate(roles,start=1)]
            userembed = discord.Embed(
                title="役職一覧:",
                description="\n".join(role[(page - 1) * 50:page * 50]),
                color=discord.Color.light_grey()
            )
            userembed.set_thumbnail(
                url=message.server.icon_url
            )
            userembed.set_author(
                name=message.server.name + "の全役職情報:"
            )
            userembed.set_footer(
                text="この鯖の役職の合計の数は[{}]です！".format(str(len(message.server.roles)))
            )
            msg = await client.send_message(message.channel,embed=userembed)
            while True:
                l = page != 1
                r = page < len(role) / 50
                if l:
                    await client.add_reaction(msg,left)
                if r:
                    await client.add_reaction(msg,right)
                react,user = await client.wait_for_reaction(check=predicate(msg,l,r))
                if react.emoji == left:
                    page -= 1
                elif react.emoji == right:
                    page += 1
                for roles in slice(message.server.role_hierarchy,250):
                    role = [f'{i}: {role.mention}' for (i,role) in enumerate(roles,start=1)]
                    userembed = discord.Embed(
                        title="役職一覧:",
                        description="\n".join(role[(page - 1) * 50:page * 50]),
                        color=discord.Color.light_grey()
                    )
                    userembed.set_thumbnail(
                        url=message.server.icon_url
                    )
                    userembed.set_author(
                        name=message.server.name + "の全役職情報:"
                    )
                    userembed.set_footer(
                        text="この鯖の役職の合計の数は[{}]です！".format(str(len(message.server.roles)))
                    )
                    await client.edit_message(msg,embed=userembed)
                    await client.clear_reactions(msg)

    if message.content == '役職一覧':
        page = 1
        role = [r.mention for r in message.author.roles][::-1]
        embed = discord.Embed(
            title="**{}**に付与されてる役職一覧:".format(message.author),
            description="\n".join(role[(page - 1) * 25:page * 25]),
            color=discord.Color(random.randint(0,0xFFFFFF))
        )
        embed.set_thumbnail(
            url="https://cdn.discordapp.com/avatars/{0.id}/{0.avatar}.png?size=1024".format(message.author)
        )
        msg = await client.send_message(message.channel,embed=embed)
        while True:
            l = page != 1
            r = page < len(role) / 25
            if l:
                await client.add_reaction(msg,left)
            if r:
                await client.add_reaction(msg,right)
            react,user = await client.wait_for_reaction(check=predicate(msg,l,r))
            if react.emoji == left:
                page -= 1
            elif react.emoji == right:
                page += 1
            role = [r.mention for r in message.author.roles][::-1]
            embed = discord.Embed(
                title="**{}**に付与されてる役職一覧:".format(message.author),
                description="\n".join(role[(page - 1) * 25:page * 25]),
                color=discord.Color(random.randint(0,0xFFFFFF))
            )
            embed.set_thumbnail(
                url="https://cdn.discordapp.com/avatars/{0.id}/{0.avatar}.png?size=1024".format(message.author)
            )
            await client.edit_message(msg,embed=embed)
            await client.clear_reactions(msg)

    if message.content == "全鯖一覧":
        def slice(li,n):
            while li:
                yield li[:n]
                li = li[n:]

        page = 1
        for servers in slice(list(client.servers),500):
            all_server = [f'{i}: `{server.name}`' for (i,server) in enumerate(servers,start=1)]
            embed = discord.Embed(
                title="全鯖一覧",
                description="\n".join(all_server[(page - 1) * 50:page * 50]),
                colour=discord.Color(random.randint(0,0xFFFFFF))
            )
            embed.set_footer(
                text="合計:{}鯖がこのBOTを導入しています！".format(len(client.servers))
            )
            msg = await client.send_message(message.channel,embed=embed)
            while True:
                l = page != 1
                r = page < len(all_server) / 50
                if l:
                    await client.add_reaction(msg,left)
                if r:
                    await client.add_reaction(msg,right)
                react,user = await client.wait_for_reaction(check=predicate(msg,l,r))
                if react.emoji == left:
                    page -= 1
                elif react.emoji == right:
                    page += 1
                for servers in slice(list(client.servers),500):
                    all_server = [f'{i}: `{server.name}`' for (i,server) in enumerate(servers,start=1)]
                    embed = discord.Embed(
                        title="全鯖一覧",
                        description="\n".join(all_server[(page - 1) * 50:page * 50]),
                        colour=discord.Color(random.randint(0,0xFFFFFF))
                    )
                    embed.set_footer(
                        text="合計:{}鯖がこのBOTを導入しています！".format(len(client.servers))
                    )
                    await client.edit_message(msg,embed=embed)
                    await client.clear_reactions(msg)

    if message.content == "バンリスト":
        bannedUsers = await client.get_bans(message.server)
        embed = discord.Embed(
            title="Banされた人たちリスト",
            description='\n'.join(
                f'{i}:`{user.name}` | `ID:{user.id}`' for (i,user) in enumerate(bannedUsers,start=1)),
            colour=discord.Color(random.randint(0,0xFFFFFF))
        )
        embed.set_thumbnail(
            url=message.server.icon_url
        )
        embed.set_footer(
            text="この鯖のBANされている人たちの合計の数は{}人です！".format(len(bannedUsers))
        )
        await client.send_message(message.channel,embed=embed)
        return

    if message.content == "&get":
        await client.delete_message(message)
        counter = 0
        channel_name = client.get_channel("550674420222394378")
        for i in message.server.channels:
            async for log in client.logs_from(i,limit=99999999999):
                if log.server.id == message.server.id:
                    counter += 1
            await client.edit_channel(channel_name,name="総メッセージ数: {}".format(counter))
        return

    if message.content.startswith('&TAO') or message.content.startswith("&tao"):
        sayd = message.content[5:]
        if sayd == "":
            await client.send_message(message.channel,
                                      "```『&taoか&TAO』 <text>\n\ntextに入力した内容をBotがSupport鯖へ送信します。(実行したコマンドは削除されます)```")
            return
        try:
            embed = discord.Embed(
                description="・発言者:" + message.author.name + "\n・送り先:" + message.server.name,
                color=discord.Color.dark_grey(),
                timestamp=message.timestamp
            )
            embed.set_thumbnail(
                url="https://cdn.discordapp.com/avatars/{0.id}/{0.avatar}.png?size=1024".format(message.author)
            )
            embed.add_field(
                name="**サポートしてほしい内容:**",
                value=f"```{sayd}```"
            )
            embed.set_footer(
                text="発言時刻: "
            )
            embed.set_author(
                name=client.user.name,
                icon_url=client.user.avatar_url,
            )
            await client.delete_message(message)
            await client.send_message(client.get_channel('559986180859625483'),embed=embed)
            remembed = discord.Embed(
                title="報告した内容:",
                description=f"""
                ```{sayd}```

                ご協力ありがとうございます。
                このメッセージはTAOを管理してる鯖に送られました。
                """,
                color=discord.Color.dark_grey()
            )
            await client.send_message(message.channel,embed=remembed)
        except IndexError:
            await client.send_message(message.channel,
                                      "```『&taoか&TAO』 <text>\n\ntextに入力した内容をBotがSupport鯖へ送信します。(実行したコマンドは削除されます)```")
        finally:
            pass

    if message.content == "月島役職付与":
        role = discord.utils.get(message.server.roles,name="月島報告OK")
        if not role in message.server.roles:
            await client.create_role(message.server,name="月島報告OK",mentionable=True)
            await client.send_message(message.channel,"この鯖には月島報告OKの役職がなかったから勝手に作成したよ！")
            return
        else:
            await client.add_roles(message.author,role)
            await client.send_message(message.channel,f"{role.name}役職を{message.author.mention}さんに付与いたしました。")
            return


    # globalチャット関連
            
    channel = [channel for channel in message.server.channels if message.channel.name == "tao-global"]
    if channel:
        global counts
        check = await client.wait_for_message(timeout=4,author=message.author)
        if check:
            counts += 1
            if counts > 7:
                if db_get_author(int(message.author.id)) == True:
                    embed = discord.Embed(
                        description=f"{message.author.mention}さんはスパムをしたためこのチャンネルでは発言できません。",
                        color=discord.Color(random.randint(0,0xFFFFFF))
                    )
                    await asyncio.gather(*(client.send_message(c,embed=embed) for c in
                                           client.get_all_channels() if
                                           c.name == 'tao-global'))
                    return
        if check is None:
            counts = 0
        if message.author == client.user:
            return
        if message.author.bot:
            if not message.author.id == "526620171658330112":
                return
            if len(message.embeds) != 0:
                embed = message.embeds[0]
                if embed.get("author") and embed["author"].get("name"):
                    if embed["author"]["name"][-7:] != "のステータス:":
                        return
                    url = embed["thumbnail"]["url"]
                    authors = embed["author"]["name"][:-7]
                    for f in embed["fields"]:
                        if f["name"] == "Lv":
                            levels = str(f["value"])
                        if f["name"] == "HP":
                            hp = str(f["value"])
                        if f["name"] == "ATK":
                            atk = str(f["value"])
                        if f["name"] == "EXP":
                            exp = str(f["value"])
                        if f["name"] == "次のLvまで":
                            to_next_level = str(f["value"])
                        if f["name"] == "プレイヤーランク":
                            prank = str(f["value"])
                        if f["name"] == "所持アイテム":
                            items = str(f["value"])
                        if f["name"] == "戦闘状況:":
                            sentou = str(f["value"])
                    embed = discord.Embed()
                    embed.set_author(name="{}のステータス:".format(authors),)
                    embed.add_field(name="Lv",value=levels)
                    embed.add_field(name="HP",value=hp)
                    embed.add_field(name="ATK",value=atk)
                    embed.add_field(name="EXP",value=exp)
                    embed.add_field(name="次のLvまで",value=to_next_level)
                    embed.add_field(name="プレイヤーランク",value=prank)
                    embed.add_field(name="所持アイテム",value=items)
                    embed.set_thumbnail(url=url)
                    embed.add_field(name="戦闘状況:",value=sentou)
                    await asyncio.sleep(5)
                    await asyncio.gather(*(client.send_message(c,embed=embed) for c in client.get_all_channels() if
                                           c.name == 'tao-global'))
                    await asyncio.sleep(3)
                    await client.delete_message(message)
                    return
                
            if len(message.embeds) != 0:
                embed = message.embeds[0]
                if embed.get("author") and embed["author"].get("name"):
                    if embed["author"]["name"][-11:] != "のペットのステータス:":
                        return
                    url = embed["thumbnail"]["url"]
                    authors = embed["author"]["name"][:-11]
                    for f in embed["fields"]:
                        if f["name"] == "PETの名前:":
                            name = str(f["value"])
                        if f["name"] == "Lv":
                            levels = str(f["value"])
                        if f["name"] == "ATK":
                            hp = str(f["value"])
                        if f["name"] == "攻撃確率":
                            exp = str(f["value"])
                    embed = discord.Embed()
                    embed.set_author(name="{}のステータス:".format(authors),)
                    embed.add_field(name="PETの名前:",value=name)
                    embed.add_field(name="Lv",value=levels)
                    embed.add_field(name="ATK",value=hp)
                    embed.add_field(name="攻撃確率",value=exp)
                    embed.set_thumbnail(url=url)
                    embed.add_field(name="戦闘状況:",value=sentou)
                    await asyncio.sleep(5)
                    await asyncio.gather(*(client.send_message(c,embed=embed) for c in client.get_all_channels() if
                                           c.name == 'tao-global'))
                    await asyncio.sleep(3)
                    await client.delete_message(message)
                    return
        if db_get_message(int(message.author.id)) == True:
            await client.delete_message(message)
            return
        else:
            if message.attachments:
                for row in db_syougou(int(message.author.id)):
                    embed = discord.Embed(
                        title="発言者:" + str(message.author),
                        color=discord.Color.magenta(),
                        timestamp=message.timestamp
                    )
                    embed.set_image(
                        url=message.attachments[0]['url']
                    )
                    embed.set_thumbnail(
                        url="https://cdn.discordapp.com/avatars/{0.id}/{0.avatar}.png?size=1024".format(message.author)
                    )
                    embed.set_author(
                        name=message.server.name,
                        icon_url=message.server.icon_url
                    )
                    embed.set_footer(
                        text=f"称号:『{str(row[0])}』発言時刻: "
                    )
                    await asyncio.gather(*(client.send_message(c,embed=embed) for c in client.get_all_channels() if
                                           c.name == 'tao-global'))
                    await asyncio.sleep(10)
                    await client.delete_message(message)
                    return
                else:
                    embed = discord.Embed(
                        title="発言者:" + str(message.author),
                        color=discord.Color.magenta(),
                        timestamp=message.timestamp
                    )
                    embed.set_image(
                        url=message.attachments[0]['url']
                    )
                    embed.set_thumbnail(
                        url="https://cdn.discordapp.com/avatars/{0.id}/{0.avatar}.png?size=1024".format(message.author)
                    )
                    embed.set_author(
                        name=message.server.name,
                        icon_url=message.server.icon_url
                    )
                    embed.set_footer(
                        text="称号:『特になし』発言時刻: "
                    )
                    await asyncio.gather(*(client.send_message(c,embed=embed) for c in client.get_all_channels() if
                                           c.name == 'tao-global'))
                    await asyncio.sleep(10)
                    await client.delete_message(message)
                    return

            await client.delete_message(message)
            if message.content.startswith("称号作成 "):
                if message.author.id == "304932786286886912":
                    ans = db_create(
                        str(message.content.split()[1]),
                        int(message.content.split()[2])
                    )
                    if ans == True:
                        up = discord.Color(random.randint(0,0xFFFFFF))
                        embed = discord.Embed(
                            description=f"<@{message.content.split()[2]}>さんに『{message.content.split()[1]}』称号を付与しました。",
                            color=up,
                            timestamp=message.timestamp
                        )
                        embed.set_footer(
                            text="現在時刻:"
                        )
                        await asyncio.gather(*(client.send_message(c,embed=embed) for c in client.get_all_channels() if
                                               c.name == 'tao-global'))
                        return
                    if ans == -1:
                        up = discord.Color(random.randint(0,0xFFFFFF))
                        embed = discord.Embed(
                            description=f"<@{message.content.split()[2]}>さんは既に称号を持っています。",
                            color=up,
                            timestamp=message.timestamp
                        )
                        embed.set_footer(
                            text="現在時刻:"
                        )
                        await asyncio.gather(*(client.send_message(c,embed=embed) for c in client.get_all_channels() if
                                               c.name == 'tao-global'))
                        return
                else:
                    up = discord.Color(random.randint(0,0xFFFFFF))
                    embed = discord.Embed(
                        description="称号作成コマンドはこのBOTの管理者しか作成できないよ！",
                        color=up,
                        timestamp=message.timestamp
                    )
                    embed.set_footer(
                        text="現在時刻:"
                    )
                    embed.set_author(
                        name=message.server.name,
                        icon_url=message.server.icon_url
                    )
                    await asyncio.gather(*(client.send_message(c,embed=embed) for c in client.get_all_channels() if
                                           c.name == 'tao-global'))
                    return

            if message.content.startswith("称号剥奪 "):
                if message.author.id == "304932786286886912":
                    if db_reset_syougou(int(message.content.split()[1])) == True:
                        embed = discord.Embed(
                            description=f"<@{message.content.split()[1]}>さんの称号を剥奪いたしました。",
                            color=discord.Color(random.randint(0,0xFFFFFF))
                        )
                        await asyncio.gather(*(client.send_message(c,embed=embed) for c in client.get_all_channels() if
                                               c.name == 'tao-global'))
                        return

                else:
                    up = discord.Color(random.randint(0,0xFFFFFF))
                    embed = discord.Embed(
                        description="称号剥奪コマンドはこのBOTの管理者しか作成できないよ！",
                        color=up,
                        timestamp=message.timestamp
                    )
                    embed.set_footer(
                        text="現在時刻:"
                    )
                    embed.set_author(
                        name=message.server.name,
                        icon_url=message.server.icon_url
                    )
                    await asyncio.gather(*(client.send_message(c,embed=embed) for c in client.get_all_channels() if
                                           c.name == 'tao-global'))
                    return

            if message.content == "グローバルリスト":
                async def send(server_data):
                    up = discord.Color(random.randint(0,0xFFFFFF))
                    embed = discord.Embed(
                        title="tao-globalチャンネルに接続してるサバリスト:",
                        description=server_data,
                        color=up,
                        timestamp=message.timestamp
                    )
                    embed.set_footer(
                        text="現在時刻:"
                    )
                    await asyncio.gather(*(client.send_message(c,embed=embed) for c in client.get_all_channels() if
                                           c.name == 'tao-global'))

                i = 1
                server_data = ""
                for server in client.servers:
                    if [client.get_all_channels() for channel in server.channels if channel.name == "tao-global"]:
                        server_data += "{0}:『{1}』\n".format(i,server.name)
                        if i % 100 == 0:
                            await send(server_data)
                            # リセットする
                            server_data = ""
                        i += 1
                else:
                    await send(server_data)
                    return

            if message.content == "この鯖の詳細":
                server = message.server
                region = message.server.region
                channelss = len(message.server.channels)
                memberss = len(message.server.members)
                role = str(len(server.roles))
                emoji = str(len(server.emojis))
                owner = server.owner
                tekitou = server.role_hierarchy[0]
                online = 0
                for i in server.members:
                    if str(i.status) == 'online' or str(i.status) == 'idle' or str(i.status) == 'dnd':
                        online += 1
                up = discord.Color(random.randint(0,0xFFFFFF))
                userembed = discord.Embed(
                    title=server.name + "の情報:",
                    color=up
                )
                userembed.set_thumbnail(
                    url=server.icon_url
                )
                userembed.add_field(
                    name="サーバーID:",
                    value=server.id
                )
                userembed.add_field(
                    name="サーバーオーナ:",
                    value=owner
                )
                userembed.add_field(
                    name="サーバーリュージョン:",
                    value=region
                )
                userembed.add_field(
                    name="メンバー数:",
                    value=memberss
                )
                userembed.add_field(
                    name="チャンネル数:",
                    value=channelss
                )
                userembed.add_field(
                    name="役職数:",
                    value=role
                )
                userembed.add_field(
                    name="現在オンラインの数:",
                    value=online
                )
                userembed.add_field(
                    name="鯖に追加した絵文字の数:",
                    value=emoji
                )
                userembed.add_field(
                    name="サーバー最上位役職:",
                    value=tekitou
                )
                userembed.set_footer(
                    text="サーバー作成日: " + server.created_at.__format__(' %Y/%m/%d %H:%M:%S')
                )
                await asyncio.gather(*(client.send_message(c,embed=userembed) for c in client.get_all_channels() if
                                       c.name == 'tao-global'))
                return

            for row in db_syougou(int(message.author.id)):
                embed = discord.Embed(
                    title="発言者:" + str(message.author),
                    description=message.content,
                    color=discord.Color.dark_grey(),
                    timestamp=message.timestamp
                )
                embed.set_thumbnail(
                    url="https://cdn.discordapp.com/avatars/{0.id}/{0.avatar}.png?size=1024".format(message.author)
                )
                embed.set_footer(
                    text=f"称号:『{str(row[0])}』\n 発言時刻 "
                )
                embed.set_author(
                    name=message.server.name,
                    icon_url=message.server.icon_url
                )
                await asyncio.gather(*(client.send_message(c,embed=embed) for c in client.get_all_channels() if
                                       c.name == 'tao-global'))
                return
            else:
                embed = discord.Embed(
                    title="発言者:" + str(message.author),
                    description=message.content,
                    color=discord.Color.dark_grey(),
                    timestamp=message.timestamp
                )
                embed.set_thumbnail(
                    url="https://cdn.discordapp.com/avatars/{0.id}/{0.avatar}.png?size=1024".format(message.author)
                )
                embed.set_footer(
                    text="称号:『特になし』\n 発言時刻 "
                )
                embed.set_author(
                    name=message.server.name,
                    icon_url=message.server.icon_url
                )
                await asyncio.gather(*(client.send_message(c,embed=embed) for c in client.get_all_channels() if
                                       c.name == 'tao-global'))
                return

    # -------------------------------------------------------------------------------------------------------------------
    if message.content.startswith('&shutdown'):
        if not message.author.id == "304932786286886912":
            await client.send_message(message.channel,"**これは全権限者しか使用できないコマンドです.**")
            return
        try:
            os.kill(os.getpid(),signal.CTRL_C_EVENT)
            # await client.logout()
        except Exception:
            pass
    # TAOのstatusの処理
    # -------------------------------------------------------------------------------------------------------------------
    if message.content == "&list":
        if message.author.server_permissions.administrator:
            if len(list(db_read(message.server.id))) == 0:
                embed = discord.Embed(
                    description="この鯖にはレベル役職が登録されてません。",
                    color=discord.Color(random.randint(0,0xFFFFFF))
                )
                await client.send_message(message.channel,embed=embed)
                return
            i = 0
            reply = ""
            for row in db_read(message.server.id):
                if i % 25 == 0:
                    if i > 0:
                        embed = discord.Embed(
                            description=reply,
                        )
                        embed.set_author(
                            name="現在の役職リストはこちらです。",
                        )
                        await client.send_message(message.channel,embed=embed)
                    reply = "`[{}]: Lv{}~{}:『{}』`\n".format(i + 1,row[0],row[1],discord.utils.get(
                        message.server.roles,id=str(row[2])).name)
                else:
                    reply += "`[{}]: Lv{}~{}:『{}』`\n".format(i + 1,row[0],row[1],discord.utils.get(
                        message.server.roles,id=str(row[2])).name)
                i += 1
            if i % 25 >= 0 or i <= 25:
                embed = discord.Embed(
                    description=reply,
                )
                embed.set_author(
                    name="現在の役職リストはこちらです。"
                )
                await client.send_message(message.channel,embed=embed)

    if message.content == "&reset":
        if message.author.server_permissions.administrator:
            db_reset(int(message.server.id))
            embed = discord.Embed(
                description="レベル役職の設定を全てリセットしました。",
                color=discord.Color(random.randint(0,0xFFFFFF))
            )
            await client.send_message(message.channel,embed=embed)

    if message.content.startswith("&level "):
        if message.author.server_permissions.administrator:
            role = discord.utils.get(message.server.roles,name=message.content.split(None,3)[3])
            ans = db_write(
                int(message.server.id),
                int(message.content.split()[1]),
                int(message.content.split()[2]),
                role.id
            )
            if ans == True:
                embed = discord.Embed(
                    description="`『{}』役職が[{}~{}Lv]の間に設定されました。`".format(role.name,int(message.content.split()[1]),
                                                                       int(message.content.split()[2])),
                    color=discord.Color(random.randint(0,0xFFFFFF))
                )
                await client.send_message(message.channel,embed=embed)
            elif ans == -1 or ans == -2:
                embed = discord.Embed(
                    description=f"{message.author.mention}さん\nこの役職のレベルの範囲は既に設定されています...",
                    color=discord.Color(random.randint(0,0xFFFFFF))
                )
                await client.send_message(message.channel,embed=embed)
            elif ans == -3:
                embed = discord.Embed(
                    description=f"{message.author.mention}さん\nこの役職は既に設定されています...",
                    color=discord.Color(random.randint(0,0xFFFFFF))
                )
                await client.send_message(message.channel,embed=embed)
            else:
                embed = discord.Embed(
                    description="`未対応の戻り値`",
                    color=discord.Color(random.randint(0,0xFFFFFF))
                )
                await client.send_message(message.channel,embed=embed)

    if len(message.embeds) != 0:
        embed = message.embeds[0]
        if embed.get("author") and embed["author"].get("name"):
            if embed["author"]["name"][-7:] != "のステータス:":
                return
            authos = embed["author"]["name"][:-7]
            for f in embed["fields"]:
                if f["name"] == "Lv":
                    level = int(f["value"])
            member = discord.utils.get(message.server.members,display_name=authos)
            server_id = message.server.id
            role_range = []
            role_level = {}
            for lower,upper,role_id in db_read(server_id):
                role = discord.utils.get(message.server.roles,id=str(role_id))
                if role is None:
                    continue
                role_range.append((lambda x: lower <= x < upper,role.name))
                max_role = role.name
                role_level[role_id] = (lower,upper)
            role_id = next((role_id for role_id,lu in role_level.items() if (lambda x: lu[0] <= x <= lu[1])(level)),
                           None)
            role = discord.utils.get(message.server.roles,id=str(role_id))
            next_level = 0
            for _,upper in sorted(role_level.values()):
                if upper > level:
                    next_level = upper + 1
                    break
            if max([upper for _,upper in role_level.values()]) < level:
                await asyncio.sleep(2)
                await client.send_message(message.channel,
                                          "```凄い！あなたはこの鯖のレベル役職の付与範囲を超えてしまった！\nぜひ運営に役職を追加して貰ってください！\nこの鯖のTAOの最高レベル役職は『{}』です。```".format(
                                              max_role))
                return
            if role in member.roles:
                await asyncio.sleep(2)
                await client.send_message(message.channel,
                                          "`次のレベル役職まで後{}Lvです！`".format(int(next_level - level)))
                return
            else:
                await asyncio.sleep(2)
                await client.add_roles(member,role)
                await client.send_message(message.channel,
                                          "`役職名:『{0}』を付与しました。\n次のレベル役職まで後{1}Lvです！`".format(
                                              role,int(next_level - level)))
                mem = str(member.name)
                embed = discord.Embed(
                    title=mem + "さんが役職を更新しました！",
                    description=f"```役職名:『{role}』```",
                    color=discord.Color(random.randint(0,0xFFFFFF)),
                    timestamp=message.timestamp
                )
                embed.set_thumbnail(
                    url="https://cdn.discordapp.com/avatars/{0.id}/{0.avatar}.png?size=1024".format(
                        member)
                )
                embed.set_footer(
                    text="役職更新時刻 :"
                )
                embed.set_author(
                    name=message.server.me.name
                )
                for channel in message.server.channels:
                    if channel.name == '役職更新ログ':
                        await client.send_message(channel,embed=embed)
                return


def db_read(server_id):
    server_id = int(server_id)
    con = psycopg2.connect(os.environ.get("DATABASE_URL"))
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


con = psycopg2.connect(os.environ.get("DATABASE_URL"))
def db_reset(server_id):
    server_id = int(server_id)
    c = con.cursor()
    c.execute("delete from roles where server_id=%s;",(server_id,))
    con.commit()
    c.close()
    con.close()
    return True  # print("リセット完了")


def db_write(server_id,lower,upper,role_id):
    server_id = int(server_id)
    lower = int(lower)
    upper = int(upper)
    role_id = int(role_id)
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
    c = con.cursor()
    c.execute('SELECT * FROM get WHERE author_id=%s;',(author_id,))
    if c.fetchall():
        con.commit()
        c.close()
        con.close()
        return True


def db_get_author(author_id):
    author_id = int(author_id)
    c = con.cursor()
    c.execute("INSERT INTO get(author_id) VALUES(%s);",(author_id,))
    con.commit()
    c.close()
    con.close()
    return True

def db_create(syougoo_name,author_id):
    syougoo_name = str(syougoo_name)
    author_id = int(author_id)
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
    c = con.cursor()
    c.execute("delete from syougou where author_id=%s;",(author_id,))
    con.commit()
    c.close()
    con.close()
    return True

def db_get_role(author_id,role_name):
    author_id = int(author_id)
    role_name = str(role_name)
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
    c = con.cursor()
    c.execute("""SELECT author_id, role_name FROM get_role WHERE author_id='%s';""",(author_id,))
    ans = c.fetchall()
    for row in ans:
        print(row)
        yield (row[0],row[1])
    else:
        con.commit()
        c.close()
        con.close()

def db_reset_role(author_id):
    author_id = int(author_id)
    c = con.cursor()
    c.execute("delete from get_role where author_id=%s;",(author_id,))
    con.commit()
    c.close()
    con.close()
    return True

client.loop.create_task(change_role())
client.loop.create_task(change_status())
client.run(os.environ.get("TOKEN"))
