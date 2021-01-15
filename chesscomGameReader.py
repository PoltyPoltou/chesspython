
import datetime as dt
import io
import chessdotcom
import chess.pgn


class ChessComGameReader():
    def __init__(self, username: str) -> None:
        self.username = username
        self.setDate(dt.datetime.now().month, dt.datetime.now().year)
        self.index = 0

    def setDate(self, month: int, year: int):
        try:
            self.gameData = chessdotcom.get_player_games_by_month(
                self.username, year, month)
        except chessdotcom.ChessDotComError as error:
            self.gameData = None

    def nextGame(self) -> chess.pgn.Game:
        if(self.gameData is not None):
            while(len(self.gameData.json["games"]) > self.index and "pgn" not in self.gameData.json["games"][self.index]):
                self.index += 1
            if(len(self.gameData.json["games"]) > self.index):
                pgn = self.gameData.json["games"][self.index]["pgn"]
                self.index += 1
                return chess.pgn.read_game(io.StringIO(pgn))
            else:
                return None
        else:
            return None


def printGameInfo(game):
    print(game.headers["Date"], " - ", game.headers["StartTime"],
          " - ", game.headers["White"], " - ", game.headers["Black"])


if __name__ == "__main__":
    test = ChessComGameReader("PoltyPoltou")
    curGame = test.nextGame()
    while curGame is not None:
        printGameInfo(curGame)
        curGame = test.nextGame()
