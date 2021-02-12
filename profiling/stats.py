import pstats
import cProfile
import os
import sys
currentdir = os.path.dirname(os.path.realpath(__file__))
parentdir = os.path.dirname(currentdir)
sys.path.append(parentdir)
from main import MyChessApp
cProfile.run(statement='MyChessApp().run()', filename="./profiling/stats.txt")
f = open("./profiling/output.txt", mode="w")
a: pstats.Stats = pstats.Stats("./profiling/stats.txt", stream=f)
a.sort_stats(pstats.SortKey.TIME)
a.reverse_order()
a.print_stats("movelist.py")
a.print_callees("movelist.py")
f.close()
