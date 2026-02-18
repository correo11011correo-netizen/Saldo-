import os
import hashlib
from ecdsa import SigningKey, SECP256k1

# Orden del grupo de la curva secp256k1 (n)
SECP256K1_N = int(
    "0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEBAAEDCE6AF48A03BBFD25E8CD0364141",
    16
)

# Alfabeto Base58 de Bitcoin
ALPHABET = "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"


def generate_secp256k1_private_key():
    """
    Genera una clave privada válida para secp256k1 usando entropía del SO,
    al estilo Bitcoin Core temprano:
    - 32 bytes aleatorios
    - interpretados como entero
    - verificación de 1 <= k < n
    """
    while True:
        raw = os.urandom(32)
        k = int.from_bytes(raw, "big")
        if 1 <= k < SECP256K1_N:
            return k


def base58check_encode(payload: bytes) -> str:
    """
    Base58Check:
    - checksum = primeros 4 bytes de SHA256(SHA256(payload))
    - payload + checksum
    - conversión a Base58 con manejo de ceros iniciales
    """
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
    """
    Private key (entero) -> dirección BTC P2PKH mainnet:
    - secp256k1 -> public key sin comprimir (0x04 || X || Y)
    - SHA256 -> RIPEMD160 -> hash160
    - prefijo 0x00 (mainnet P2PKH)
    - Base58Check -> dirección tipo '1...'
    """
    sk = SigningKey.from_secret_exponent(priv_int, curve=SECP256k1)
    vk = sk.get_verifying_key()

    x = vk.pubkey.point.x()
    y = vk.pubkey.point.y()
    pubkey_bytes = b"\x04" + x.to_bytes(32, "big") + y.to_bytes(32, "big")

    sha = hashlib.sha256(pubkey_bytes).digest()
    ripe = hashlib.new("ripemd160", sha).digest()

    versioned_payload = b"\x00" + ripe

    address = base58check_encode(versioned_payload)
    return address


if __name__ == "__main__":
    priv_int = generate_secp256k1_private_key()
    priv_hex = f"{priv_int:064x}"
    address = private_key_to_p2pkh_address(priv_int)

    print("=== CLAVE BTC ESTILO 2009 (NO HD, SIN SEED) ===")
    print("Private key (HEX, 64 chars):")
    print(priv_hex)
    print()
    print("Dirección BTC (P2PKH mainnet, tipo 1...):")
    print(address)
    print()
    print("IMPORTANTE:")
    print("- Esta clave es REAL y válida en mainnet.")
    print("- Guarda la private key OFFLINE. Si la perdés, perdés los fondos.")
