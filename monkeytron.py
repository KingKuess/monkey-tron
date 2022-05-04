import asyncio
from inspect import Arguments
import re
import discord
from discord import flags
from discord.ext import commands, tasks
import os
import time
import sched
import threading
from discord_buttons_plugin import *
import pytz
from datetime import date, datetime
import sys
from dotenv import load_dotenv

version = "v1.0.2"
load_dotenv()

intents = discord.Intents.default()
intents.members = True


s = sched.scheduler(time.time, time.sleep)

bot = commands.Bot(command_prefix='+', intents=intents, help_command=None)
buttons = ButtonsClient(bot)

@bot.command(pass_context=True, name="help")
async def help(ctx):
    embed = discord.Embed(title="MonkeyTron " + version + " Help", colour=discord.Colour(0x3e038c))
    embed.add_field(name=f"+help", value="Shows this message\n", inline=False)
    embed.add_field(name=f"+scrim [HH:MM] [opponent + pings]", value="Schedules a scrim for the same day EST and DMs any pinged roles/members 10 minutes before unless they are in VC or react with ❌\nEX: '+scrim 21:00 Big Dogs @Gorilla'\n", inline=False)
    embed.add_field(name=f"+react [message]", value="Automatically reacts to the message with ✅ and ❌\n", inline=False)
    embed.add_field(name=f"+cancel", value="Shows the list of scheduled scrims and allows you to cancel\n", inline=False)


    await ctx.send(embed=embed)

@bot.command(pass_context=True)
async def cancel(ctx):

    components = []
    currentActionRow = []

    if (tasksDict.__len__() == 0):
        await ctx.reply("There are no scrims scheduled")
        await ctx.message.delete()
        return

    j = 0
    for i, key in enumerate(tasksDict.keys()):
        if j > 3:
            components.append(ActionRow(currentActionRow))
            j = 0
            currentActionRow = []
            currentActionRow.append(
                Button(label=key, style=ButtonType().Danger, custom_id="button_" + str(i)))
        else:
            j += 1
            currentActionRow.append(
                Button(label=key, style=ButtonType().Danger, custom_id="button_" + str(i)))
    components.append(ActionRow(currentActionRow))

    await buttons.send(
        content="Please choose which scrim to cancel",
        channel=ctx.channel.id,
        components=components)
    await ctx.message.delete()

@bot.command(pass_context=True, name="react")
async def react(ctx):
    await ctx.message.add_reaction('✅')
    await ctx.message.add_reaction('❌')
    await ctx.message.add_reaction('📅')

@bot.command(pass_context=True, name="scrim")
async def scrim(ctx):
    commandArgs = ctx.message.clean_content.split(' ')
    if len(ctx.message.mentions) == 0 and len(ctx.message.role_mentions) == 0:
        await ctx.message.channel.send(
            'Invalid Arguments, No mentioned roles. Format is +scrim [HH:MM] [message + mentions]   ex. "+scrim 21:00 big dogs @Gorilla" note: time is always same day EST')
        return

    try:
        sTime = commandArgs[1]
        sMessage = " ".join(commandArgs[2:])
    except:
        await ctx.message.channel.send(
            'Invalid Arguments, Invalid number of arguments. Format is +scrim [HH:MM] [message + mentions]   ex. "+scrim 21:00 big dogs @Gorilla" note: time is always same day EST')
        return
    
    
    if not bool(re.search('(0[0-9]|1[0-9]|2[0-3]):([0-5][0-9])', sTime)):
        await ctx.message.channel.send(
            'Invalid Arguments, time in wrong format. Format is +scrim [HH:MM] [message + mentions]   ex. "+scrim 21:00 big dogs @Gorilla" note: time is always same day EST')
        return


    await ctx.message.add_reaction('✅')
    await ctx.message.add_reaction('❌')
    await ctx.message.add_reaction('📅')

    await createScrimEvent(sTime, sMessage, ctx)


@bot.event
async def on_ready():
    print('We have logged in as {0.user}'.format(bot) + ' ' + version)
    sys.stdout.flush()
    await bot.change_presence(activity=discord.Game('Type +help for help'))


@bot.event
async def on_message(message):
    print(message.content)
    sys.stdout.flush()
    if message.author == bot.user:
        return

    await bot.process_commands(message)


tasksDict = {
}
ctxDict = {}


async def createScrimEvent(sTime, text, ctx):
    t = asyncio.get_event_loop().create_task(eventHandler(sTime, text, ctx))
    tasksDict[text + " @ " + sTime] = t
    ctxDict[text + " @ " + sTime] = ctx




async def getRoleMembers(ctx):
    Members = [] + ctx.message.mentions
    rolesToObserve = ctx.message.role_mentions
    for member in ctx.channel.members:
        for role in member.roles:
            if rolesToObserve.__contains__(role):
                Members.append(member)
    return list(set(Members))


