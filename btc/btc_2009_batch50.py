import os
import hashlib
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

OUTPUT_FILE = "btc_keys_50.txt"

with open(OUTPUT_FILE, "w") as f:
    f.write("=== GENERADOR BTC ESTILO 2009 — BLOQUE DE 50 ===\n")
    f.write("Claves privadas y direcciones P2PKH reales (mainnet)\n\n")

    print("=== GENERADOR BTC ESTILO 2009 — BLOQUE DE 50 ===")
    print("Claves privadas y direcciones P2PKH reales (mainnet)\n")

    for i in range(1, 51):
        priv_int = generate_secp256k1_private_key()
        priv_hex = f"{priv_int:064x}"
        address = private_key_to_p2pkh_address(priv_int)

        block = (
            f"[{i}]\n"
            f"Private key (HEX): {priv_hex}\n"
            f"Address (BTC P2PKH): {address}\n"
            + "-" * 60 + "\n"
        )

        print(block)
        f.write(block)

    f.write("\nIMPORTANTE:\n")
    f.write("- Estas claves son reales y válidas en mainnet.\n")
    f.write("- Guarda este archivo en un lugar seguro.\n")

print(f"\nArchivo guardado como: {OUTPUT_FILE}")
