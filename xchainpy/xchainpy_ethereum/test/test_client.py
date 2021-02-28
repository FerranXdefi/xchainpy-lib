import pytest
from xchainpy.xchainpy_ethereum.client import Client
import time, json

class TestClient:
    prefix = "resources/ropsten/"
    mnemonic = open(prefix + "mnemonic", 'r').readline()
    router_abi = json.loads(open(prefix + "router_abi", 'r').readline())
    token_abi = json.loads(open(prefix + "token_abi", 'r').readline())
    network = open(prefix + "network", 'r').readline()
    eth_api = open("resources/ether_api", 'r').readline()
    thor_router_address = "0x9d496De78837f5a2bA64Cb40E62c19FBcB67f55a"
    thor_token_address = "0xd601c6A3a36721320573885A8d8420746dA3d7A0"
    client = Client(mnemonic, network, "ropsten", eth_api)
    client_address = "0x0dC1Ce70a8ddFA3F2070984C35010a285CF0530D"
    test_hash = "0x7aa171c7c024cbfdcf6e8097fbd8ec18bacf33581acdea0d3923c031a55b931e"
    test_rune_transfer_hash = "0xa23a19ec29fbc0edc245befe80bda6a29def5b3b4610bf20b670d9e90bfa8095"

    def test_is_connected(self):
        assert self.client.is_connected()

    def test_set_network(self):
        self.client.set_network(network=self.network)
        assert self.client.is_connected()

    def test_get_network(self):
        assert self.client.get_network() == self.network

    def test_validate_address(self):
        assert self.client.validate_address(self.client_address)
        assert self.client.validate_address(self.thor_router_address)
        assert self.client.validate_address(self.thor_token_address)

    def test_get_address(self):
        assert self.client.get_address() == self.client_address

    def test_set_phrase(self):
        assert self.client.set_phrase(self.mnemonic) == self.client_address
        assert self.client.is_connected()

    def test_get_abi(self):
        assert str(self.client.get_abi(self.thor_router_address)) == str(self.router_abi)
        assert str(self.client.get_abi(self.thor_token_address)) == str(self.token_abi)
        self.client.ether_api = None
        assert str(self.client.get_abi(self.thor_router_address)) == str(self.router_abi)
        assert str(self.client.get_abi(self.thor_token_address)) == str(self.token_abi)

    def test_get_contract(self):
        router_contract = self.client.get_contract(self.thor_router_address, erc20=False)
        assert router_contract.functions.RUNE().call() == self.thor_token_address
        token_contract = self.client.get_contract(self.thor_token_address, erc20=True)
        decimal_place = token_contract.functions.decimals().call()
        assert token_contract.functions.symbol().call() == 'RUNE'
        token_contract = self.client.get_contract(self.thor_token_address, erc20=False)
        assert token_contract.functions.maxSupply().call()/10**decimal_place == 500000000.0

    def test_read_contract(self):
        assert self.client.read_contract(self.thor_router_address, "RUNE", False) == self.thor_token_address

    def test_get_balance(self):
        balance = self.client.get_balance()
        balance_address = self.client.get_balance(address=self.client_address)
        assert balance == balance_address
        rune_balance = self.client.get_balance(contract_address=self.thor_token_address)
        rune_balance_address = self.client.get_balance(address=self.client_address,
                                                       contract_address=self.thor_token_address)
        assert rune_balance == rune_balance_address

    def test_get_fees(self):
        self.client.set_gas_strategy("fast")
        fast_fee = self.client.get_fees()
        self.client.set_gas_strategy("medium")
        medium_fee = self.client.get_fees()
        self.client.set_gas_strategy("slow")
        slow_fee = self.client.get_fees()
        assert fast_fee >= medium_fee >= slow_fee

    def test_get_transaction_data(self):
        data = self.client.get_transaction_data(self.test_hash)
        tx_hash = self.client.w3.toHex(data["hash"])
        from_addr = data["from"]
        value = data["value"]
        assert tx_hash == self.test_hash
        assert from_addr == self.client_address
        assert self.client.w3.fromWei(value, 'ether') == 3

    def test_get_transaction_receipt(self):
        data = self.client.get_transaction_receipt(self.test_rune_transfer_hash)
        value = data['logs'][0]['data']
        amount = self.client.w3.toInt(hexstr=value)
        assert amount/10**18 == 1

    def test_transfer_ethereum(self):
        self.client.set_gas_strategy("fast")
        assert self.client.get_balance() > 0.0001
        tx_hash = self.client.transfer('0x81941E3DeEeA41b6309045ECbAFd919Db5aF6147', 0.0001)
        data = self.client.get_transaction_data(tx_hash)
        assert float(self.client.w3.fromWei(data["value"], 'ether')) == 0.0001

    def test_transfer_rune(self):
        self.client.set_gas_strategy("fast")
        dest_addr = self.client.w3.toChecksumAddress('0x5039c76445efcfa78d91b8974c100151634cbf2d')
        rune_balance = self.client.get_balance(contract_address=self.thor_token_address)
        assert rune_balance > 1
        receipt = self.client.transfer(dest_addr, 1, contract_address=self.thor_token_address)
        value = receipt['logs'][0]['data']
        amount = self.client.w3.toInt(hexstr=value)
        assert amount/10**18 == 1

    def test_write_contract(self):
        old_balance = self.client.get_balance(contract_address=self.thor_token_address)
        func_to_call = "giveMeRUNE"
        self.client.set_gas_strategy("fast")
        tx_receipt = self.client.write_contract(self.thor_token_address, func_to_call, erc20=False)
        new_balance = self.client.get_balance(contract_address=self.thor_token_address)
        assert new_balance > old_balance
