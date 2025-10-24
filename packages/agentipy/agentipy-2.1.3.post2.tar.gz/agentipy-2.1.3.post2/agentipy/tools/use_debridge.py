import base64
import logging
from typing import Optional

import requests
from solana.rpc.commitment import Confirmed
from solana.rpc.types import TxOpts
from solders.message import to_bytes_versioned  # type: ignore
from solders.pubkey import Pubkey as PublicKey  # type: ignore
from solders.transaction import VersionedTransaction  # type: ignore

from agentipy.agent import SolanaAgentKit
from agentipy.constants import DEBRIDGE_API_URL
from agentipy.wallet.privy_wallet_client import PrivyWalletClient
from agentipy.wallet.solana_wallet_client import SolanaWalletClient

logger = logging.getLogger(__name__)

class DeBridgeManager:
    async def create_debridge_transaction(
        agent: SolanaAgentKit,
        src_chain_id: str,
        src_chain_token_in: str,
        src_chain_token_in_amount: str,
        dst_chain_id: str,
        dst_chain_token_out: str,
        dst_chain_token_out_recipient: str,
        src_chain_order_authority_address: str,
        dst_chain_order_authority_address: str,
        affiliate_fee_percent: str = "0",
        affiliate_fee_recipient: str = "",
        prepend_operating_expenses: bool = True,
        dst_chain_token_out_amount: str = "auto") -> dict:
        """
        Create a cross-chain bridge transaction using the deBridge Liquidity Network API.

        Args:
            agent (SolanaAgentKit): The Solana agent instance.
            src_chain_id (str): The internal chain ID of the source chain.
            src_chain_token_in (str): The address of the input token (token being sold).
            src_chain_token_in_amount (str): The amount of input token to sell (with decimals), or 'auto'.
            dst_chain_id (str): The internal chain ID of the destination chain.
            dst_chain_token_out (str): The address of the output token (token being bought).
            dst_chain_token_out_recipient (str): The recipient address on the destination chain.
            src_chain_order_authority_address (str): The address on the source chain for order authority.
            dst_chain_order_authority_address (str): The address on the destination chain for order authority.
            affiliate_fee_percent (str): The percentage of affiliate fee to cut off. Defaults to "0".
            affiliate_fee_recipient (str): The recipient address of the affiliate fee. Optional.
            prepend_operating_expenses (bool): Whether to prepend operating expenses. Defaults to True.
            dst_chain_token_out_amount (str): The amount of output token to buy (with decimals), or 'auto'. Defaults to "auto".

        Returns:
            dict: The response from the create-tx API endpoint.
        """

        logger.info(f"Creating deBridge transaction for source chain ID: {src_chain_id}, source chain token in: {src_chain_token_in}, source chain token in amount: {src_chain_token_in_amount}, destination chain ID: {dst_chain_id}, destination chain token out: {dst_chain_token_out}, destination chain token out recipient: {dst_chain_token_out_recipient}, source chain order authority address: {src_chain_order_authority_address}, destination chain order authority address: {dst_chain_order_authority_address}, affiliate fee percent: {affiliate_fee_percent}, affiliate fee recipient: {affiliate_fee_recipient}, prepend operating expenses: {prepend_operating_expenses}, destination chain token out amount: {dst_chain_token_out_amount}")

        if not dst_chain_token_out_recipient:
            raise ValueError("Destination chain token recipient is required")

        if not src_chain_order_authority_address or not dst_chain_order_authority_address:
            raise ValueError("Order authority addresses are required")

        params = {
            "srcChainId": src_chain_id,
            "srcChainTokenIn": src_chain_token_in,
            "srcChainTokenInAmount": src_chain_token_in_amount,
            "dstChainId": dst_chain_id,
            "dstChainTokenOut": dst_chain_token_out,
            "dstChainTokenOutAmount": dst_chain_token_out_amount,
            "dstChainTokenOutRecipient": dst_chain_token_out_recipient,
            "srcChainOrderAuthorityAddress": src_chain_order_authority_address,
            "dstChainOrderAuthorityAddress": dst_chain_order_authority_address,
            "affiliateFeePercent": affiliate_fee_percent,
            "prependOperatingExpense": str(prepend_operating_expenses).lower(),
        }

        if affiliate_fee_recipient:
            params["affiliateFeeRecipient"] = affiliate_fee_recipient

        try:
            response = requests.get(
                f"{DEBRIDGE_API_URL}/dln/order/create-tx", 
                params=params
            )

            if not response.ok:
                raise Exception(
                    f"HTTP error! status: {response.status_code}, body: {response.text}"
                )

            result = response.json()
            logger.info(f"DeBridge API response: {result}")
            return result

        except Exception as e:
            raise Exception(f"Error creating deBridge transaction: {str(e)}")

    async def execute_debridge_transaction(agent: SolanaAgentKit, transaction_data: dict) -> str:
        """
        Execute a given bridge transaction on Solana using VersionedTransaction.
        Accepts deBridge's unsigned tx (hex/base64), fixes blockhash, and
        either sends via PrivyWalletClient (full base64 tx) or signs+sends via SolanaWalletClient.
        """
        from solders.hash import Hash  # type: ignore
        from solders.message import MessageV0  # type: ignore
        from solders.message import to_bytes_versioned
        from solders.signature import \
            Signature as SoldersSignature  # type: ignore

        if not transaction_data or "data" not in transaction_data:
            raise Exception("Invalid transaction data provided for execution.")

        try:
            logger.info(f"Transaction data received: {transaction_data}")

            data_str = transaction_data["data"]
            if isinstance(data_str, str) and data_str.startswith("0x"):
                raw_bytes = bytes.fromhex(data_str[2:])
            
            else:
                raw_bytes = base64.b64decode(data_str)
                        
            tx = VersionedTransaction.from_bytes(raw_bytes)
            
            latest_blockhash_resp = await agent.connection.get_latest_blockhash()
            latest = latest_blockhash_resp.value

            msg: MessageV0 = tx.message  # type: ignore
            new_msg = MessageV0(
                header=msg.header,
                account_keys=msg.account_keys,
                recent_blockhash=Hash.from_string(str(latest.blockhash)),
                instructions=msg.instructions,
                address_table_lookups=msg.address_table_lookups,
            )

            from solders.signature import Signature  # type: ignore
            zero_sig = Signature.default()
            unsigned_tx = VersionedTransaction.populate(new_msg, [zero_sig])

            if isinstance(agent.wallet_client, PrivyWalletClient):
                full_base64_tx = base64.b64encode(bytes(unsigned_tx)).decode("utf-8")

                res = await agent.wallet_client.send_transaction(full_base64_tx)
                tx_id = res.get("hash", "tx_id")
                signature: str | SoldersSignature = tx_id
                

            elif isinstance(agent.wallet_client, SolanaWalletClient):
                sig_bytes = agent.wallet.sign_message(to_bytes_versioned(new_msg))
                signed_tx = VersionedTransaction.populate(new_msg, [sig_bytes])

                tx_resp = await agent.connection.send_transaction(
                    signed_tx,
                    opts=TxOpts(
                        preflight_commitment=Confirmed,
                        skip_preflight=False,
                        max_retries=3,
                    )
                )
                tx_id = tx_resp.value
                signature = tx_id
                

            else:
                raise ValueError(f"Unsupported wallet client type: {type(agent.wallet_client).__name__}")

            if isinstance(signature, str):
                signature = SoldersSignature.from_string(signature)

            await agent.connection.confirm_transaction(
                tx_sig=signature,
                commitment=Confirmed,
                last_valid_block_height=latest.last_valid_block_height,
            )

            return str(tx_id)

        except Exception as err:
            raise Exception(f"Error executing transaction: {str(err)}")
    
    async def check_transaction_status(tx_hash: str) -> list[dict]:
        """
        Check the status of a transaction using its hash.

        Args:
            tx_hash (str): The hash of the transaction to check.

        Returns:
            list[dict]: A list of statuses for the orders related to the transaction.
        """
        try:
            order_ids_url = f"{DEBRIDGE_API_URL}/dln/tx/{tx_hash}/order-ids"
            print(f"Getting order IDs from: {order_ids_url}")

            order_ids_response = requests.get(order_ids_url)
            if not order_ids_response.ok:
                raise Exception(
                    f"HTTP error! status: {order_ids_response.status_code}, "
                    f"body: {order_ids_response.text}"
                )

            order_ids_data = order_ids_response.json()
            print(f"Order IDs response: {order_ids_data}")

            if "orderIds" not in order_ids_data or not order_ids_data["orderIds"]:
                raise Exception("No order IDs found for this transaction")

            statuses = []
            for order_id in order_ids_data["orderIds"]:
                status_url = f"{DEBRIDGE_API_URL}/dln/order/{order_id}/status"
                print(f"Getting status from: {status_url}")

                status_response = requests.get(status_url)
                if not status_response.ok:
                    raise Exception(
                        f"HTTP error! status: {status_response.status_code}, "
                        f"body: {status_response.text}"
                    )

                status_data = status_response.json()
                status_data["orderLink"] = f"https://app.debridge.finance/order?orderId={order_id}"
                print(f"Status response: {status_data}")
                statuses.append(status_data)

            return statuses

        except Exception as e:
            raise Exception(f"Failed to check transaction status: {str(e)}")