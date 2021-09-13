import pytest
from xchainpy_ethereum.client import Client
from xchainpy_ethereum.models.asset import Asset
from xchainpy_ethereum.models.client_types import EthereumClientParams
import json, os, time


ETH_RUNE = Asset("ETH", "RUNE", contract="0xd601c6A3a36721320573885A8d8420746dA3d7A0")
ETH_ETH = Asset("ETH", "ETH")


class TestClient:
    # initialization of parameters for xchainpy_etheruem client
    prefix = "../xchainpy_ethereum/resources/testnet/"
    mnemonic = open(prefix + "mnemonic", 'r').readline()
    # web3 websocket provider is needed, e.g. infura
    wss = open(prefix + "infura", 'r').readline()
    # etherscan api is needed if there's intention to interact with non ERC20 token
    # the client will fetch abi for specific contract
    eth_api = open("../xchainpy_ethereum/resources/ether_api", 'r').readline()
    params = EthereumClientParams(wss_provider=wss, etherscan_token=eth_api, phrase=mnemonic)

    router_abi = json.loads(open(prefix + "router_abi", 'r').readline())
    token_abi = json.loads(open(prefix + "token_abi", 'r').readline())
    test_address = "0x0dC1Ce70a8ddFA3F2070984C35010a285CF0530D"
    test_hash = "0x7aa171c7c024cbfdcf6e8097fbd8ec18bacf33581acdea0d3923c031a55b931e"
    test_rune_transfer_hash = "0xa23a19ec29fbc0edc245befe80bda6a29def5b3b4610bf20b670d9e90bfa8095"

    # the router address changes on every churn
    thor_router_address = "0x9d496De78837f5a2bA64Cb40E62c19FBcB67f55a"

    @pytest.fixture
    def test_init(self):
        self.client = Client(params=self.params)
        yield
        self.client.purge_client()

    def test_init_param(self):
        with pytest.raises(Exception) as err:
            EthereumClientParams(wss_provider=self.wss, etherscan_token=self.eth_api,
                                 phrase=self.mnemonic, network="invalid")
        assert str(err.value) == "Invalid network"

    def test_init_client(self):
        test_params = EthereumClientParams(wss_provider=self.wss, etherscan_token=self.eth_api, phrase="invalid")
        with pytest.raises(Exception) as err:
            Client(test_params)
        assert str(err.value) == "invalid phrase"

    def test_set_phrase(self, test_init):
        with pytest.raises(Exception) as err:
            self.client.set_phrase(phrase="invalid")
        assert str(err.value) == "invalid phrase"

    def test_web3_provider_connection(self, test_init):
        assert self.client.is_web3_connected()
        test_params = EthereumClientParams(wss_provider="wss://testnet.network.io/ws/v3/invalid",
                                           etherscan_token=self.eth_api, phrase=self.mnemonic)
        with pytest.raises(Exception) as err:
            Client(test_params)
        with pytest.raises(Exception) as err:
            assert self.client.set_wss_provider(wss_provider="wss://testnet.network.io/ws/v3/invalid")
        self.client.set_wss_provider(wss_provider=self.wss)
        assert self.client.is_web3_connected()

    def test_validate_address(self, test_init):
        assert self.client.validate_address(self.test_address)
        assert self.client.validate_address(self.thor_router_address)
        assert self.client.validate_address(ETH_RUNE.contract)

    def test_get_address(self, test_init):
        assert self.client.get_address() == self.test_address

    @pytest.mark.asyncio
    async def test_get_abi(self, test_init):
        res = await self.client.thornode_api_get("/inbound_addresses")
        self.thor_router_address = next(filter(lambda x: x['chain'] == self.client.chain, res), None)["router"]
        if os.path.exists(self.prefix + ETH_RUNE.contract):
            os.remove(self.prefix + ETH_RUNE.contract)
        if os.path.exists(self.prefix + self.thor_router_address):
            os.remove(self.prefix + self.thor_router_address)

        assert str(await self.client.get_abi(self.thor_router_address)) == str(self.router_abi)
        assert str(await self.client.get_abi(ETH_RUNE.contract)) == str(self.token_abi)
        self.client.ether_api = None
        assert str(await self.client.get_abi(self.thor_router_address)) == str(self.router_abi)
        assert str(await self.client.get_abi(ETH_RUNE.contract)) == str(self.token_abi)

    @pytest.mark.asyncio
    async def test_get_contract(self, test_init):
        res = await self.client.thornode_api_get("/inbound_addresses")
        self.thor_router_address = next(filter(lambda x: x['chain'] == self.client.chain, res), None)["router"]
        router_contract = await self.client.get_contract(self.thor_router_address, erc20=False)
        assert router_contract.functions.RUNE().call() == ETH_RUNE.contract
        token_contract = await self.client.get_contract(ETH_RUNE.contract, erc20=True)
        assert token_contract.functions.symbol().call() == 'RUNE'
        token_contract = await self.client.get_contract(ETH_RUNE.contract, erc20=False)
        decimal_place = token_contract.functions.decimals().call()
        assert token_contract.functions.maxSupply().call()/10**decimal_place == 500000000.0

    @pytest.mark.asyncio
    async def test_get_balance(self, test_init):
        balance = await self.client.get_balance()
        balance_address = await self.client.get_balance(address=self.test_address)
        assert balance == balance_address
        rune_balance = await self.client.get_balance(asset=ETH_RUNE)
        rune_balance_address = await self.client.get_balance(address=self.test_address,
                                                       asset=ETH_RUNE)
        assert rune_balance == rune_balance_address

    def test_get_fees(self, test_init):
        self.client.set_gas_strategy("fast")
        fast_fee = self.client.get_fees()
        self.client.set_gas_strategy("medium")
        medium_fee = self.client.get_fees()
        self.client.set_gas_strategy("slow")
        slow_fee = self.client.get_fees()
        assert fast_fee >= medium_fee >= slow_fee

    def test_get_transaction_data(self, test_init):
        data = self.client.get_transaction_data(self.test_hash)
        tx_hash = self.client.w3.toHex(data["hash"])
        from_addr = data["from"]
        value = data["value"]
        assert tx_hash == self.test_hash
        assert from_addr == self.test_address
        assert self.client.w3.fromWei(value, 'ether') == 3

    def test_get_transaction_receipt(self, test_init):
        data = self.client.get_transaction_receipt(self.test_rune_transfer_hash)
        value = data['logs'][0]['data']
        amount = self.client.w3.toInt(hexstr=value)
        assert amount/10**18 == 1

    @pytest.mark.asyncio
    async def test_transfer_rune(self, test_init):
        self.client.set_gas_strategy("fast")
        dest_addr = self.client.w3.toChecksumAddress('0x81941E3DeEeA41b6309045ECbAFd919Db5aF6147')
        rune_balance = await self.client.get_balance(asset=ETH_RUNE)
        assert rune_balance > 1
        receipt = await self.client.transfer(asset=ETH_RUNE, amount=1, recipient=dest_addr)
        value = receipt['logs'][0]['data']
        amount = self.client.w3.toInt(hexstr=value)
        assert amount/10**18 == 1

    @pytest.mark.asyncio
    async def test_transfer_ethereum(self, test_init):
        self.client.set_gas_strategy("fast")
        assert await self.client.get_balance() > 0.0001
        tx_hash = await self.client.transfer(asset=ETH_ETH, amount=0.0001, recipient='0x81941E3DeEeA41b6309045ECbAFd919Db5aF6147')
        data = self.client.get_transaction_data(tx_hash)
        assert float(self.client.w3.fromWei(data["value"], 'ether')) == 0.0001

    @pytest.mark.asyncio
    async def test_read_contract(self, test_init):
        res = await self.client.thornode_api_get("/inbound_addresses")
        self.thor_router_address = next(filter(lambda x: x['chain'] == self.client.chain, res), None)["router"]
        assert await self.client.read_contract(ETH_RUNE.contract, "balanceOf", self.client.get_address()) / 10**18 \
               == await self.client.get_balance(asset=ETH_RUNE)
        assert await self.client.read_contract(self.thor_router_address, "RUNE", erc20=False) == ETH_RUNE.contract

    @pytest.mark.asyncio
    async def test_write_contract_token(self, test_init):
        old_balance = await self.client.get_balance(asset=ETH_RUNE)
        func_to_call = "giveMeRUNE"
        self.client.gas_price = self.client.w3.toWei(10, 'gwei')
        tx_receipt = await self.client.write_contract(ETH_RUNE.contract, func_to_call, erc20=False)
        new_balance = await self.client.get_balance(asset=ETH_RUNE)
        time.sleep(1)
        assert new_balance > old_balance

    @pytest.mark.asyncio
    async def test_write_contract_router(self, test_init):
        """write to rune router: deposit() with memo for switching eth.rune to thor.rune"""
        old_balance = await self.client.get_balance(asset=ETH_RUNE)
        func_to_call = "deposit"
        asgard_address = self.client.w3.toChecksumAddress("0x8d6690d9068e0da603ada9c26d475f19b1d56c91")
        amount = 10*10**18
        assert old_balance > 10
        memo = "switch:tthor1vecuqg5tejlxncykw6dfkj6hgkv49d59lc0z6j"
        router = await self.client.get_contract(contract_address=self.thor_router_address, erc20=False)
        self.client.gas_price = self.client.w3.toWei(10, 'gwei')
        # <Function deposit(address,address,uint256,string)>
        tx_receipt = await self.client.write_contract(self.thor_router_address, func_to_call,
                                                asgard_address, ETH_RUNE.contract, amount,
                                                memo, erc20=False)
        new_balance = await self.client.get_balance(asset=ETH_RUNE)
        time.sleep(1)
        assert new_balance < old_balance

    # @pytest.mark.asyncio
    # async def test_thorchain_eth_rune(self, test_init):
    #     old_balance = await self.client.get_balance()
    #     func_to_call = "approve"


    # def test_fast_write(self):
    #     func_to_call = "xxx"
    #     self.client.set_gas_strategy("fast")
    #     nonce = self.client.w3.eth.getTransactionCount(self.client.get_address())
    #     for i in range(10):
    #         tx_receipt = self.client.write_contract(ETH_RUNE.contract, func_to_call, erc20=False, nonce=nonce+i)