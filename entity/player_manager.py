from .player import Player
from utils.singleton import Singleton
from utils.log import logger


@Singleton
class PlayerManager:
    def __init__(self):
        self._players = dict()
        self.player_factory = None

    def set_factory(self, factory):
        self.player_factory = factory

    def get_player(self, uid):
        if uid not in self._players:
            return None
        return self._players[uid]

    def get_or_new_player(self, uid):
        player = self.get_player(uid)
        if player is None:
            player = self.player_factory(uid)
            self._add_player(player)
        return player

    def _add_player(self, player: Player):
        uid = player.get_uid()
        if uid in self._players:
            logger.error("PlayerManager.add_player, Player:%s is not None" % uid)
        self._players[uid] = player

    def remove_player(self, uid):
        del self._players[uid]

    def count(self):
        return len(self._players)

    def map(self, fn):
        for k, v in self._players:
            fn(k, v)
