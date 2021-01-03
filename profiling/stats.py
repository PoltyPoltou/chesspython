import pstats
import cProfile
from main import MyChessApp
cProfile.run(statement='MyChessApp().run()', filename="stats.txt")
f = open("output.txt", mode="w")
a: pstats.Stats = pstats.Stats("stats.txt", stream=f)
a.sort_stats(pstats.SortKey.TIME)
a.reverse_order()
a.print_stats("movelist.py")
a.print_callees("movelist.py")
f.close()
