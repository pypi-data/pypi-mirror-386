from testnet.interfaces import WalletAddressCreateInterface
from testnet.interfaces.logs import Logger
from typing import Optional, Dict
from eth_account import Account


class EthWalletAddressCreate(WalletAddressCreateInterface):
    @staticmethod
    def create(user_id: Optional[int] = None) -> Dict[str, str]:
        """
        Creates a new Eth wallet and returns the wallet details.

        Args:
            user_id (int, optional): User associated with the wallet. Defaults to None.

        Returns:
            Dict[str, str]: Wallet details or an error message.
        """
        logger = Logger(log_file="eth-addresses-generator.log").get_logger()
        try:
            account: Account = Account.create()
            private_key = "0x" + account.key.hex()
            public_key = account.address
            logger.info(f"Creating wallet with address {public_key}")
            return {"address": str(public_key), "private_key": str(private_key)}
        except Exception as ex:
            logger.error(f"Error creating eth address: {ex}")
            return {"error": str(ex)}
