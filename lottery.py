import random
import traceback
import queue
from discord.ext import commands, tasks
from discord.utils import get
from datetime import datetime
from pd import pd


async def setup(bot):
    l = lottery(bot)
    await bot.add_cog(l)
    l.handout.start()
    l.delete_msgs.start()


guid = 871762312208474133
uid4o = 139179662369751041

class lottery(commands.Cog):
    def __init__(self, bot):
        print('lottery module loaded')
        self.bot = bot
        self.pd = pd('prizes.json')
        for i in ['participants', 'prizes']:
            if i not in self.pd:
                print('resetting {} in ctor'.format(i))
                self.pd[i]= []
        if 'channel' not in self.pd:
            print('setting channel to none')
            self.pd['channel'] = None
        if 'last_date' not in self.pd:
            print('resetting last date')
            self.pd['last_date'] = ''
        self.pd.sync()
        hugs = open('hugs.txt').read()
        self.hugs = [x for x in hugs.split('\n\n') if x != '']
        self.q = queue.Queue()
        self.msg_to_delete = None

    @commands.command()
    async def lottery(self, ctx, *args):
        if args[0] == 'set' and args[1] == 'channel':
            a = self.set_channel(ctx)
        elif args[0] == 'hugs':
            a = '```\n' + str(self._hugs()) + '```'
        elif args[0] == 'print':
            a = str({k: v for k,v in self.pd.items() if k != 'bribe'})
        elif args[0] == 'bribe':
            if ctx.channel.id != 875942917489983508:
                await ctx.send('please, use #bot-spam channel for bribes')
                return
            nl = 50
            if 'bribe' not in self.pd:
                self.pd['bribe'] = random.randrange(nl)
                self.pd.sync()
            if len(args) == 1:
                a = 'gimme that number. like `.lottery bribe 12` or whatever number you have'
            else:
                try:
                    num = int(args[1])
                    if num == self.pd['bribe']:
                        self.pd['bribe'] = random.randrange(nl)
                        self.pd['participants'].append(ctx.author.id)
                        self.pd.sync()
                        a = 'woohoo, just what i wanted'
                    else:
                        a = f'nop, dont like that number. try nymbers 0-{nl-1}'
                except:
                    a = 'thats not a number'
        elif args[0] == 'handout':
            if ctx.author.id == self.bot.id4o:
                try:
                    await self.handout(True)
                except Exception as e:
                    self.pd._dict = bckup
                    self.pd.sync()
                    print('new', self.pd)
                    raise
                a = 'ok. check dedicated channel'
            else:
                a = 'snif snif. nop, you dont smell like 4o'
        elif args[0] == 'add' and args[1] == 'prize':
            await ctx.send('youre about to add prize(s) to the cookie jar')
            a = ''
            dry = False
            if args[-1] == '--dry':
                args = args[:-1]
                dry = True
            for i in args[2:]:
                if not dry:
                    self.pd['prizes'].append([ctx.author.id, i])
                    self.pd.sync()
                a += 'user {} added {} to prize pool\n'.format(self._print_user(ctx.author.id), i)
                if dry:
                    a += 'no prizes were added due to --dry option\n'
        elif args[0] == 'participants':
            a = str(self.pd['participants'])
        elif args[0] == 'prizes':
            a = str([x[1] for x in self.pd['prizes']])
        else:
            a = 'invalid command: {}'.format(*args)
        await self.bot.send(ctx, a)

    def set_channel(self, ctx):
        self.pd['channel'] = ctx.channel.id
        self.pd.sync()
        return 'lottery channel set'
        
    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot:
            return

        member = message.author

        role = get(member.guild.roles, name='corp member')
        
        if role not in member.roles:
            return

        if message.guild:
            if message.guild.id == guid:
                if self._add_participant(message.author.id):
                    msg = "user {} takes part in this week's lottery ({} participants so far)".format(self._print_user(message.author.id), len(self.pd['participants']))
                    self.q.put(await message.channel.send(msg))

    def cog_unload(self):
        print('killing lottery cog')
        self.handout.cancel()

    @tasks.loop(seconds = 5)
    async def delete_msgs(self):
        try:
            await self.msg_to_delete.delete()
            self.msg_to_delete = None
        except Exception as e:
            pass
        try:
            msg = self.q.get(block = False)
            self.msg_to_delete = msg
        except:
            pass

    @tasks.loop(hours = 4)
    async def handout(self, force = False):
        try:
            await self._handout(force)
        except Exception as e:
            print(e)

    async def _handout(self, force):
        mf = '%Y%m%d'
        if force == False:
            if self.pd['last_date'] == datetime.now().strftime(mf):
                print('last date check failed')
                return
        if len(self.pd['prizes']) == 0:
            await self.bot.send(self.pd['channel'], 'cookie jar empty. say`.lottery add prize <prize>` to add prize')
#            await self.bot.send(self.pd['channel'], f'no prizes <@{uid4o}>. adding default set')
#            self.pd['prizes'].append([uid4o, 't8ticket'])
#            self.pd['prizes'].append([uid4o, 't8ticket'])
#            self.pd['prizes'].append([uid4o, 'hugs'])
#            self.pd['prizes'].append([uid4o, 'hugs'])
#            self.pd['prizes'].append([uid4o, 'hugs'])
#            self.pd['prizes'].append([uid4o, 'hugs'])
#            self.pd['prizes'].append([uid4o, 'hugs'])
        wn = len(self.pd['participants'])
        if wn == 0:
            print('nobody participate. sadly')
            return
        rnd_w = random.randrange(wn)
        w = self.pd['participants'][rnd_w]
        if w in [743638088080687224, 276102320708648960]:
            return
        pl = [x for x in self.pd['prizes'] if x[0] != w]
        pn = len(pl)
        if pn == 0:
            print('no cookies for winner ', self._print_user(w), '. total cookies: ', len(self.pd['prizes']))
            return
        rnd_p = random.randrange(pn)
        p = pl[rnd_p]
        print('prize: ', p[1])
        msg = 'cookie handout by new bot !!!111 beep boop boop i spy with my robot eye {} gets the prize: `{}`. '.format(self._print_user(w), p[1])
        msg += '{} please give the promissed cookie immediately\n'.format(self._print_user(p[0]))
        msg += 'participants list is cleared. please send any msg to take part in next round\n'
        msg += 'rnd info: prize {}/{} participant {}/{}\n'.format(rnd_p, pn, rnd_w, wn)
        if p[1].startswith('hugs'):
            msg += f'```\n{self._hugs()}```'
        await self.bot.send(self.pd['channel'], msg)
        print('cleaning up')
        print('upating date')
        self.pd['last_date'] = datetime.now().strftime(mf)
        print('removing prize')
        self.pd['prizes'].remove(p)
        print('clearing participants')
        self.pd['participants'] = []
        print('updating json')
        self.pd.sync()
        print('handout commenced')

    def _add_participant(self, uid):
        for i in self.pd['participants']:
            if i == uid:
                return False
        self.pd['participants'].append(uid)
        self.pd.sync()
        return True

    def _print_user(self, uid):
        return '<@' + str(uid) + '>'

    def _hugs(self):
        n = len(self.hugs)
        rnd_p = random.randrange(n)
        return self.hugs[rnd_p]


