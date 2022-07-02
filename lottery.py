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
        for i in ['participants', 'prizes']:
            if i not in self.pd:
                self.pd[i]= []
        if 'last_date' not in self.pd:
            self.pd['last_date'] = ''
        self.pd.sync()

    @commands.command()
    async def lottery(self, ctx, *args):
        if args[0] == 'set' and args[1] == 'channel':
            a = self.set_channel(ctx)
        elif args[0] == 'handout':
            if ctx.author.id == self.bot.id4o:
                try:
                    await self.handout(True)
                    a = 'ok. check dedicated channel'
                except Exception as e:
                    print(e)
                    raise
            else:
                a = 'snif snif. nop, you dont smell like 4o'
        elif args[0] == 'add' and args[1] == 'prize':
            a = ''
            for i in args[2:]:
                a += self.add_prize(ctx.author.id, i)+'\n'
        elif args[0] == 'participants':
            a = str(self.pd['participants'])
        elif args[0] == 'prizes':
            a = self.prizes()
        else:
            a = 'invalid command: {}'.format(*args)
        await self.bot.send(ctx, a)

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

    @tasks.loop(hours = 2)
    async def handout(self, force = False):
        try:
            await self._handout(force)
        except Exception as e:
            print(e)
            raise

    async def _handout(self, force):
        self.pd = pd('prizes.json')
        mf = '%Y%m%d'
        if force == False:
            if self.pd['last_date'] == datetime.now().strftime(mf):
                print('no time for handouts', self.pd['last_date'], datetime.now().strftime(mf))
                return
        # pull prize
        print('lottery not forced')
        try:
            prize = self._pull_prize()
        except:
            await self.bot.send(self.pd['channel'], 'no prizes in cookie jar')
            return 'failed to pull a cookie out of a cookie jar. cookie jar may be empty or 4o screwed it up again'
        print('prize:', prize)
        # define a prize winner
        try:
            uid = self._winner(prize[0][0])
        except:
            await self.bot.send(self.pd['channel'], 'failed to define a winner. either nobody was participating, or 4o screwed it up again')
            return 'None'
        print('winner:', uid)
        # clear participants
        print(4)
        # start a task for next prize handout
        msg = 'cookie handout by new bot !!!111 beep boop boop i spy with my robot eye {} gets the prize: `{}`. '.format(self._print_user(uid[0]), prize[0][1])
        msg += '{} please give the promissed cookie immediately\n'.format(self._print_user(prize[0][0]))
        msg += 'participants list is cleared. please send any msg to take part in next round\n'
        msg += 'rnd info: prize {}/{} participant {}/{}\n'.format(prize[2], prize[1], uid[2], uid[1])
        msg += ' current prize list: `{}`'.format(self._print_prizes())
        await self.bot.send(self.pd['channel'], msg)
        self.pd['last_date'] = datetime.now().strftime(mf)
        self._clear_participants()
        self.pd.sync()
        print(5)

    def add_prize(self, uid, prize):
        self.pd['prizes'].append([uid, prize])
        self.pd.sync()
        return 'user {} added {} to prize pool'.format(self._print_user(uid), prize)

    def prizes(self):
        return '`{}`'.format(self._print_prizes())

    def _add_participant(self, uid):
        for i in self.pd['participants']:
            if i == uid:
                return False
        self.pd['participants'].append(uid)
        self.pd.sync()
        return True

    def _winner(self, exclude):
        n = len(self.pd['participants'])
        rnd = self._rnd(n)
        ret = self.pd['participants'][rnd]
        if ret == exclude:
            raise Exception()
        return (ret, n, rnd)

    def _clear_participants(self):
        self.pd['participants'] = []
        self.pd.sync()

    def _pull_prize(self):
        n = len(self.pd['prizes'])
        if n == 0:
            raise Exception()
        rnd = self._rnd(n)
        p = self.pd['prizes'].pop(rnd)
        return (p, n, rnd)

    def _rnd(self, n):
        import random
        return random.randrange(n)

    def _print_prizes(self):
        return str([x[1] for x in self.pd['prizes']])

    def _print_user(self, uid):
        return '<@' + str(uid) + '>'
