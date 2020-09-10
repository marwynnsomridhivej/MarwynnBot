import discord
import json
import os
import asyncio
from datetime import datetime
from discord.ext import commands
from utils import globalcommands, customerrors, paginator


gcmds = globalcommands.GlobalCMDS()
PROHIB_NAMES = ("list", "search", "create", "edit", "delete", "tag", "tags", "make", "remove")


class Tags(commands.Cog):
    
    def __init__(self, client):
        self.client = client

    async def cog_before_invoke(self, ctx):
        await gcmds.invkDelete(ctx)

    async def tag_help(self, ctx) -> discord.Message:
        timestamp = f"Executed by {ctx.author.display_name} " + "at: {:%m/%d/%Y %H:%M:%S}".format(datetime.now())
        pfx = gcmds.prefix(ctx)
        tag = (f"**Usage:** `{pfx}tag`\n"
               "**Returns:** This help menu\n"
               "**Aliases:** `tags`")
        list = (f"**Usage:** `{pfx}tag list`\n"
                "**Returns:** A list of all the tags you own, if any")
        search = (f"**Usage:** `{pfx}tag search`\n"
                  "**Returns:** A list of the top 20 tags that contain the query substring in the order of most used\n"
                  "**Special Cases:** If no tag is found, it will return an error message")
        create = (f"**Usage:** `{pfx}tag create (name)`\n"
                  "**Returns:** An interactive tag creation panel\n"
                  "**Aliases:** `make`\n"
                  "**Special Cases:** If the tag `name` already exists and you own it, you can choose to edit or delete it")
        edit = (f"**Usage:** `{pfx}tag edit (name)`\n"
                "**Returns:** An interactive tag edit panel\n"
                "**Special Cases:** If the tag does not exist, you will have the option to create it. You can only "
                "edit tags you own")
        delete = (f"**Usage:** `{pfx}tag delete`\n"
                  "**Returns:** A tag delete confirmation panel\n"
                  "**Aliases:** `remove`\n"
                  "**Special Cases:** The tag must exist and you must own the tag in order to delete it")
        cmds = [("Help", tag), ("List", list), ("Search", search), ("Create", create), ("Edit", edit), ("Delete", delete)]

        embed = discord.Embed(title="Tag Commands",
                              description=f"{ctx.author.mention}, tags are an easy way to create your own custom "
                              "command! Here are all the tag commands MarwynnBot supports",
                              color=discord.Color.blue())
        embed.set_footer(text=timestamp, icon_url=ctx.author.avatar_url)
        for name, value in cmds:
            embed.add_field(name=name,
                            value=value,
                            inline=False)
        return await ctx.channel.send(embed=embed)

    async def check_tag(self, ctx, name) -> bool:
        if not os.path.exists('db/tags.json') or not name:
            return False

        with open('db/tags.json', 'r') as f:
            file = json.load(f)

        if not name in file[str(ctx.guild.id)]:
            return False

        return True

    async def create_tag(self, ctx, name, content):
        gcmds.json_load('db/tags.json', {})
        with open('db/tags.json', 'r') as f:
            file = json.load(f)
        if not str(ctx.guild.id) in file:
            file.update({str(ctx.guild.id): {}})
        file[str(ctx.guild.id)].update({
            name: {
                'author_id': ctx.author.id,
                'content': content,
                'created_at': int(datetime.now().timestamp())
            }
        })
        with open('db/tags.json', 'w') as g:
            json.dump(file, g, indent=4)

    @commands.group(invoke_without_command=True, aliases=['tags'])
    async def tag(self, ctx, *, tag: str = None):
        if not tag:
            return await self.tag_help(ctx)
        if not await self.check_tag(ctx, tag):
            raise customerrors.TagNotFound(tag)

    @tag.command()
    async def list(self, ctx):
        return

    @tag.command()
    async def search(self, ctx, *, keyword):
        return

    @tag.command(aliases=['make'])
    async def create(self, ctx, *, tag):
        if await self.check_tag(ctx, tag):
            raise customerrors.TagAlreadyExists(tag)
        embed = discord.Embed(title=f"Create Tag \"{tag}\"",
                              description=f"{ctx.author.mention}, within 2 minutes, please enter what you would like the tag to return\n\n"
                              f"ex. *If you enter \"test\", doing `{gcmds.prefix(ctx)}tag {tag}` will return \"test\"*",
                              color=discord.Color.blue())
        embed.set_footer(text="Enter \"cancel\" to cancel this setup")
        panel = await ctx.channel.send(embed=embed)

        def from_user(message: discord.Message) -> bool:
            return message.author.id == ctx.author.id and message.channel == ctx.channel

        try:
            result = await self.client.wait_for("message", check=from_user, timeout=120)
        except asyncio.TimeoutError:
            return await gcmds.timeout(ctx, "tag creation", 120)

        await self.create_tag(ctx, tag, result.content)

    @tag.command()
    async def edit(self, ctx, *, tag):
        return

    @tag.command(aliaes=['remove'])
    async def delete(self, ctx, *, tag):
        return


def setup(client):
    client.add_cog(Tags(client))