import asyncio
import base64
import logging
import platform

import aiohttp
from solana.rpc.commitment import Confirmed
from solana.rpc.types import TxOpts
from solders.message import to_bytes_versioned  # type: ignore
from solders.pubkey import Pubkey  # type: ignore
from solders.transaction import VersionedTransaction  # type: ignore

from agentipy.agent import SolanaAgentKit
from agentipy.constants import (DEFAULT_OPTIONS, JUP_API, LAMPORTS_PER_SOL,
                                TOKENS)
from agentipy.wallet.privy_wallet_client import PrivyWalletClient
from agentipy.wallet.solana_wallet_client import SolanaWalletClient

if platform.system() == "Windows":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

logger = logging.getLogger(__name__)


class TradeManager:
    @staticmethod
    async def trade(
        agent: SolanaAgentKit,
        output_mint: Pubkey,
        input_amount: float,
        input_mint: Pubkey = TOKENS["USDC"],
        slippage_bps: int = DEFAULT_OPTIONS["SLIPPAGE_BPS"],
    ) -> str:
        """
        Swap tokens using Jupiter Exchange.

        Args:
            agent (SolanaAgentKit): The Solana agent instance.
            output_mint (Pubkey): Target token mint address.
            input_amount (float): Amount to swap (in token decimals).
            input_mint (Pubkey): Source token mint address (default: USDC).
            slippage_bps (int): Slippage tolerance in basis points (default: 300 = 3%).

        Returns:
            str: Transaction signature.

        Raises:
            Exception: If the swap fails.
        """
        try:
            
            if isinstance(input_amount, str):
                input_amount = float(input_amount)
            
            amount_in_lamports = int(input_amount * LAMPORTS_PER_SOL)
            
            quote_url = (
                f"{JUP_API}/quote?"
                f"inputMint={input_mint}"
                f"&outputMint={output_mint}"
                f"&amount={amount_in_lamports}"
                f"&slippageBps={slippage_bps}"
                f"&onlyDirectRoutes=true"
                f"&maxAccounts=20"
            )

            async with aiohttp.ClientSession() as session:
                async with session.get(quote_url) as quote_response:
                    if quote_response.status != 200:
                        raise Exception(
                            f"Failed to fetch quote: {quote_response.status}"
                        )
                    quote_data = await quote_response.json()

                async with session.post(
                    f"{JUP_API}/swap",
                    json={
                        "quoteResponse": quote_data,
                        "userPublicKey": str(agent.wallet_address),
                        "wrapAndUnwrapSol": True,
                        "dynamicComputeUnitLimit": True,
                        "prioritizationFeeLamports": "auto",
                    },
                ) as swap_response:
                    if swap_response.status != 200:
                        raise Exception(
                            f"Failed to fetch swap transaction: {swap_response.status}"
                        )
                    swap_data = await swap_response.json()

            latest_blockhash = await agent.connection.get_latest_blockhash()

            if isinstance(agent.wallet_client, PrivyWalletClient):
                res = await agent.wallet_client.send_transaction(
                    swap_data["swapTransaction"]
                )
                tx_id = res.get("hash", "tx_id")
                signature = tx_id  # Store signature for confirmation

            elif isinstance(agent.wallet_client, SolanaWalletClient):
                swap_transaction_buf = base64.b64decode(swap_data["swapTransaction"])
                transaction = VersionedTransaction.from_bytes(swap_transaction_buf)

                signature = agent.wallet.sign_message(
                    to_bytes_versioned(transaction.message)
                )
                signed_transaction = VersionedTransaction.populate(
                    transaction.message, [signature]
                )

                tx_id = await agent.connection.send_transaction(
                    signed_transaction,
                    opts=TxOpts(
                        preflight_commitment=Confirmed,
                        skip_preflight=False,
                        max_retries=3,
                    ),
                )
                logger.info(f"Transaction Signature: {tx_id}")
                signature = tx_id  # Store signature for confirmation

            else:
                raise ValueError(
                    f"Unsupported wallet client type: {type(agent.wallet_client).__name__}"
                )

            if isinstance(signature, str):
                from solders.signature import Signature  # type: ignore
                signature = Signature.from_string(signature)

            await agent.connection.confirm_transaction(
                tx_sig=signature,
                commitment=Confirmed,
                last_valid_block_height=latest_blockhash.value.last_valid_block_height,
            )

            return str(signature)

        except Exception as e:
            raise Exception(f"Swap failed: {str(e)}")
