import discord
from discord.ui import InputText, Modal
from discord.ext import commands
from fuzzywuzzy import process


quotes = []


def new_quote(text, author):
    final_quote = f"> {text}\n> - **{author}**"
    quotes.append(final_quote)


class QuoteModal(Modal):
    def __init__(self, author, text, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.add_item(
            InputText(
                label="Quote",
                value=text,
                style=discord.InputTextStyle.long,
            )
        )
        self.add_item(InputText(label="Author", value=author))

    async def callback(self, interaction: discord.Interaction):
        embed = discord.Embed(title="Your Modal Results",
                              color=discord.Color.random())
        embed.add_field(name="First Input",
                        value=self.children[0].value, inline=False)
        embed.add_field(name="Second Input",
                        value=self.children[1].value, inline=False)
        await interaction.response.send_message(embeds=[embed], ephemeral=True)
        new_quote(self.children[0].value, self.children[1].value)


# TODO separate for servers
class QuoteCog(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.create_quotes()

    @discord.slash_command(name="quote-add")
    async def quote_add(self, ctx, text: str, author: str):
        """Adds a new quote to the list"""
        if text is None or author is None:
            await ctx.respond("Uncompleted Command!", ephemeral=True)
            return 0
        final_quote = f"> {text}\n> - **{author}**"
        await ctx.respond(f"Added quote\n{final_quote}", ephemeral=True)
        quotes.append(final_quote)
        await self.write_file()

    @discord.slash_command()
    async def quote(self, ctx, search: str):
        """Returns the best matching Quote"""
        match = process.extractOne(search, quotes)
        await ctx.respond(match[0])

    @discord.slash_command(name="quote-list")
    async def quote_list(self, ctx, search: str):
        """Shows all matching quotes"""
        match = process.extract(search, quotes)
        result = "\n\n".join([element[0] for element in match])
        await ctx.respond("All results:\n" + result)

    @discord.message_command(name="Turn into quote")
    async def turn_into_quote(self, ctx: discord.commands.context.ApplicationContext, message: discord.Message):
        await ctx.send_modal(QuoteModal(title="Create a new Quote", author=message.author.display_name, text=message.content))

    # If ping -> then ping as default value
    # else author as default value
    # @discord.message_command() hidden because old

    async def make_quote(self, ctx: discord.commands.context.ApplicationContext, message: discord.Message):
        def check(m):
            return m.author == ctx.author and m.channel == ctx.channel

        first = await ctx.respond("Who is the author?")
        author = await discord.wait_for('message', check=check, timeout=60)
        quotes.append(f"> {message.content}\n> - **{author.content}**")
        await message.channel.delete_messages([author])
        await first.delete_original_message()
        await self.write_file()

    def create_quotes(self):
        quotes.clear()
        with open("quotes.csv", 'r', encoding="utf-8") as file:
            for row in file.readlines():
                quotes.append(row.replace("\n", "").replace("\\n", "\n"))
                # rewrite to strip last two characters and handle multi line quites

    async def write_file(self):
        text = "\n".join([row.replace("\n", "\\n") for row in quotes])
        with open("quotes.csv", 'w', newline="", encoding="utf_8") as file:
            file.write(text)
