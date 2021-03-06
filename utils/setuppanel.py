import asyncio
import re
from typing import Any, List, Union

import discord
from discord.ext import commands

from . import customerrors

__all__ = (
    "SetupPanel",
)


VALID_CORO_NAMES = [
    "get_channel",
    "get_hex",
    "get_url",
    "get_role",
    "get_message_content",
    "channel",
    "hex",
    "url",
    "role",
    "message",
    "chain",
]
channel_tag_rx = re.compile(r'<#[0-9]{18}>')
channel_id_rx = re.compile(r'[0-9]{18}')
role_tag_rx = re.compile(r'<@&[0-9]{18}>')
hex_color_rx = re.compile(r'#[A-Fa-f0-9]{6}')
url_rx = re.compile(r'https?://(?:www\.)?.+')


class SetupPanel():
    __slots__ = [
        "bot",
        "ctx",
        "author",
        "chnl",
        "guild",
        "send",
        "timeout",
        "name",
        "embed",
        "has_intro",
        "cancellable",
        "steps",
        "map",
        "channel",
        "hex",
        "url",
        "role",
        "message",
    ]

    def __init__(self, ctx: commands.Context, bot: commands.AutoShardedBot,
                 timeout: int = 30, name: str = "interactive", embed: discord.Embed = None,
                 has_intro: bool = False, cancellable: bool = True):
        self.bot = bot
        self.ctx = ctx
        self.author = ctx.author
        self.chnl = ctx.channel
        self.guild = ctx.guild
        self.send = ctx.channel.send
        self.timeout = timeout
        self.name = name
        self.embed = embed
        self.has_intro = has_intro
        self.cancellable = cancellable
        self.steps = []
        self.map = {
            "get_channel": self._from_user_channel,
            "get_message_content": self._from_user,
            "get_role": self._from_user_role,
            "get_hex": self._from_user_hex,
            "get_url": self._from_user_url,
            "until_finish": self._from_user,
        }
        self.channel = self.get_channel
        self.hex = self.get_hex
        self.url = self.get_url
        self.role = self.get_role
        self.message = self.get_message_content

    def _from_user(self, message: discord.Message) -> bool:
        if message.content.lower() == "cancel":
            raise customerrors.CancelError(self.ctx, self.name)
        return message.author == self.author and message.channel == self.chnl

    def _from_user_role(self, message: discord.Message) -> bool:
        return self._from_user(message) and re.match(role_tag_rx, message.content)

    def _from_user_channel(self, message: discord.Message) -> bool:
        return self._from_user(message) and (re.match(channel_tag_rx, message.content) or
                                             re.match(channel_id_rx, message.content))

    def _from_user_hex(self, message: discord.Message) -> bool:
        return self._from_user(message) and re.match(hex_color_rx, message.content)

    def _from_user_url(self, message: discord.Message) -> bool:
        return self._from_user(message) and re.match(url_rx, message.content)

    def _from_user_finish(self, message: discord.Message) -> bool:
        return message.author == self.author and message.channel == self.chnl and message.content.lower() == "finish"

    async def intro(self, **options) -> None:
        embed = options.get("embed", self.embed)
        if not embed:
            raise ValueError("An embed must be provided for use in the intro")
        sleep_time = float(options.get("sleep_time", 3.0))
        await self.send(embed=embed)
        await asyncio.sleep(sleep_time)
        return

    def add_step(self, coro: callable, **options) -> None:
        if options.get("ignore_error", False):
            async def ie_coro():
                try:
                    return await coro
                except Exception:
                    return options.get("default", None)
            self.steps.append(ie_coro)
        else:
            self.steps.append(coro)

    async def start(self, **options) -> List[Any]:
        if not self.steps:
            raise ValueError("Please specify at least one setup operation before starting the setup panel")
        if self.has_intro:
            await self.intro(**options)
        return [await coro for coro in self.steps]

    def get_channel(self, **options) -> None:
        async def coro(embed: discord.Embed, timeout: int, **kwargs) -> int:
            provided = kwargs.get("provided", None)

            if not provided:
                await self.send(embed=embed)
                try:
                    response = await self.bot.wait_for("message", check=self._from_user_channel, timeout=timeout)
                except asyncio.TimeoutError:
                    raise customerrors.TimeoutError(self.ctx, self.name, timeout)
            else:
                response = provided
            return int(response.content) if not "<#" in response.content else int(response.content[2:20])

        embed = options.get("embed", None)
        if not embed:
            raise ValueError("You must specify an embed")
        timeout = options.get("timeout", self.timeout)
        provided = options.get("provided", None)
        if not options.get("immediate", False):
            self.add_step(coro(embed, timeout, provided=provided))
        else:
            return self.bot.loop.create_task(coro(embed, timeout, provided=provided))

    def get_hex(self, **options) -> None:
        async def coro(embed: discord.Embed, timeout: int, **kwargs) -> int:
            provided = kwargs.get("provided", None)

            if not provided:
                await self.send(embed=embed)
                try:
                    response = await self.bot.wait_for("message", check=self._from_user_hex, timeout=timeout)
                except asyncio.TimeoutError:
                    raise customerrors.TimeoutError(self.ctx, self.name, timeout)
            else:
                response = provided
            return int(response.content[1:], 16)

        embed = options.get("embed", None)
        if not embed:
            raise ValueError("You must specify an embed")
        timeout = options.get("timeout", self.timeout)
        provided = options.get("provided", None)
        if not options.get("immediate", False):
            self.add_step(coro(embed, timeout, provided=provided))
        else:
            return self.bot.loop.create_task(coro(embed, timeout, provided=provided))

    def get_url(self, **options) -> None:
        async def coro(embed: discord.Embed, timeout: int, **kwargs) -> str:
            provided = kwargs.get("provided", None)

            if not provided:
                await self.send(embed=embed)
                try:
                    response = await self.bot.wait_for("message", check=self._from_user_url, timeout=timeout)
                except asyncio.TimeoutError:
                    raise customerrors.TimeoutError(self.ctx, self.name, timeout)
            else:
                response = provided
            return response.content

        embed = options.get("embed", None)
        if not embed:
            raise ValueError("You must specify an embed")
        timeout = options.get("timeout", self.timeout)
        provided = options.get("provided", None)
        if not options.get("immediate", False):
            self.add_step(coro(embed, timeout, provided=provided))
        else:
            return self.bot.loop.create_task(coro(embed, timeout, provided=provided))

    def get_message_content(self, **options) -> None:
        async def coro(embed: discord.Embed, timeout: int, **kwargs) -> str:
            provided = kwargs.get("provided", False)

            if not provided:
                await self.send(embed=embed)
                try:
                    response = await self.bot.wait_for("message", check=self._from_user, timeout=timeout)
                except asyncio.TimeoutError:
                    raise customerrors.TimeoutError(self.ctx, self.name, timeout)
            else:
                response = provided
            return response.content

        embed = options.get("embed", None)
        if not embed:
            raise ValueError("You must specify an embed")
        timeout = options.get("timeout", self.timeout)
        provided = options.get("provided", None)
        if not options.get("immediate", False):
            self.add_step(coro(embed, timeout, provided=provided))
        else:
            return self.bot.loop.create_task(coro(embed, timeout, provided=provided))

    def get_role(self, **options) -> None:
        async def coro(embed: discord.Embed, timeout: int,
                       obtain_type: str = "full", **kwargs) -> Union[discord.Role, int]:
            provided = kwargs.get("provided", False)

            if not provided:
                await self.send(embed=embed)
                try:
                    response = await self.bot.wait_for("message", check=self._from_user_role, timeout=timeout)
                except asyncio.TimeoutError:
                    raise customerrors.TimeoutError(self.ctx, self.name, timeout)
            else:
                response = provided

            if obtain_type == "full":
                return self.guild.get_role(int(response.content[3:21]))
            else:
                return int(response.content[3:21])

        embed = options.get("embed", None)
        if not embed:
            raise ValueError("You must specify an embed")
        timeout = options.get("timeout", self.timeout)
        obtain_type = options.get("obtain_type", "id")
        provided = options.get("provided", None)
        if not options.get("immediate", False):
            self.add_step(coro(embed, timeout, obtain_type=obtain_type, provided=provided))
        else:
            return self.bot.loop.create_task(coro(embed, timeout, obtain_type=obtain_type, provided=provided))

    def chain(self, func_names: List[str], embeds: Union[discord.Embed, List[discord.Embed]],
              timeouts: List[Union[int, float]] = None, **options) -> None:
        async def chainer(funcs: List[callable], embeds: List[discord.Embed],
                          timeouts: List[Union[int, float]], **kwargs) -> List[List[Any]]:
            values = []

            def validate(message: discord.Message) -> bool:
                checker = self.map[func.__name__]
                return checker(message)

            if not kwargs.get("provided", False):
                for embed, func, timeout in zip(embeds, funcs, timeouts):
                    kwargs['embed'] = embed
                    await self.send(embed=embed)
                    try:
                        message = await self.bot.wait_for("message", check=validate, timeout=timeout)
                    except asyncio.TimeoutError:
                        raise customerrors.TimeoutError(self.ctx, self.name, timeout)
                    values.append(func(**kwargs, provided=message, immediate=True))
            else:
                return kwargs['provided']
            await asyncio.sleep(0)
            return [task.result() for task in values]

        for name in func_names:
            if not name in VALID_CORO_NAMES:
                raise ValueError(f"{name} is not a valid setup operation name")
        else:
            funcs = [getattr(self, name) for name in func_names]
        if not timeouts:
            timeouts = [options.get("timeout", 30) for _ in funcs]
        if not options.get("immediate", False):
            self.add_step(chainer(funcs, embeds, timeouts, **options))
        else:
            return self.bot.loop.create_task(chainer(funcs, embeds, timeouts, **options))

    def until_finish(self, func_name: str, **options) -> None:
        async def repeater(func: callable, **kwargs) -> List[Any]:
            values = []
            embed = kwargs.get("embed")
            timeout = kwargs.get("timeout", 30)

            def validate(message: discord.Message) -> bool:
                checker = self.map[func.__name__]
                return self._from_user_finish(message) or checker(message)

            while True:
                await self.send(embed=embed)
                try:
                    message = await self.bot.wait_for("message", check=validate, timeout=timeout)
                except asyncio.TimeoutError:
                    raise customerrors.TimeoutError(self.ctx, self.name, timeout)
                if message.content == "finish":
                    break
                values.append(func(**kwargs, provided=message, immediate=True))
            return [task.result() for task in values]

        async def chain_repeater(**kwargs) -> List[List[Any]]:
            values = []
            func_names = kwargs.get("func_names")
            funcs = [getattr(self, name) for name in func_names]
            embeds = kwargs.get("embeds")
            timeouts = kwargs.get("timeouts", [30 for _ in func_names])

            def validate(message: discord.Message) -> bool:
                checker = self.map[func.__name__]
                return self._from_user_finish(message) or checker(message)

            while True:
                subvalues = []
                message = ""
                for func, embed, timeout in zip(funcs, embeds, timeouts):
                    await self.send(embed=embed)
                    try:
                        message = await self.bot.wait_for("message", check=validate, timeout=timeout)
                    except asyncio.TimeoutError:
                        raise customerrors.TimeoutError(self.ctx, self.name, self.timeout)
                    if message.content == "finish":
                        break
                    subvalues.append(func(embed=embed, provided=message, immediate=True, **kwargs))
                if message.content == "finish":
                    break
                await asyncio.sleep(0)
                values.append([task.result() for task in subvalues])
            return values

        if not func_name in VALID_CORO_NAMES:
            raise ValueError("Please specify a valid setup operation name")
        try:
            func = getattr(self, func_name)
        except AttributeError:
            raise AttributeError(f"'{func_name}' is not a valid setup function")
        embed = options.get("embed", None)
        if not embed and not func_name == "chain":
            raise ValueError("You must specify an embed")
        if not func_name == "chain":
            self.add_step(repeater(func, **options))
        else:
            if not options.get('func_names', None):
                raise ValueError("Please specify function names")
            elif not options.get('embeds', None):
                raise ValueError("Please specify embeds to use")
            else:
                self.add_step(chain_repeater(**options))
        return
