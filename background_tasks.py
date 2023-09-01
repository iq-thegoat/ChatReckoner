import discord
from discord.ext import commands,tasks
from db import  DbStruct,BotDb
from Config import *
session = BotDb().session
from icecream import ic
class BackgroundTasks(commands.Cog):

    def __init__(self,bot:discord.Client):
        self.bot = bot
        self.check_votes.start()
        self.check_polls.start()
        self.update_users_votes.start()

    def cog_unload(self) -> None:
        self.check_votes.stop()
        self.check_polls.stop()
        self.update_users_votes.stop()

    @tasks.loop(seconds=2)
    async def check_votes(self):
        print("Started. loop")
        results = session.query(DbStruct.member).order_by(DbStruct.member.votes.desc())
        for member in results:
            #["Tier 0","Tier F","Tier 1",'Tier 2','Tier 3']
            if member.votes >= rank_up_level:
                dis_member = self.bot.get_guild(Guild).get_member(member.user_id)
                roles = dis_member.roles
                for role in roles:
                    if role.name in tiers:
                        rank = str(role.name)
                        current_role_index = tiers.index(str(rank))
                        next_role_index    = current_role_index+1
                        if len(tiers) <= next_role_index:
                            pass
                        else:
                            await dis_member.add_roles(discord.utils.get(self.bot.get_guild(Guild).roles, name=str(tiers[next_role_index]))) # Give Next Rank
                            await dis_member.remove_roles(discord.utils.get(self.bot.get_guild(Guild).roles, name=str(tiers[current_role_index]))) # Remove last Rank
                            member.votes -= rank_up_level
                            member.rank = str(tiers[next_role_index])
                            session.commit()

                    else:
                        pass

                session.commit()
            elif member.votes <= -rank_up_level:
                dis_member = self.bot.get_guild(Guild).get_member(member.user_id)
                roles = dis_member.roles
                for role in roles:
                    if role.name in tiers:
                        rank = str(role.name)
                        current_role_index = tiers.index(str(rank))
                        next_role_index = current_role_index - 1
                        if next_role_index < 0:
                            pass
                        else:
                            await dis_member.add_roles(discord.utils.get(self.bot.get_guild(Guild).roles, name=str(
                                tiers[next_role_index])))  # Give lower Rank
                            await dis_member.remove_roles(discord.utils.get(self.bot.get_guild(Guild).roles, name=str(
                                tiers[current_role_index])))  # Remove last Rank
                            member.votes += rank_up_level
                            member.rank = str(tiers[next_role_index])
                            session.commit()

                    else:
                        pass

                session.commit()



    @tasks.loop(seconds=2)
    async def check_polls(self):
        #get all polls
        results = session.query(DbStruct.tierpolls).all()
        for poll in results:
            message = await self.bot.get_guild(Guild).get_channel(tier_submit_channel).fetch_message(poll.id)
            votes = 0
            for reaction in message.reactions:
                ic(reaction.emoji)
                if reaction.emoji == upvote_reaction:
                    votes += reaction.count
                elif reaction.emoji == downvote_reaction:
                    votes -= reaction.count
                else:
                    pass
            poll.votes = votes

            session.commit()

    @tasks.loop(seconds=2)
    async def update_users_votes(self):
        results = session.query(DbStruct.tierpolls).all()
        for poll in results:
            member = session.query(DbStruct.member).filter(DbStruct.member.user_id == poll.voted_user).first()
            if member:
                member.votes -= poll.last_recorded
                member.votes += poll.votes
                poll.last_recorded = poll.votes
            session.commit()



async def setup(bot):
    await bot.add_cog(BackgroundTasks(bot))