def getTimeUTC(timeEST):
    est = pytz.timezone('US/Eastern')
    utc = pytz.utc

    nowEST = datetime.now(est)

    minutes = int(timeEST.split(":")[1])
    hours = int(timeEST.split(":")[0])

    

    sTime = est.localize(datetime(nowEST.year, nowEST.month,
                                  nowEST.day, hour=hours, minute=minutes))


    datetimeUTC = sTime.astimezone(utc)

    print("Now EST: '%s'" % nowEST)
    print("STime EST: '%s'" % sTime)
    print("Stime UTC: '%s'" % datetimeUTC)
    sys.stdout.flush()

    return datetimeUTC.timestamp()


async def eventHandler(sTime, text, ctx):
    peopleToSpam = await getRoleMembers(ctx)

    sTimeUTC = getTimeUTC(sTime)

    while time.time() < sTimeUTC - (60 * 10):
        await asyncio.sleep(30)

    originalMsg = await ctx.channel.fetch_message(ctx.message.id)

    for reaction in originalMsg.reactions:
        print(reaction)
        if reaction.emoji == '❌':
            async for user in reaction.users():
                if peopleToSpam.__contains__(user):
                    peopleToSpam.remove(user)

    for channel in ctx.guild.channels:
        if channel.type.name == "voice":
            for member in channel.members:
                if peopleToSpam.__contains__(member):
                    peopleToSpam.remove(member)

    for i, val in enumerate(peopleToSpam):
        asyncio.get_event_loop().create_task(spamMessage(val, text))

    try:
        del tasksDict[text + " @ " + sTime]
        del ctxDict[text + " @ " + sTime]
    except KeyError as ex:
        print("No such key: '%s'" % ex.message)
        sys.stdout.flush()


async def spamMessage(member, text):
    for i in range(3):
        print("Trying to send message to: " + member.name)
        sys.stdout.flush()
        await member.send("Yo " + member.name + ", time for scrim with " + text + " !!!!!!")

@buttons.click
async def button_0(ctx):
    currentKey = ""
    try:
        for i, key in enumerate(tasksDict.keys()):
            if (i == 0):
                currentKey = key
                tasksDict[key].cancel()
                await ctxDict[key].channel.send(key + " has been cancelled!")
        del ctxDict[currentKey]
        del tasksDict[currentKey]
    except KeyError as ex:
        print("No such key: '%s'" % ex.message)
        sys.stdout.flush()

    await ctx.reply("The Scrim: "+currentKey+" Has Been Cancelled!", flags=MessageFlags.EPHEMERAL)
    await ctx.message.delete()


@buttons.click
async def button_1(ctx):
    currentKey = ""
    try:
        for i, key in enumerate(tasksDict.keys()):
            if (i == 1):
                currentKey = key
                tasksDict[key].cancel()
                await ctxDict[key].channel.send(key + " has been cancelled!")
        del ctxDict[currentKey]
        del tasksDict[currentKey]
    except KeyError as ex:
        print("No such key: '%s'" % ex.message)

    await ctx.reply("The Scrim: "+currentKey+" Has Been Cancelled!", flags=MessageFlags.EPHEMERAL)
    await ctx.message.delete()


@buttons.click
async def button_2(ctx):
    currentKey = ""
    try:
        for i, key in enumerate(tasksDict.keys()):
            if (i == 2):
                currentKey = key
                tasksDict[key].cancel()
                await ctxDict[key].channel.send(key + " has been cancelled!")
        del ctxDict[currentKey]
        del tasksDict[currentKey]
    except KeyError as ex:
        print("No such key: '%s'" % ex.message)

    await ctx.reply("The Scrim: "+currentKey+" Has Been Cancelled!", flags=MessageFlags.EPHEMERAL)
    await ctx.message.delete()


@buttons.click
async def button_3(ctx):
    currentKey = ""
    try:
        for i, key in enumerate(tasksDict.keys()):
            if (i == 3):
                currentKey = key
                tasksDict[key].cancel()
                await ctxDict[key].channel.send(key + " has been cancelled!")
        del ctxDict[currentKey]
        del tasksDict[currentKey]
    except KeyError as ex:
        print("No such key: '%s'" % ex.message)

    await ctx.reply("The Scrim: "+currentKey+" Has Been Cancelled!", flags=MessageFlags.EPHEMERAL)
    await ctx.message.delete()


@buttons.click
async def button_4(ctx):
    currentKey = ""
    try:
        for i, key in enumerate(tasksDict.keys()):
            if (i == 4):
                currentKey = key
                tasksDict[key].cancel()
                await ctxDict[key].channel.send(key + " has been cancelled!")
        del ctxDict[currentKey]
        del tasksDict[currentKey]
    except KeyError as ex:
        print("No such key: '%s'" % ex.message)

    await ctx.reply("The Scrim: "+currentKey+" Has Been Cancelled!", flags=MessageFlags.EPHEMERAL)
    await ctx.message.delete()


