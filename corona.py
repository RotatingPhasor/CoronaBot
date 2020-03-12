import requests
import xmltodict
import json
import os
from bs4 import BeautifulSoup
import discord
import asyncio

DISCORD_TOKEN = 'STRING TOKEN'
# CHANNEL ID IS A NUMBER, NOT STRING
CHANNEL_ID = 111111

client = discord.Client()


def get_data():
    prev_countries = []
    if os.path.exists('/tmp/prev_countries.json'):
        with open('/tmp/prev_countries.json', 'r') as f:
            prev_countries = json.load(f)

    gUrl = "1lwnfa-GlNRykWBL5y7tWpLxDoCfs8BvzWxFjeOZ1YJk"
    idIn = "1"
    url = "https://spreadsheets.google.com/feeds/list/" + gUrl + "/" + idIn + "/public/values"
    data = requests.get(url).content
    data = xmltodict.parse(data)['feed']['entry']

    processed_data = {}
    new_countries = []
    countries = []
    total_cases = 0
    total_deaths = 0

    for entry in data:
        country = entry['gsx:country']
        p_confirmed_cases = str(entry['gsx:confirmedcases']).replace(',', '')
        if (p_confirmed_cases == 'None') or (not p_confirmed_cases):
            confirmed_cases = 0
        else:
            confirmed_cases = int(p_confirmed_cases)
        p_confirmed_deaths = str(entry['gsx:reporteddeaths']).replace(',', '')
        if (p_confirmed_deaths == 'None') or (not p_confirmed_deaths):
            confirmed_deaths = 0
        else:
            confirmed_deaths = int(p_confirmed_deaths)
        processed_data[country] = {'confirmed_deaths': confirmed_deaths, 'confirmed_cases': confirmed_cases}
        countries.append(country)
        total_cases += confirmed_cases
        total_deaths += confirmed_deaths

        if country not in prev_countries:
            new_countries.append(country)

    json.dump(countries, open('/tmp/prev_countries.json', 'w'))

    return post_discord(new_countries, processed_data, total_cases, total_deaths)


def check_change(prev_deaths, total_deaths, prev_cases, total_cases):
    if (prev_deaths != total_deaths) or (prev_cases != total_cases):
        if (total_deaths - prev_deaths >= 50) or (total_cases - prev_cases >= 100):
            return True
    return False


def post_discord(new_countries, processed_data, total_cases, total_deaths):
    if os.path.exists('/tmp/prev_data.json'):
        with open('/tmp/prev_data.json', 'r') as f:
            prev_data = json.load(f)
            prev_deaths = prev_data['prev_deaths']
            prev_cases = prev_data['prev_cases']
    else:
        prev_deaths = 0
        prev_cases = 0

    if check_change(prev_deaths, total_deaths, prev_cases, total_cases):
        messages = ['Death Count is {} 💀'.format(total_deaths),
                    'Total Cases {} 🤢'.format(total_cases)]
        json.dump({'prev_deaths': total_deaths, 'prev_cases': total_cases}, open('/tmp/prev_data.json', 'w'))
    else:
        messages = []
    for country in new_countries:
        message = "New country infected: {} :airplane:".format(country)
        messages.append(message)

    return messages


@client.event
async def on_ready():
    print('Logged in as {0.user}'.format(client))


async def corona_check():
    await client.wait_until_ready()
    while not client.is_closed():
        channel = client.get_channel(CHANNEL_ID)
        try:
            messages = get_data()
        except Exception as ex:
            print(ex)
            messages = []

        for message in messages:
            await channel.send((message))
        await asyncio.sleep(1800)


client.loop.create_task(corona_check())
client.run(DISCORD_TOKEN)
