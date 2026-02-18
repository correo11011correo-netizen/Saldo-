import os
import hashlib
import requests
import time
from ecdsa import SigningKey, SECP256k1

SECP256K1_N = int(
    "0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEBAAEDCE6AF48A03BBFD25E8CD0364141",
    16
)

ALPHABET = "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"

def generate_secp256k1_private_key():
    while True:
        raw = os.urandom(32)
        k = int.from_bytes(raw, "big")
        if 1 <= k < SECP256K1_N:
            return k

def base58check_encode(payload: bytes) -> str:
    checksum = hashlib.sha256(hashlib.sha256(payload).digest()).digest()[:4]
    data = payload + checksum
    zeros = len(data) - len(data.lstrip(b"\x00"))
    num = int.from_bytes(data, "big")
    encoded = ""
    while num > 0:
        num, rem = divmod(num, 58)
        encoded = ALPHABET[rem] + encoded
    return "1" * zeros + encoded

def private_key_to_p2pkh_address(priv_int: int) -> str:
    sk = SigningKey.from_secret_exponent(priv_int, curve=SECP256k1)
    vk = sk.get_verifying_key()
    x = vk.pubkey.point.x()
    y = vk.pubkey.point.y()
    pubkey_bytes = b"\x04" + x.to_bytes(32, "big") + y.to_bytes(32, "big")
    sha = hashlib.sha256(pubkey_bytes).digest()
    ripe = hashlib.new("ripemd160", sha).digest()
    versioned_payload = b"\x00" + ripe
    return base58check_encode(versioned_payload)

# ============================
#   SISTEMA MULTI‑RPC INTELIGENTE
# ============================

TEST_ADDR = "1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa"

RPCS = [
    {
        "name": "mempool.space",
        "url": lambda a: f"https://mempool.space/api/address/{a}/utxo",
        "parser": lambda r: sum(utxo["value"] for utxo in r.json())
    },
    {
        "name": "blockstream.info",
        "url": lambda a: f"https://blockstream.info/api/address/{a}/utxo",
        "parser": lambda r: sum(utxo["value"] for utxo in r.json())
    },
    {
        "name": "blockchain.info",
        "url": lambda a: f"https://blockchain.info/unspent?active={a}",
        "parser": lambda r: sum(tx["value"] for tx in r.json()["unspent_outputs"])
    },
    {
        "name": "sochain",
        "url": lambda a: f"https://sochain.com/api/v2/get_tx_unspent/BTC/{a}",
        "parser": lambda r: sum(int(tx["value"]) for tx in r.json()["data"]["txs"])
    },
    {
        "name": "blockchair",
        "url": lambda a: f"https://api.blockchair.com/bitcoin/dashboards/address/{a}",
        "parser": lambda r: r.json()["data"][a]["address"]["balance"]
    }
]

def try_rpc(rpc, address):
    try:
        r = requests.get(rpc["url"](address), timeout=10)
        if r.status_code != 200:
            return None
        return rpc["parser"](r)
    except:
        return None

def select_working_rpc():
    for rpc in RPCS:
        bal = try_rpc(rpc, TEST_ADDR)
        if bal is not None:
            print(f"✔ RPC activo: {rpc['name']} (balance Satoshi: {bal} sats)")
            return rpc
    print("❌ Ningún RPC funciona con la dirección de Satoshi.")
    return None

RPC_ACTIVO = select_working_rpc()

def get_balance_sats(address: str) -> int:
    global RPC_ACTIVO

    # 1) Intentar con el RPC activo
    if RPC_ACTIVO:
        bal = try_rpc(RPC_ACTIVO, address)
        if bal is not None:
            return bal
        print(f"⚠ RPC falló: {RPC_ACTIVO['name']} → buscando otro...")

    # 2) Buscar otro RPC funcional
    RPC_ACTIVO = select_working_rpc()
    if RPC_ACTIVO:
        bal = try_rpc(RPC_ACTIVO, address)
        if bal is not None:
            return bal

    return -1

# ============================
#   LOOP PRINCIPAL
# ============================

print("=== BTC HUNTER — LOOP INFINITO ===")
print("Generando 1 dirección por ciclo, sin detenerse.\n")

counter = 0

while True:
    counter += 1

    # Re-testear RPC cada 500 ciclos
    if counter % 500 == 0:
        print("\n🔄 Re-test RPC con dirección de Satoshi...")
        RPC_ACTIVO = select_working_rpc()

    priv_int = generate_secp256k1_private_key()
    priv_hex = f"{priv_int:064x}"
    address = private_key_to_p2pkh_address(priv_int)
    balance = get_balance_sats(address)

    if counter % 20 == 0:
        print(f"[{counter}] Dirección de control: {address}")

    with open("formulario.txt", "w") as f:
        f.write(f"Private key: {priv_hex}\n")
        f.write(f"Address: {address}\n")
        f.write(f"Balance: {balance} sats\n")

    if balance > 0:
        with open("with_funds.txt", "a") as f:
            f.write(f"{address} | {priv_hex} | {balance} sats\n")
        print(f"🔥 ENCONTRADO FONDO: {address} → {balance} sats")

    time.sleep(0.2)
