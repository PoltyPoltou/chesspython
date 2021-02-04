from analysis import MoveQuality
from io import StringIO
import os
import pickle
import chess.pgn


class GameAndAnalysisStorage:
    def __init__(self, usrname) -> None:
        self.storageDict: dict[chess.pgn.Game,
                               dict[chess.pgn.GameNode, MoveQuality]] = {}
        self.username = usrname

    def __contains__(self, elem):
        return elem in self.storageDict.keys()


def loadGamesFromDisk(username: str) -> GameAndAnalysisStorage:
    if(os.path.exists("data/" + username + ".pickle")):
        file = open("data/" + username + ".pickle", "rb")
        result = pickle.load(file)
        file.close()
        file = open("data/lastdata.txt", "w")
        file.write(username)
        file.close()
        # compatibility issue with stored infos, we must add
        # the theoric attribute to every MoveQuality object
        for lst_quality in result.storageDict.values():
            for q in lst_quality.values():
                if(not hasattr(q, "theoric")):
                    q.theoric = False
        return result
    else:
        return GameAndAnalysisStorage(username)


def saveGamesToDisk(data: GameAndAnalysisStorage) -> None:
    file = open("data/" + data.username + ".pickle", "wb")
    pickle.dump(data, file)
    file.close()


def loadLastSavedData() -> GameAndAnalysisStorage:
    file = open("data/lastdata.txt", "r")
    usr = file.read()
    file.close()
    return loadGamesFromDisk(usr)
