from xchainpy_util.asset import Asset
from xchainpy_client.models.balance import Balance
from xchainpy_util.chain import THORCHAIN
from xchainpy_client.models import tx_types
import bech32

DECIMAL = 8
DEFAULT_GAS_VALUE = '2000000'

def base_amount(value: str and int, decimal: int = DECIMAL) -> str:
    if type(value) == int:
        return str(value / 10**decimal)
    else:
        return str(int(value) / 10**decimal)

def cnv_big_number(value: float and int and str, decimal: int = DECIMAL) -> str:
    if type(value) == float or type(value) == int:
        return str(round(float(value) * (10**decimal)))
    elif type(value) == str:
        return str(round(float(value) * (10**decimal)))

def getDenomWithChain(asset) -> str :
    return f'THOR.{asset["symbol"].upper()}'

def bech32_fromwords(words):
    res = bech32.convertbits(words,5,8,False)
    if res != None:
        return res
def frombech32(address : str):
    (prefix , words) = bech32.bech32_decode(address)
    res = bech32_fromwords(words)
    return res

    