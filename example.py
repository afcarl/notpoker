from pokerbots.engine.game import Table
from pokerbots.player.pokerbot import Pokerbot
import time

# need to create a module name botname.botname containing the correct code.
# it's hardcoded sadly
p1 = Pokerbot('vivekbot')
p2 = Pokerbot('vivekbot')

num_matches = 100

for i in range(num_matches):
    t = Table(p1, p2)
    t.play_match()