@buttons.click
async def button_5(ctx):
    currentKey = ""
    try:
        for i, key in enumerate(tasksDict.keys()):
            if (i == 5):
                currentKey = key
                tasksDict[key].cancel()
                await ctxDict[key].channel.send(key + " has been cancelled!")
        del ctxDict[currentKey]
        del tasksDict[currentKey]
    except KeyError as ex:
        print("No such key: '%s'" % ex.message)

    await ctx.reply("The Scrim: "+currentKey+" Has Been Cancelled!", flags=MessageFlags.EPHEMERAL)
    await ctx.message.delete()


@buttons.click
async def button_6(ctx):
    currentKey = ""
    try:
        for i, key in enumerate(tasksDict.keys()):
            if (i == 6):
                currentKey = key
                tasksDict[key].cancel()
                await ctxDict[key].channel.send(key + " has been cancelled!")
        del ctxDict[currentKey]
        del tasksDict[currentKey]
    except KeyError as ex:
        print("No such key: '%s'" % ex.message)

    await ctx.reply("The Scrim: "+currentKey+" Has Been Cancelled!", flags=MessageFlags.EPHEMERAL)
    await ctx.message.delete()


@buttons.click
async def button_7(ctx):
    currentKey = ""
    try:
        for i, key in enumerate(tasksDict.keys()):
            if (i == 7):
                currentKey = key
                tasksDict[key].cancel()
                await ctxDict[key].channel.send(key + " has been cancelled!")
        del ctxDict[currentKey]
        del tasksDict[currentKey]
    except KeyError as ex:
        print("No such key: '%s'" % ex.message)

    await ctx.reply("The Scrim: "+currentKey+" Has Been Cancelled!", flags=MessageFlags.EPHEMERAL)
    await ctx.message.delete()


@buttons.click
async def button_8(ctx):
    currentKey = ""
    try:
        for i, key in enumerate(tasksDict.keys()):
            if (i == 8):
                currentKey = key
                tasksDict[key].cancel()
                await ctxDict[key].channel.send(key + " has been cancelled!")
        del ctxDict[currentKey]
        del tasksDict[currentKey]
    except KeyError as ex:
        print("No such key: '%s'" % ex.message)

    await ctx.reply("The Scrim: "+currentKey+" Has Been Cancelled!", flags=MessageFlags.EPHEMERAL)
    await ctx.message.delete()


@buttons.click
async def button_9(ctx):
    currentKey = ""
    try:
        for i, key in enumerate(tasksDict.keys()):
            if (i == 9):
                currentKey = key
                tasksDict[key].cancel()
                await ctxDict[key].channel.send(key + " has been cancelled!")
        del ctxDict[currentKey]
        del tasksDict[currentKey]
    except KeyError as ex:
        print("No such key: '%s'" % ex.message)

    await ctx.reply("The Scrim: "+currentKey+" Has Been Cancelled!", flags=MessageFlags.EPHEMERAL)
    await ctx.message.delete()


@buttons.click
async def button_10(ctx):
    currentKey = ""
    try:
        for i, key in enumerate(tasksDict.keys()):
            if (i == 10):
                currentKey = key
                tasksDict[key].cancel()
                await ctxDict[key].channel.send(key + " has been cancelled!")
        del ctxDict[currentKey]
        del tasksDict[currentKey]
    except KeyError as ex:
        print("No such key: '%s'" % ex.message)

    await ctx.reply("The Scrim: "+currentKey+" Has Been Cancelled!", flags=MessageFlags.EPHEMERAL)
    await ctx.message.delete()


@buttons.click
async def button_11(ctx):
    currentKey = ""
    try:
        for i, key in enumerate(tasksDict.keys()):
            if (i == 11):
                currentKey = key
                tasksDict[key].cancel()
                await ctxDict[key].channel.send(key + " has been cancelled!")
        del ctxDict[currentKey]
        del tasksDict[currentKey]
    except KeyError as ex:
        print("No such key: '%s'" % ex.message)

    await ctx.reply("The Scrim: "+currentKey+" Has Been Cancelled!", flags=MessageFlags.EPHEMERAL)
    await ctx.message.delete()


@buttons.click
async def button_12(ctx):
    currentKey = ""
    try:
        for i, key in enumerate(tasksDict.keys()):
            if (i == 12):
                currentKey = key
                tasksDict[key].cancel()
                await ctxDict[key].channel.send(key + " has been cancelled!")
        del ctxDict[currentKey]
        del tasksDict[currentKey]
    except KeyError as ex:
        print("No such key: '%s'" % ex.message)

    await ctx.reply("The Scrim: "+currentKey+" Has Been Cancelled!", flags=MessageFlags.EPHEMERAL)
    await ctx.message.delete()


