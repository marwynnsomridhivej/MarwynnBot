from random import randint

import discord
from discord.ext import commands, tasks
from faker import Faker
from utils import extract

COLOR_FORMATS = ['hex', 'rgb', 'hsv', 'hsl']
HUES = ['red', 'orange', 'yellow', 'green', 'blue', 'purple', 'pink']
LUMINOSITIES = ['bright', 'dark', 'light']


class AutoGen(commands.Cog):
    def __init__(self, bot: commands.AutoShardedBot):
        self.bot = bot
        self.fake = Faker()
        self.set_faker_seed.start()

    async def send(self, ctx, name: str, func: str, color: discord.Color = None) -> discord.Message:
        embed = discord.Embed(title=name.title(),
                              description=f"```{func}```",
                              color=color or discord.Color.blue())
        embed.set_footer(text=f"Disclaimer: The data provided is randomly generated using Faker "
                         "(https://pypi.org/project/Faker/). Any resemblance to real values in any "
                         "way is purely coincidental. This functionality is intended to be used for generating "
                         "values for testing purposes.")
        return await ctx.channel.send(embed=embed)

    @tasks.loop(seconds=60)
    async def set_faker_seed(self):
        Faker.seed(randint(0, 100000))

    def cog_unload(self):
        if self.set_faker_seed.is_running:
            self.set_faker_seed.stop()

    @commands.command(aliases=['aaddress'],
                      desc="Returns an autogenerated address",
                      usage="autoaddress")
    async def autoaddress(self, ctx):
        return await self.send(ctx, "address", self.fake.address())

    @commands.command(aliases=['acity'],
                      desc="Returns a autogenerated city name",
                      usage="autocity")
    async def autocity(self, ctx):
        return await self.send(ctx, "city", self.fake.city())

    @commands.command(aliases=['acountry'],
                      desc="Returns an autogenerated country name",
                      usage="autocountry")
    async def autocountry(self, ctx):
        return await self.send(ctx, "country", self.fake.country())

    @commands.command(aliases=['astreet'],
                      desc="Returns an autogenerated street name",
                      usage="autostreet")
    async def autostreet(self, ctx):
        return await self.send(ctx, "street", self.fake.street_name())

    @commands.command(aliases=['alp', 'alicense'],
                      desc="Returns an autogenerated license plate",
                      usage="autolicenseplace")
    async def autolicenseplate(self, ctx):
        return await self.send(ctx, "license plate", self.fake.license_plate())

    @commands.command(aliases=['acolor'],
                      desc="Returns an autogenerated color value",
                      usage="autocolor (format) (hue) (luminosity)",
                      note='`(format)` can be "hex", "hsv", "hsl", or "rgb", defaults to "hex"'
                      '`(hue)` can be "red", "orange", "yellow", "green", "blue", "purple", "pink", '
                      'or can be unspecified for a random hue.\n\n'
                      '`(luminosity)` can be "bright", "dark", "light", or unspecified for a random luminosity')
    async def autocolor(self, ctx, *, options: str = None):
        options = options.split(" ") if options else []
        color_format = extract(options, COLOR_FORMATS, func="lower", default="hex")
        hue = extract(options, HUES, func="lower")
        luminosity = extract(options, LUMINOSITIES, func="lower", default="random")
        return await self.send(
            ctx,
            f"{color_format} color",
            self.fake.color(
                hue=hue, luminosity=luminosity, color_format=color_format
            )
        )

    @commands.command(aliases=['acn', 'acolorname'],
                      desc="Returns an autogenerated color name",
                      usage="autocolorname")
    async def autocolorname(self, ctx):
        return await self.send(ctx, "color name", self.fake.color_name())

    @commands.command(aliases=['abs'],
                      desc="Returns an autogenerated nonsense string",
                      usage="fnonsense")
    async def autononsense(self, ctx):
        return await self.send(ctx, "nonsense", self.fake.bs())

    @commands.command(aliases=['acp', 'acatch'],
                      desc="Returns an autogenerated catch-phrase",
                      usage="autocatchphrase")
    async def autocatchphrase(self, ctx):
        return await self.send(ctx, "catch phrase", self.fake.catch_phrase())

    @commands.command(aliases=['acompany'],
                      desc="Returns an autogenerated company name",
                      usage="autocompany")
    async def autocompany(self, ctx):
        return await self.send(ctx, "company", self.fake.company())

    @commands.command(aliases=['adate'],
                      desc="Returns an autogenerated date",
                      usage="autodate")
    async def autodate(self, ctx):
        return await self.send(ctx, "date", self.fake.date(pattern="%d/%m/%Y"))

    @commands.command(aliases=['atime'],
                      desc="Returns a random time",
                      usage="autotime")
    async def autotime(self, ctx):
        return await self.send(ctx, "time", self.fake.time())

    @commands.command(aliases=['aday'],
                      desc="Returns an autogenerated day of the month",
                      usage="autoday")
    async def autoday(self, ctx):
        return await self.send(ctx, "day", self.fake.day_of_month())

    @commands.command(aliases=['aweek'],
                      desc="Returns an autogenerated day of the week",
                      usage="autoweek")
    async def autoweek(self, ctx):
        return await self.send(ctx, "day of the week", self.fake.day_of_week())

    @commands.command(aliases=['amonth'],
                      desc="Returns an autogenerated month",
                      usage="automonth")
    async def automonth(self, ctx):
        return await self.send(ctx, "month", self.fake.month_name())

    @commands.command(aliases=['ayear'],
                      desc="Returns an autogenerated year",
                      usage="autoyear")
    async def autoyear(self, ctx):
        return await self.send(ctx, "year", self.fake.year())

    @commands.command(aliases=['aemail'],
                      desc="Returns an autogenerated email address",
                      usage="autoemail (domain)",
                      note="`(domain)` can be a domain ending with an extension, "
                      "if unspecified, defaults to a random domain")
    async def autoemail(self, ctx, *, domain: str = None):
        return await self.send(ctx, "email address", self.fake.email(domain=domain))

    @commands.command(aliases=['aip'],
                      desc="Returns an autogenerated IP address",
                      usage="autoip (version) (class)",
                      note='`(version)` can be either 4 or 6, defaults to 4 if unspecified. '
                      '`(class)` can be either "a", "b", or "c", defaults to random')
    async def autoip(self, ctx, *, options: str = None):
        options = options.split(" ") if options else []
        version = extract(options, "46")
        addr_class = extract(options, "abc", func="lower")
        if not version or version != "6":
            func = self.fake.ipv4(address_class=addr_class)
        else:
            func = self.fake.ipv6()
        return await self.send(ctx, "IP address", func)

    @commands.command(aliases=['amac'],
                      desc="Returns an autogenerated MAC address",
                      usage="automac")
    async def automac(self, ctx):
        return await self.send(ctx, "MAC address", self.fake.mac_address())

    @commands.command(aliases=['aport'],
                      desc="Returns an autogenerated port number",
                      usage="autoport")
    async def autoport(self, ctx):
        return await self.send(ctx, "port", self.fake.port_number())

    @commands.command(aliases=['aisbn'],
                      desc="Returns an autogenerated ISBN",
                      usage="autoisbn (version)",
                      note='`(version)` can be either "10" or "13", defaults to 13 if unspecified')
    async def autoisbn(self, ctx, version: int = None):
        if not version or version == 13:
            func = self.fake.isbn13()
        else:
            func = self.fake.isbn10()
        return await self.send(ctx, "ISBN", func)

    @commands.command(aliases=['ajob'],
                      desc="Retrusn an autogenerated job",
                      usage="autojob")
    async def autojob(self, ctx):
        return await self.send(ctx, "job", self.fake.job())

    @commands.command(aliases=['afn', 'afirstname'],
                      desc="Returns an autogenerated first name",
                      usage="autofirstname")
    async def autofirstname(self, ctx):
        return await self.send(ctx, "first name", self.fake.first_name())

    @commands.command(aliases=['aln', 'alastname'],
                      desc="Returns an autogenerated last name",
                      usage="autolastname")
    async def autolastname(self, ctx):
        return await self.send(ctx, "last name", self.fake.last_name())

    @commands.command(aliases=['an'],
                      desc="Returns an autogenerated full name",
                      usage="autoname")
    async def autoname(self, ctx):
        return await self.send(ctx, "name", self.fake.name())

    @commands.command(aliases=['auagent', 'auseragent', 'ausera'],
                      desc="Returns an autogenerated user agent",
                      usage="autouseragent (platform)",
                      note='`(platform)` can be "android", "chrome", "firefox", "internet explorer" or "ie", '
                      '"ios", "linux", "mac", "opera", "safari", "windows", defaults to random')
    async def autouseragent(self, ctx, platform: str = "random"):
        funcs = {
            "android": self.fake.android_platform_token(),
            "chrome": self.fake.chrome(),
            "firefox": self.fake.firefox(),
            "internet explorer": self.fake.internet_explorer(),
            "ie": self.fake.internet_explorer(),
            "ios": self.fake.ios_platform_token(),
            "linux": self.fake.linux_platform_token(),
            "mac": self.fake.mac_platform_token(),
            "opera": self.fake.opera(),
            "safari": self.fake.safari(),
            "windows": self.fake.windows_platform_token(),
            "random": self.fake.user_agent()
        }
        func = funcs.get(platform.lower(), funcs['random'])
        return await self.send(ctx, "user agent", func)


def setup(bot):
    bot.add_cog(AutoGen(bot))
