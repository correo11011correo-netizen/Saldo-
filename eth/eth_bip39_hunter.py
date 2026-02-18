import os
import hmac
import hashlib
import struct
import time
import requests
from ecdsa import SECP256k1, SigningKey
from eth_hash.auto import keccak  # Keccak-256 real, mismo que Ethereum

# ============================
#   BIP39
# ============================

def mnemonic_to_seed(mnemonic: str, passphrase: str = "") -> bytes:
    mnemonic = mnemonic.strip()
    salt = ("mnemonic" + passphrase).encode("utf-8")
    return hashlib.pbkdf2_hmac("sha512", mnemonic.encode("utf-8"), salt, 2048, dklen=64)

# ============================
#   BIP32
# ============================

def hmac_sha512(key: bytes, data: bytes) -> bytes:
    return hmac.new(key, data, hashlib.sha512).digest()

def bip32_master_key(seed: bytes):
    I = hmac_sha512(b"Bitcoin seed", seed)
    return I[:32], I[32:]

def privkey_to_pubkey_uncompressed(privkey: bytes) -> bytes:
    sk = SigningKey.from_string(privkey, curve=SECP256k1)
    vk = sk.get_verifying_key()
    x = vk.pubkey.point.x()
    y = vk.pubkey.point.y()
    return b"\x04" + x.to_bytes(32, "big") + y.to_bytes(32, "big")

def ckd_priv(k_par: bytes, c_par: bytes, index: int):
    # Child Key Derivation privado (BIP32)
    if index >= 0x80000000:
        data = b"\x00" + k_par + struct.pack(">L", index)
    else:
        pub = privkey_to_pubkey_uncompressed(k_par)
        data = pub + struct.pack(">L", index)
    I = hmac_sha512(c_par, data)
    I_L, I_R = I[:32], I[32:]
    k_int = (int.from_bytes(I_L, "big") + int.from_bytes(k_par, "big")) % SECP256k1.order
    if k_int == 0:
        raise ValueError("Derivación inválida (k_int = 0)")
    return k_int.to_bytes(32, "big"), I_R

def derive_path(master_priv: bytes, master_chain: bytes, path: str):
    # Deriva cualquier path tipo: m/44'/60'/0'/0/0
    if not path.startswith("m/"):
        raise ValueError("Path inválido, debe empezar con m/")
    segments = path.lstrip("m/").split("/")
    k, c = master_priv, master_chain
    for seg in segments:
        if seg.endswith("'"):
            index = int(seg[:-1]) + 0x80000000
        else:
            index = int(seg)
        k, c = ckd_priv(k, c, index)
    return k, c

# ============================
#   ETH ADDRESS (Keccak real)
# ============================

def keccak_256(data: bytes) -> bytes:
    # Keccak real, mismo que usa Ethereum
    return keccak(data)

def to_checksum_address(addr_hex_noprefix: str) -> str:
    addr_lower = addr_hex_noprefix.lower()
    keccak_hex = keccak_256(addr_lower.encode("utf-8")).hex()
    out = ""
    for c, k in zip(addr_lower, keccak_hex):
        if c.isalpha() and int(k, 16) >= 8:
            out += c.upper()
        else:
            out += c
    return out

def privkey_to_eth_address(privkey: bytes) -> str:
    pub = privkey_to_pubkey_uncompressed(privkey)
    # Ethereum: Keccak-256 de la pubkey sin el 0x04
    k = keccak_256(pub[1:])
    addr = k[-20:].hex()
    return "0x" + to_checksum_address(addr)

# ============================
#   MULTI-RPC ETH
# ============================

TEST_ADDR = "0xde0B295669a9FD93d5F28D9Ec85E40f4cb697BAe"

RPCS = [
    {
        "name": "blockchair",
        "url": lambda a: f"https://api.blockchair.com/ethereum/dashboards/address/{a}",
        "parser": lambda r, a: int(r.json()["data"][a.lower()]["address"]["balance"])
    },
    {
        "name": "blockcypher",
        "url": lambda a: f"https://api.blockcypher.com/v1/eth/main/addrs/{a}/balance",
        "parser": lambda r, a: int(r.json()["balance"])
    },
    {
        "name": "ethplorer",
        "url": lambda a: f"https://api.ethplorer.io/getAddressInfo/{a}?apiKey=freekey",
        "parser": lambda r, a: int(r.json()["ETH"]["rawBalance"])
    }
]

def try_rpc_eth(rpc, address):
    try:
        r = requests.get(rpc["url"](address), timeout=10)
        if r.status_code != 200:
            return None
        return rpc["parser"](r, address)
    except Exception:
        return None

def select_working_rpc():
    for rpc in RPCS:
        bal = try_rpc_eth(rpc, TEST_ADDR)
        if bal is not None:
            print(f"✔ RPC ETH activo: {rpc['name']} (test balance: {bal} wei)")
            return rpc
    print("❌ Ningún RPC ETH funciona.")
    return None

RPC_ACTIVO = None

def get_balance_wei(address: str) -> int:
    global RPC_ACTIVO
    if RPC_ACTIVO:
        bal = try_rpc_eth(RPC_ACTIVO, address)
        if bal is not None:
            return bal
        print(f"⚠ RPC falló: {RPC_ACTIVO['name']} → cambiando...")
    RPC_ACTIVO = select_working_rpc()
    if RPC_ACTIVO:
        bal = try_rpc_eth(RPC_ACTIVO, address)
        if bal is not None:
            return bal
    return -1

# ============================
#   MAIN
# ============================

def main():
    global RPC_ACTIVO

    print("=== ETH BIP39 HUNTER — SOLO 2 CUENTAS ===")
    print("Path: m/44'/60'/0'/0/i (MetaMask / Binance compatible)\n")

    mnemonic = input("Ingrese su frase de 12 palabras: ").strip()
    seed = mnemonic_to_seed(mnemonic)
    master_priv, master_chain = bip32_master_key(seed)

    base_path = "m/44'/60'/0'/0"
    base_priv, base_chain = derive_path(master_priv, master_chain, base_path)

    RPC_ACTIVO = select_working_rpc()
    if RPC_ACTIVO is None:
        return

    for index in range(2):  # SOLO CUENTAS 0 y 1
        priv_child, _ = ckd_priv(base_priv, base_chain, index)
        priv_hex = priv_child.hex()
        address = privkey_to_eth_address(priv_child)

        balance = get_balance_wei(address)

        print(f"[{index}] {address} | balance: {balance} wei")

        # Último formulario
        with open("eth_formulario.txt", "w") as f:
            f.write(f"Index: {index}\n")
            f.write(f"Path: {base_path}/{index}\n")
            f.write(f"Private key: {priv_hex}\n")
            f.write(f"Address: {address}\n")
            f.write(f"Balance: {balance} wei\n")

        # Si tiene fondos, registro
        if balance > 0:
            with open("eth_with_funds.txt", "a") as f:
                f.write(f"{index} | {address} | {priv_hex} | {balance} wei\n")

            with open("eth_found_wallets.txt", "a") as f:
                f.write("=====================================\n")
                f.write(f"Index: {index}\n")
                f.write(f"Path: {base_path}/{index}\n")
                f.write(f"Dirección: {address}\n")
                f.write(f"Clave privada: {priv_hex}\n")
                f.write(f"Balance: {balance} wei\n")
                f.write(f"RPC usado: {RPC_ACTIVO['name']}\n")
                f.write(f"Timestamp: {time.ctime()}\n")
                f.write("=====================================\n\n")

            print(f"🔥 ENCONTRADO FONDO ETH: {address} → {balance} wei")

if __name__ == "__main__":
    main()