@buttons.click
async def button_13(ctx):
    currentKey = ""
    try:
        for i, key in enumerate(tasksDict.keys()):
            if (i == 13):
                currentKey = key
                tasksDict[key].cancel()
                await ctxDict[key].channel.send(key + " has been cancelled!")
        del ctxDict[currentKey]
        del tasksDict[currentKey]
    except KeyError as ex:
        print("No such key: '%s'" % ex.message)

    await ctx.reply("The Scrim: "+currentKey+" Has Been Cancelled!", flags=MessageFlags.EPHEMERAL)
    await ctx.message.delete()


@buttons.click
async def button_14(ctx):
    currentKey = ""
    try:
        for i, key in enumerate(tasksDict.keys()):
            if (i == 14):
                currentKey = key
                tasksDict[key].cancel()
                await ctxDict[key].channel.send(key + " has been cancelled!")
        del ctxDict[currentKey]
        del tasksDict[currentKey]
    except KeyError as ex:
        print("No such key: '%s'" % ex.message)

    await ctx.reply("The Scrim: "+currentKey+" Has Been Cancelled!", flags=MessageFlags.EPHEMERAL)
    await ctx.message.delete()


@buttons.click
async def button_15(ctx):
    currentKey = ""
    try:
        for i, key in enumerate(tasksDict.keys()):
            if (i == 15):
                currentKey = key
                tasksDict[key].cancel()
                await ctxDict[key].channel.send(key + " has been cancelled!")
        del ctxDict[currentKey]
        del tasksDict[currentKey]
    except KeyError as ex:
        print("No such key: '%s'" % ex.message)

    await ctx.reply("The Scrim: "+currentKey+" Has Been Cancelled!", flags=MessageFlags.EPHEMERAL)
    await ctx.message.delete()


@buttons.click
async def button_16(ctx):
    currentKey = ""
    try:
        for i, key in enumerate(tasksDict.keys()):
            if (i == 16):
                currentKey = key
                tasksDict[key].cancel()
                await ctxDict[key].channel.send(key + " has been cancelled!")
        del ctxDict[currentKey]
        del tasksDict[currentKey]
    except KeyError as ex:
        print("No such key: '%s'" % ex.message)

    await ctx.reply("The Scrim: "+currentKey+" Has Been Cancelled!", flags=MessageFlags.EPHEMERAL)
    await ctx.message.delete()


@buttons.click
async def button_17(ctx):
    currentKey = ""
    try:
        for i, key in enumerate(tasksDict.keys()):
            if (i == 17):
                currentKey = key
                tasksDict[key].cancel()
                await ctxDict[key].channel.send(key + " has been cancelled!")
        del ctxDict[currentKey]
        del tasksDict[currentKey]
    except KeyError as ex:
        print("No such key: '%s'" % ex.message)

    await ctx.reply("The Scrim: "+currentKey+" Has Been Cancelled!", flags=MessageFlags.EPHEMERAL)
    await ctx.message.delete()


@buttons.click
async def button_18(ctx):
    currentKey = ""
    try:
        for i, key in enumerate(tasksDict.keys()):
            if (i == 18):
                currentKey = key
                tasksDict[key].cancel()
                await ctxDict[key].channel.send(key + " has been cancelled!")
        del ctxDict[currentKey]
        del tasksDict[currentKey]
    except KeyError as ex:
        print("No such key: '%s'" % ex.message)

    await ctx.reply("The Scrim: "+currentKey+" Has Been Cancelled!", flags=MessageFlags.EPHEMERAL)
    await ctx.message.delete()


@buttons.click
async def button_19(ctx):
    currentKey = ""
    try:
        for i, key in enumerate(tasksDict.keys()):
            if (i == 19):
                currentKey = key
                tasksDict[key].cancel()
                await ctxDict[key].channel.send(key + " has been cancelled!")
        del ctxDict[currentKey]
        del tasksDict[currentKey]
    except KeyError as ex:
        print("No such key: '%s'" % ex.message)

    await ctx.reply("The Scrim: "+currentKey+" Has Been Cancelled!", flags=MessageFlags.EPHEMERAL)
    await ctx.message.delete()


@buttons.click
async def button_20(ctx):
    currentKey = ""
    try:
        for i, key in enumerate(tasksDict.keys()):
            if (i == 20):
                currentKey = key
                tasksDict[key].cancel()
                await ctxDict[key].channel.send(key + " has been cancelled!")
        del ctxDict[currentKey]
        del tasksDict[currentKey]
    except KeyError as ex:
        print("No such key: '%s'" % ex.message)

    await ctx.reply("The Scrim: "+currentKey+" Has Been Cancelled!", flags=MessageFlags.EPHEMERAL)
    await ctx.message.delete()

bot.run(os.getenv('token'))
