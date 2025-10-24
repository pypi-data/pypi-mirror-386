from testnet.interfaces.logs import Logger
from typing import NoReturn, Optional, Dict, Any
from decimal import Decimal
from web3 import Web3, HTTPProvider
from eth_account import Account

from dotenv import load_dotenv
from os import getenv

load_dotenv()

class EthTransaction:
    def __init__(self, private_key: str, to_address: str, value: float) -> NoReturn:
        self.logger = Logger("eth-transactions.log").get_logger()
        rpc_url = getenv("ETH_RPC_LINK")
        if not rpc_url:
            self.logger.error("Failed to get rpc url from .env file")
            raise ValueError("Missing ETH_RPC_LINK in .env file")

        self.w3 = Web3(HTTPProvider(rpc_url))
        if not self.w3.is_connected():
            self.logger.error("Failed to connect to provider RPC")
            raise ConnectionError("Cannot connect to Ethereum RPC")
        
        if not private_key:
            self.logger.error("Private key not provided")
            raise ValueError("Private key is required")

        self.account = Account.from_key(private_key)
        self.from_address = self.account.address

        if not to_address or not self.w3.is_address(to_address):
            self.logger.error(f"Invalid to_address: {to_address}")
            raise ValueError("Invalid to_address")

        if not value or value <= 0:
            self.logger.error(f"Invalid transaction value: {value}")
            raise ValueError("Transaction value must be greater than 0")

        self.to_address = self.w3.to_checksum_address(to_address)
        self.value = Decimal(value)
        self.private_key = private_key

    def format_transaction(self) -> Dict[str, Any]:
        transaction: Dict = {
            "chainId": self.w3.eth.chain_id,
            "from": self.from_address,
            "to": self.to_address,
            "value": self.w3.to_wei(self.value, "ether"),
            "nonce": self.w3.eth.get_transaction_count(self.from_address),
            "gas": 21000,
            'maxFeePerGas': self.w3.to_wei(2, 'gwei'),
            'maxPriorityFeePerGas': self.w3.to_wei(2, 'gwei'),
        }
        return transaction
        
    def send_transaction(self) -> Dict:
        transaction = self.format_transaction()
        signed = self.w3.eth.account.sign_transaction(transaction, self.private_key)
        tx_hash = self.w3.eth.send_raw_transaction(signed.raw_transaction)
        self.logger.info(f"""Transaction sent success, 
                             from: {self.from_address}, 
                             to: {self.to_address}, 
                             value: {self.value}, 
                             tx: {tx_hash.hex()}""")
        return {"tx": tx_hash.hex()}
