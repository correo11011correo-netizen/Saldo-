import os
import hmac
import hashlib
import struct
import time
import requests
from ecdsa import SECP256k1, SigningKey
from eth_hash.auto import keccak
from mnemonic import Mnemonic

# ============================
#   BIP39 & WALLET ENGINE
# ============================

mnemo = Mnemonic("english")
# Dirección real para TEST de sistema (Beacon Deposit Contract)
REAL_TEST_ADDR = "0x00000000219ab540356cBB839Cbe05303d7705Fa"

# LISTA DE RPCs PÚBLICOS (ROTATIVOS)
RPC_NODES = [
    "https://cloudflare-eth.com",
    "https://eth.llamarpc.com",
    "https://rpc.ankr.com/eth",
    "https://ethereum.publicnode.com",
    "https://1rpc.io/eth"
]
CURRENT_RPC_INDEX = 0

def generate_secure_mnemonic():
    return mnemo.to_mnemonic(os.urandom(16))

def mnemonic_to_seed(mnemonic: str) -> bytes:
    return hashlib.pbkdf2_hmac("sha512", mnemonic.encode("utf-8"), b"mnemonic", 2048, dklen=64)

# ============================
#   BIP32 / BIP44 DERIVATION
# ============================

def hmac_sha512(key: bytes, data: bytes) -> bytes:
    return hmac.new(key, data, hashlib.sha512).digest()

def bip32_master_key(seed: bytes):
    I = hmac_sha512(b"Bitcoin seed", seed)
    return I[:32], I[32:]

def ckd_priv(k_par: bytes, c_par: bytes, index: int):
    sk = SigningKey.from_string(k_par, curve=SECP256k1)
    pub = b"\x04" + sk.get_verifying_key().to_string()
    data = pub + struct.pack(">L", index)
    I = hmac_sha512(c_par, data)
    I_L, I_R = I[:32], I[32:]
    k_int = (int.from_bytes(I_L, "big") + int.from_bytes(k_par, "big")) % SECP256k1.order
    return k_int.to_bytes(32, "big"), I_R

def derive_path(master_priv: bytes, master_chain: bytes, path: str):
    segments = path.lstrip("m/").split("/")
    k, c = master_priv, master_chain
    for seg in segments:
        if not seg: continue
        index = int(seg[:-1]) + 0x80000000 if seg.endswith("'") else int(seg)
        k, c = ckd_priv(k, c, index)
    return k, c

# ============================
#   ETHEREUM UTILS
# ============================

def privkey_to_eth_address(privkey: bytes) -> str:
    sk = SigningKey.from_string(privkey, curve=SECP256k1)
    pub = b"\x04" + sk.get_verifying_key().to_string()
    k = keccak(pub[1:])
    addr = k[-20:].hex().lower()
    keccak_addr = keccak(addr.encode("utf-8")).hex()
    checksum_addr = "0x"
    for i, char in enumerate(addr):
        if char.isalpha() and int(keccak_addr[i], 16) >= 8:
            checksum_addr += char.upper()
        else:
            checksum_addr += char
    return checksum_addr

# ============================
#   JSON-RPC MULTI-NODE ENGINE
# ============================

def call_rpc(method, params):
    global CURRENT_RPC_INDEX
    
    # Reintentamos con cada nodo de la lista si hay fallos
    for _ in range(len(RPC_NODES)):
        rpc_url = RPC_NODES[CURRENT_RPC_INDEX]
        payload = {
            "jsonrpc": "2.0",
            "method": method,
            "params": params,
            "id": 1
        }
        try:
            r = requests.post(rpc_url, json=payload, timeout=5)
            if r.status_code == 200:
                result = r.json().get("result")
                if result is not None:
                    return result
        except:
            pass
        
        # Si falla, saltamos al siguiente RPC
        CURRENT_RPC_INDEX = (CURRENT_RPC_INDEX + 1) % len(RPC_NODES)
    
    return None

def get_eth_data(address: str):
    # Consulta de Balance (eth_getBalance)
    bal_hex = call_rpc("eth_getBalance", [address, "latest"])
    if bal_hex is None: return None
    balance = int(bal_hex, 16)
    
    # Consulta de Historial (eth_getTransactionCount / Nonce)
    nonce_hex = call_rpc("eth_getTransactionCount", [address, "latest"])
    nonce = int(nonce_hex, 16) if nonce_hex else 0
    
    return {"balance": balance, "tx_count": nonce}

def main():
    print(f"=== ETH MULTI-NODE HUNTER v4.0 (JSON-RPC) ===")
    print(f"[*] Nodos configurados: {len(RPC_NODES)}")
    
    # --- PRUEBA DE RED INICIAL ---
    print(f"\n[?] Verificando conexión inicial con dirección real...")
    test = get_eth_data(REAL_TEST_ADDR)
    if test and test["balance"] > 0:
        print(f"✅ SISTEMA ONLINE! Saldo de TEST detectado: {test['balance']/10**18} ETH")
        print(f"[*] Nodo activo: {RPC_NODES[CURRENT_RPC_INDEX]}\n")
    else:
        print(f"❌ ERROR CRÍTICO! No se pudo conectar con los nodos RPC o no hay internet.")
        return
    
    paths = [
        "m/44'/60'/0'/0/0",  # Account 1 (MetaMask/Binance)
        "m/44'/60'/0'/0",    # Legacy
    ]
    
    count = 0
    start_time = time.time()

    while True:
        count += 1
        
        # TEST DE SISTEMA PERIÓDICO (Cada 100 semillas)
        if count % 100 == 0:
            test = get_eth_data(REAL_TEST_ADDR)
            if not test or test["balance"] == 0:
                print(f"❌ FALLO DE RED! Esperando 30s...")
                time.sleep(30)
                continue

        mnemonic = generate_secure_mnemonic()
        seed = mnemonic_to_seed(mnemonic)
        m_priv, m_chain = bip32_master_key(seed)

        if count % 20 == 0:
            print(f"[*] Procesando... Seeds: {count} | RPC: {RPC_NODES[CURRENT_RPC_INDEX]}")

        for path in paths:
            try:
                priv, _ = derive_path(m_priv, m_chain, path)
                address = privkey_to_eth_address(priv)
                
                data = get_eth_data(address)
                if not data: continue

                balance = data["balance"]
                txs = data["tx_count"]

                if balance > 0 or txs > 0:
                    status = "🔥 DINERO ENCONTRADO" if balance > 0 else "💎 HISTORIAL DETECTADO"
                    eth_val = balance / 10**18
                    
                    print(f"\n{status} en {path}")
                    print(f"ADDR: {address} | BAL: {eth_val} ETH | TXS: {txs}")
                    print(f"SEED: {mnemonic}\n")

                    filename = "GOLD_FUNDS.txt" if balance > 0 else "HISTORY_ACTIVE.txt"
                    with open(filename, "a") as f:
                        f.write(f"SEED: {mnemonic}\nPATH: {path}\nADDR: {address}\nBAL: {eth_val} ETH\nTXS: {txs}\nPRIV: {priv.hex()}\n\n")

            except Exception:
                continue
        
        # Ya no necesitamos esperas tan largas, el sistema multinodo es más resistente.
        time.sleep(0.1)

if __name__ == "__main__":
    main()
