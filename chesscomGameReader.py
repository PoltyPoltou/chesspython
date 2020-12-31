
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
        self.gameData = chessdotcom.get_player_games_by_month(
            self.username, year, month)

    def nextGame(self) -> chess.pgn.Game:
        if(len(self.gameData.json["games"]) > self.index):
            pgn = self.gameData.json["games"][self.index]["pgn"]
            self.index += 1
            return chess.pgn.read_game(io.StringIO(pgn))
        else:
            print("Fin des parties")
            return chess.pgn.Game()


if __name__ == "__main__":
    test = ChessComGameReader("PoltyPoltou")
    print(test.nextGame())
