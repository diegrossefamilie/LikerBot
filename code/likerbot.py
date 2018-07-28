import discord
import sys
import asyncio
import asyncpg
import random
import re

from variables import (
    TOKEN_LIKER,
    DUDES_WHO_CAN_MAKE_ALL,
    PGUSER,
    PGPASSWORD
)

DATABASENAME = 'likerbot'

connection = None

users, admins = {}, []

bot = discord.Client()
accept_answer_emoji = '👍'

regular = r'^lk\?(?P<command>add|delete|adminadd|admindel|adminlist|help)( (?P<discordname>[A-Za-z]+#\d{4}))?( )?(?P<smiles>.+)?'

@bot.event
async def on_message(message):
    if message.author.bot:
        return

    reg = re.search(regular, message.content, re.IGNORECASE)

    display_name = f'{message.author.name}#{message.author.discriminator}'
    context = await get_command_context(reg)

    if context is None: 
        emojis = users.get(display_name.upper())
        if emojis:
            await asyncio.sleep(random.randint(1, 3))
            try:
                await bot.add_reaction(message, emoji=random.choice(emojis))
            except:
                pass  
        return                

    if context['command'] == 'help':
        embed = discord.Embed(description="Команды могут давать только некоторые пользователи:", color=0xb800e6)
        embed.add_field(name="lk?add discord_name emojis", value="Обновляет информацию о применяемых эмоциях", inline=False)
        embed.add_field(name="lk?delete discord_name", value="Убирает информацию о применяемых эмоциях", inline=False)
        embed.add_field(name="lk?adminadd discord_name", value="Делает пользователя админом бота", inline=False)
        embed.add_field(name="lk?admindel discord_name", value="Убирает пользователя как админа бота", inline=False)
        embed.add_field(name="lk?adminlist", value="Показывает, кто сейчас может командовать ботом", inline=False)
        embed.set_author(name='Я Лайкуша миленький', icon_url=bot.user.default_avatar_url)
        helpmessage = await bot.send_message(message.channel, embed=embed)
        await asyncio.sleep(2)
        await bot.add_reaction(helpmessage, emoji='😎')  

    elif context['command'] == 'add':
        if not await check_permissions(display_name):
            await bot.add_reaction(message, emoji='❌')
            return
        discord_name = context['discord_name']
        smiles = context['smiles']

        responce = await connection.fetch(f"SELECT emojis FROM discordusers WHERE discorduser='{discord_name}';")
        if responce:
            query = f"UPDATE discordusers SET discorduser = '{discord_name}', emojis='{smiles}' WHERE discorduser = '{discord_name}';"
        else:
            query = f"INSERT INTO discordusers(discorduser, emojis) VALUES ('{discord_name}', '{smiles}');"
        await connection.fetch(query)
        await bot.add_reaction(message, emoji=accept_answer_emoji)
        await fill_cache()    

    elif context['command'] == 'delete':
        discord_name = context['discord_name']
        await connection.fetch(f"DELETE FROM discordusers WHERE discorduser = '{discord_name}';")
        await bot.add_reaction(message, emoji=accept_answer_emoji)
        await fill_cache()   

    elif context['command'] == 'adminadd':
        discord_name = context['discord_name']
        responce = await connection.fetch(f"SELECT discorduser FROM administrators WHERE discorduser = '{discord_name}';")
        if not responce:
            query = f"INSERT INTO administrators(discorduser) VALUES ('{discord_name}');"
            await connection.fetch(query)
            await bot.add_reaction(message, emoji=accept_answer_emoji)
            await fill_cache()    

    elif context['command'] == 'admindel':
        discord_name = context['discord_name']
        await connection.fetch(f"DELETE FROM administrators WHERE discorduser = '{discord_name}';")
        await bot.add_reaction(message, emoji=accept_answer_emoji)
        await fill_cache()  

    elif context['command'] == 'adminlist':
        if admins:
            adminlist = admins[:5]
            rest = len(admins) - len(adminlist)
            my_message = "\n".join(adminlist)
            if rest > 0:
                my_message = f'{my_message}\n... и еще {rest} других'
        else:
            my_message = "*а никого и нет*"
        await bot.send_message(message.channel, f"Администраторы:```{my_message}```")  


@bot.event
async def on_ready():
    await bot.change_presence(game=discord.Game(name='слежку за няшами', type=0))
    print('Лайкуша готов :з')

async def get_command_context(regex):
    if regex is None:
        return None
    
    command_name = regex.group('command').lower()
    if command_name:
        if command_name in ['help', 'adminlist']:
            return { 'command' : command_name }

        elif command_name == 'add':
            discordname = regex.group('discordname')
            smiles = regex.group('smiles')
            if discordname and smiles:
                return { 'command' : command_name, 'discord_name' : discordname.upper(), 'smiles' : smiles.replace(' ', '') }
            else:
                return None

        elif command_name in ['delete', 'adminadd', 'admindel']:
            if regex.group('discordname'):
                return { 'command' : command_name, 'discord_name' : regex.group('discordname').upper() }
            else:
                return None
    else:
        return None

async def check_permissions(display_name):
    return display_name in DUDES_WHO_CAN_MAKE_ALL or display_name.upper() in admins

async def connect_to_database():
    global connection
    try:
        connection = await asyncpg.connect(host='db' if docker else 'localhost', database=DATABASENAME, user=PGUSER, password=PGPASSWORD)
    except:
        print('Cannot connect to database')

async def fill_cache():
    responce = await connection.fetch("SELECT * FROM discordusers")
    global users
    users = {}
    for entry in responce:
        users[entry[0].upper()] = entry[1]
    
    responce = await connection.fetch("SELECT * FROM administrators")
    global admins
    admins = []
    for entry in responce:
        admins.append(entry[0].upper())

docker = 'docker' in sys.argv[1:]

loop = asyncio.get_event_loop()
loop.run_until_complete(connect_to_database())
loop.run_until_complete(fill_cache())
loop.run_until_complete(bot.run(TOKEN_LIKER))

loop.close()
