import os
import sys
import secrets
from eth_account import Account
from typing import Optional
import httpx
from x402.common import process_price_to_atomic_amount


def check_and_create_wallet(wallet: Optional[Account] = None) -> Account:
    if wallet is None:
        wallet_pk = os.getenv("WALLET_PRIVATE_KEY")
        if wallet_pk:
            wallet = Account.from_key(wallet_pk)
            print(f"[Laissez] Loaded wallet from .env file")
            print(f"[Laissez] Wallet address: {wallet.address}")
            print_usdc_balance_base_sepolia(wallet)
        else:
            wallet_creation_prompt = """
No wallet found. 
If you have a wallet private key, please set WALLET_PRIVATE_KEY in the .env file and run the program again.
If you don't have a wallet private key, you can create one now.
Note: If you choose to create a wallet, Laissez will add the wallet private key to the .env file.

Would you like to create a wallet now? (Y/n) >>> """
            wallet_creation_response = input(wallet_creation_prompt)
            if wallet_creation_response.lower() == "y" or wallet_creation_response.lower() == "":
                random_string = secrets.token_urlsafe(32)
                wallet = Account.create(random_string)
                env_file = ".env"
                with open(env_file, "a", encoding="utf-8") as f:
                    f.write(f"\nWALLET_PRIVATE_KEY={wallet.key.hex()}\n")
                    print("\n[Laissez] Wallet created and saved to .env file")

                print("="*50)
                print(f"[Laissez] SAVE THIS FOR FUTURE USE")
                print(f"[Laissez] Wallet address: {wallet.address}")
                print(f"[Laissez] Wallet private key: {wallet.key.hex()}")
                print("="*50)
                print()
                print("[Laissez] IMPORTANT:")
                print("[Laissez] Copy the wallet address and add faucet funds to 'Base Sepolia' for testing at https://faucet.circle.com")
                print()
                print("="*50)
                print("[Laissez] Please run the program again to continue.")
                print()
                sys.exit(0)
            else:
                raise ValueError("No wallet found and user did not want to create one")
    return wallet



def get_laissez_api_key(provided_api_key: Optional[str] = None) -> str:
    """Fetch and validate the Laissez API key.

    Prefers the provided_api_key argument, otherwise reads LAISSEZ_API_KEY from the environment.
    Ensures the key is in the expected format (lsz- prefix).
    """
    api_key = provided_api_key or os.getenv("LAISSEZ_API_KEY")
    if not api_key:
        raise ValueError(
            "LAISSEZ_API_KEY not found in environment. Create one at https://app.laissez.xyz to track agent spending."
        )
    if not api_key.startswith("lsz-"):
        raise ValueError(
            "Invalid LAISSEZ_API_KEY format. Get your API key at https://app.laissez.xyz"
        )
    return api_key


def _encode_balance_of_call(address: str) -> str:
    selector = "70a08231"  # keccak("balanceOf(address)") first 4 bytes
    addr = address.lower().replace("0x", "")
    padded_addr = addr.rjust(64, "0")
    return f"0x{selector}{padded_addr}"


def _get_usdc_address_base_sepolia() -> str:
    # Reuse x402 mapping for USDC on Base Sepolia
    _, asset_address, _ = process_price_to_atomic_amount("0.001", "base-sepolia")
    return asset_address


def print_usdc_balance_base_sepolia(wallet: Account, rpc_url: Optional[str] = None) -> None:
    """Print the wallet's USDC balance on Base Sepolia and exit.

    If the balance is 0, prints the faucet message and exits.
    """
    rpc = rpc_url or os.getenv("BASE_SEPOLIA_RPC_URL") or "https://sepolia.base.org"
    usdc_address = _get_usdc_address_base_sepolia()
    call_data = _encode_balance_of_call(wallet.address)

    payload = {
        "jsonrpc": "2.0",
        "method": "eth_call",
        "params": [
            {"to": usdc_address, "data": call_data},
            "latest",
        ],
        "id": 1,
    }

    try:
        with httpx.Client(timeout=20.0) as client:
            resp = client.post(rpc, json=payload)
            resp.raise_for_status()
            data = resp.json()
    except Exception as e:
        print(f"[Laissez] Failed to get USDC balance on Base Sepolia: {e}")
        print(f"[Laissez] Check you have funds in your wallet at https://sepolia.basescan.org/address/{wallet.address}")

    result_hex = data.get("result")
    if not result_hex:
        print(f"[Laissez]Failed to get USDC balance on Base Sepolia: {data}")
        print(f"[Laissez] Check you have funds in your wallet at https://sepolia.basescan.org/address/{wallet.address}")

    raw_balance = int(result_hex, 16)

    if raw_balance == 0:
        print(f"[Laissez] USDC balance on Base Sepolia: 0.000000 USDC")
        print("[Laissez] Copy the wallet address and add faucet funds to 'Base Sepolia' for testing at https://faucet.circle.com")
        sys.exit(0)

    human = raw_balance / 10**6  # USDC has 6 decimals
    print(f"[Laissez] USDC balance on Base Sepolia: {human:.6f} USDC")
    print("[Laissez] You can add more funds to your wallet at https://faucet.circle.com")
    print("="*50)
    print()


def print_ascii_art() -> None:
    print("""
▐▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▌
▐                                                             ▌
▐                                                             ▌
▐                                                             ▌
▐     ██╗      █████╗ ██╗███████╗███████╗███████╗███████╗     ▌
▐     ██║     ██╔══██╗██║██╔════╝██╔════╝██╔════╝╚══███╔╝     ▌
▐     ██║     ███████║██║███████╗███████╗█████╗    ███╔╝      ▌
▐     ██║     ██╔══██║██║╚════██║╚════██║██╔══╝   ███╔╝       ▌
▐     ███████╗██║  ██║██║███████║███████║███████╗███████╗     ▌
▐     ╚══════╝╚═╝  ╚═╝╚═╝╚══════╝╚══════╝╚══════╝╚══════╝     ▌
▐                                                             ▌
▐                                                             ▌
▐                                                             ▌
▐▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▌
""")