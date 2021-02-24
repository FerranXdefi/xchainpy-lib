from xchainpy.xchainpy_util.asset import Asset
from xchainpy.xchainpy_client.models.balance import Balance
from xchainpy.xchainpy_util.chain import THORCHAIN
from xchainpy.xchainpy_client.models import tx_types

DECIMAL = 8
DEFAULT_GAS_VALUE = '10000000'

def base_amount(value: str and int, decimal: int = DECIMAL) -> str:
    if type(value) == int:
        return str(value / 10**decimal)
    else:
        return str(int(value) / 10**decimal)