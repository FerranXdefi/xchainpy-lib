from . import MsgCoin
class MsgNativeTx:
    def __init__(self, coins : list[MsgCoin] , memo : str , signer : str):
        self._coins = coins
        self._memo = memo
        self._signer = signer

    @property
    def coins(self):
        return self._coins

    @coins.setter
    def coins(self, coins):
        self._coins = coins

    @property
    def memo(self):
        return self._memo

    @memo.setter
    def memo(self, memo):
        self._memo = memo

    @property
    def signer(self):
        return self._signer

    @signer.setter
    def signer(self, signer):
        self._signer = signer