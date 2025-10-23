# Discord Chat Exporter

Ein einfaches Python-Package zum Exportieren von Discord-Chats als HTML-Dateien.

## Installation

```bash
pip install dc-chat-exporter
```

## Verwendung

### Mit discord.py

```python
import discord
from dc_chat_exporter import export_chat

client = discord.Client(intents=discord.Intents.default())

@client.event
async def on_ready():
    channel = client.get_channel(CHANNEL_ID)
    await export_chat(channel, limit=100)
    print("Chat exportiert!")

client.run('YOUR_TOKEN')
```

### Mit py-cord

```python
import discord
from dc_chat_exporter import export_chat

bot = discord.Bot()

@bot.slash_command(name="export", description="Exportiert den aktuellen Chat")
async def export_command(ctx):
    await ctx.defer()
    file_path = await export_chat(ctx.channel, limit=100)
    await ctx.respond(f"Chat wurde exportiert: {file_path}")

bot.run('YOUR_TOKEN')
```

## Beispiel mit Custom-Dateinamen

```python
await export_chat(channel, limit=200, output_file="mein_chat_export.html")
```

## Features

- ✅ Discord Dark Theme Design
- ✅ Zeigt Avatare, Benutzernamen und Timestamps
- ✅ Unterstützt Bilder und Anhänge
- ✅ Unterstützt Embeds
- ✅ Zeigt Rollenfarben
- ✅ Nur-Lese-Ansicht (kein Schreiben möglich)

## Lizenz

MIT License - siehe LICENSE Datei