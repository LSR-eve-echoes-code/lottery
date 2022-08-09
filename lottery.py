import random
from discord.ext import commands, tasks
from datetime import datetime
from pd import pd


def setup(bot):
    l = lottery(bot)
    bot.add_cog(l)
    l.handout.start()


guid = 871762312208474133
uid4o = 139179662369751041

class lottery(commands.Cog):
    def __init__(self, bot):
        print('lottery module loaded')
        self.bot = bot
        self.pd = pd('prizes.json')
        print(self.pd)
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

    @commands.command()
    async def lottery(self, ctx, *args):
        print('old', self.pd)
        if args[0] == 'set' and args[1] == 'channel':
            a = self.set_channel(ctx)
        elif args[0] == 'print':
            a = str(self.pd)
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
            a = ''
            for i in args[2:]:
                self.pd['prizes'].append([ctx.author.id, i])
                self.pd.sync()
                a += 'user {} added {} to prize pool'.format(self._print_user(ctx.author.id), i)
        elif args[0] == 'participants':
            a = str(self.pd['participants'])
        elif args[0] == 'prizes':
            a = str([x[1] for x in self.pd['prizes']])
        else:
            a = 'invalid command: {}'.format(*args)
        await self.bot.send(ctx, a)
        print('new', self.pd)

    def set_channel(self, ctx):
        self.pd['channel'] = ctx.channel.id
        self.pd.sync()
        return 'lottery channel set'
        
    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot == False:
            if message.guild.id == guid:
                if self._add_participant(message.author.id):
                    msg = "user {} takes part in this week's lottery ({} participants so far)".format(self._print_user(message.author.id), len(self.pd['participants']))
                    await self.bot.send(message.channel.id, msg)

    def cog_unload(self):
        self.handout.cancel()

    @tasks.loop(hours = 4)
    async def handout(self, force = False):
        print('old: ', self.pd)
        try:
            await self._handout(force)
        except Exception as e:
            print(e)
        print('new: ', self.pd)

    async def _handout(self, force):
        mf = '%Y%m%d'
        if force == False:
            if self.pd['last_date'] == datetime.now().strftime(mf):
                print('no time for handouts', self.pd['last_date'], datetime.now().strftime(mf))
                return
        print('pulling winner from list')
        wn = len(self.pd['participants'])
        if wn == 0:
            print('nobody participate. sadly')
            return
        rnd_w = random.randrange(wn)
        w = self.pd['participants'][rnd_w]
        print('winner:', w)
        print('pulling prize from list')
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
