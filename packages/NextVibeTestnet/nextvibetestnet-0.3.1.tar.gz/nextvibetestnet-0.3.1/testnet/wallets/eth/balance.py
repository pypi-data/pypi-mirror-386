from testnet.interfaces.logs import Logger
from testnet.interfaces import AddressBalanceInterface
from typing import Optional
from decimal import Decimal
from web3 import Web3, HTTPProvider
from web3.types import Wei

from dotenv import load_dotenv
import os

load_dotenv()

class EthAddressBalance(AddressBalanceInterface):
    @staticmethod
    def get_balance(wallet_name: Optional[str] = None, address: Optional[str] = None) -> float | Decimal:
        logger = Logger("eth-addresses-balance.log").get_logger()
        try:
            rpc_url: str | None = os.getenv("ETH_RPC_LINK")
            if not rpc_url:
                logger.error("Failed to get rpc url from .env file")
                return 0.0
            
            w3 = Web3(HTTPProvider(rpc_url))
            if not w3.is_connected():
                logger.error("Failed to connect to provider RPC")
                return 0.0

            if not address or not Web3.is_address(address):
                logger.error(f"Address {address} is not valid")
                return 0.0

            balance_wei: Wei = w3.eth.get_balance(address)
            balance: Decimal = w3.from_wei(number=balance_wei, unit="ether")
            logger.info(f"Successfully got balance for address: {address}, balance: {balance}")
            return balance
            
        except Exception as ex:
            logger.error(f"Unknown error while getting balance for address {address}: {ex}")
            return 0.0
           