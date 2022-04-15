import logging
import random
from MusicCog import Music

import discord
from discord.ext import commands
from QuoteCog import QuoteCog
from discord.ext.pages import Paginator, Page

intents = discord.Intents.default()
bot = commands.Bot(command_prefix='!', debug_guilds=[
    708765604471111751, 962419994308771900], intents=intents)


class DeleteView(discord.ui.View):
    @discord.ui.button(label="Delete", style=discord.ButtonStyle.danger)
    async def button_callback(self, button, interaction):
        # so ugly
        await interaction.channel.delete_messages([interaction.message])
        # await interaction.delete_original_message()


@bot.slash_command()
async def new_help(ctx):
    my_pages = [
        Page(
            embeds=[
                discord.Embed(title="Quotes").add_field(name="Quotes",
                                                        value="- **/quote:** searches the best fitting quote" +
                                                              "\n- **/quote-list:** lists all fitting quotes" +
                                                              "\n- **/quote-add:** adds a new Quote with given text and author" +
                                                              "\n- **Right-Click** messages to turn them into a quote",
                                                        inline=False)

            ],
        ),
        Page(
            content="This is my second page. It only has message content.",
        ),
        Page(
            embeds=[
                discord.Embed(
                    title="This is my third page.",
                    description="It has no message content, and one embed.",
                )
            ],
        ),
    ]
    paginator = Paginator(pages=my_pages, author_check=False)
    await paginator.respond(ctx.interaction)


@bot.slash_command()
async def help(ctx):
    embed = discord.Embed(
        title="Helpful message goes here",
        description="A short description of all commands.",
        color=discord.Colour.purple(),
    )
    embed.add_field(name="Valorant",
                    value="- **/valorant-Agent:** chooses a random Valorant Agent" +
                          "\n- **/valorant-role:** chooses a random Valorant role",
                    inline=False)
    embed.add_field(name="Quotes",
                    value="- **/quote:** searches the best fitting quote" +
                          "\n- **/quote-list:** lists all fitting quotes" +
                          "\n- **/quote-add:** adds a new Quote with given text and author" +
                          "\n- **Right-Click** messages to turn them into a quote", inline=False)
    await ctx.respond("", view=DeleteView(), embed=embed)


# region Valorant
agent_list = ["Astra", "Breach", "Brimstone", "Chamber", "Cypher", "Jett", "KAY/O", "Killjoy", "Neon", "Omen",
              "Phoenix", "Raze", "Reyna", "Sage", "Skye", "Sova", "Viper", "Yoru"]
role_list = ["Controller", "Duelist", "Initiator", "Sentinel"]


class RerollView(DeleteView):
    @discord.ui.button(label="Reroll", style=discord.ButtonStyle.primary)
    async def button_callback(self, button, interaction):
        # TODO ensure the same option isn't given again
        await interaction.message.edit(content=f"Your random Agent is: **{random.choice(agent_list)}**")


@bot.slash_command(name="valorant-agent", description="Chooses a random Valorant agent")
async def valorant_agent(ctx):
    await ctx.respond(f"Your random Agent is: **{random.choice(agent_list)}**", view=RerollView())


# TODO combine buttons into one

class RerollViewRole(DeleteView):
    @discord.ui.button(label="Reroll", style=discord.ButtonStyle.primary)
    async def button_callback(self, button, interaction):
        # TODO ensure the same option isn't given again
        await interaction.message.edit(content=f"Your random role is: **{random.choice(role_list)}**")


@bot.slash_command(name="valorant-role", description="Chooses a random Valorant role")
async def valorant_role(ctx):
    await ctx.respond(f"Your random role is: **{random.choice(role_list)}**", view=RerollViewRole())


# endregion


# region Music

@bot.slash_command()
async def play_old(ctx, song: str):
    # check if song is link or search youtube for string
    author_voice = ctx.author.voice.channel
    if author_voice is None:
        await ctx.respond(f"You arent in any voice-channel")
    if ctx.voice_client is None:
        await author_voice.connect()
    else:
        await ctx.voice_client.move_to(author_voice)
    await ctx.respond(f"{song} is playing")


@bot.slash_command()
async def leave(ctx):
    print(type(ctx))
    await ctx.respond("leaving", delete_after=0)
    await ctx.voice_client.disconnect()


# endregion


# region Events
@bot.event
async def on_ready():
    print(f"{bot.user} is ready and online!")


# endregion


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    bot.add_cog(QuoteCog(bot))
    bot.add_cog(Music(bot))
    bot.run(open("discordCredentials.json").read())
