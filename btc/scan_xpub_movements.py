#!/usr/bin/env python3
import sys, hashlib, hmac, struct, json
from urllib.request import urlopen

# ===== Base58Check =====
ALPHABET = "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"

def b58decode(s):
    num = 0
    for ch in s:
        num = num * 58 + ALPHABET.index(ch)
    return num

def b58decode_check(s):
    num = b58decode(s)
    full = num.to_bytes(82, "big").lstrip(b"\x00")
    pad = 0
    for ch in s:
        if ch == "1":
            pad += 1
        else:
            break
    full = b"\x00" * pad + full
    data, checksum = full[:-4], full[-4:]
    calc = hashlib.sha256(hashlib.sha256(data).digest()).digest()[:4]
    if calc != checksum:
        raise ValueError("Checksum inválido")
    return data

def b58encode_check(payload):
    num = int.from_bytes(payload, "big")
    res = ""
    while num > 0:
        num, rem = divmod(num, 58)
        res = ALPHABET[rem] + res
    for b in payload:
        if b == 0:
            res = "1" + res
        else:
            break
    return res

# ===== secp256k1 =====
P = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEFFFFFC2F
N = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEBAAEDCE6AF48A03BBFD25E8CD0364141
Gx = 55066263022277343669578718895168534326250603453777594175500187360389116729240
Gy = 32670510020758816978083085130507043184471273380659243275938904335757337482424
G = (Gx, Gy)

def inv_mod(k, p):
    return pow(k, p - 2, p)

def point_add(P1, P2):
    if P1 is None:
        return P2
    if P2 is None:
        return P1
    x1, y1 = P1
    x2, y2 = P2
    if x1 == x2 and (y1 + y2) % P == 0:
        return None
    if P1 == P2:
        s = (3 * x1 * x1 * inv_mod(2 * y1 % P, P)) % P
    else:
        s = ((y2 - y1) * inv_mod((x2 - x1) % P, P)) % P
    x3 = (s * s - x1 - x2) % P
    y3 = (s * (x1 - x3) - y1) % P
    return (x3, y3)

def scalar_mult(k, point):
    if k % N == 0 or point is None:
        return None
    k = k % N
    result = None
    addend = point
    while k:
        if k & 1:
            result = point_add(result, addend)
        addend = point_add(addend, addend)
        k >>= 1
    return result

def serP(P):
    x, y = P
    return (b"\x02" if (y % 2 == 0) else b"\x03") + x.to_bytes(32, "big")

def parse_pubkey(sec):
    if sec[0] not in (2, 3):
        raise ValueError("Solo pubkeys comprimidas soportadas")
    x = int.from_bytes(sec[1:], "big")
    # y^2 = x^3 + 7
    a = (x*x*x + 7) % P
    y = pow(a, (P+1)//4, P)
    if (y % 2) != (sec[0] - 2):
        y = (-y) % P
    return (x, y)

# ===== BIP32 desde XPUB (solo hijos públicos no endurecidos) =====
def parse_xpub(xpub):
    raw = b58decode_check(xpub)
    if len(raw) != 78:
        raise ValueError("XPUB inválido")
    version = raw[0:4]
    depth = raw[4]
    parent_fp = raw[5:9]
    child_num = struct.unpack(">I", raw[9:13])[0]
    chain_code = raw[13:45]
    pubkey = raw[45:78]
    return version, depth, parent_fp, child_num, chain_code, pubkey

def CKDpub(K_par, c_par, i):
    if i >= 0x80000000:
        raise ValueError("Hijo endurecido no soportado en CKDpub")
    data = serP(K_par) + struct.pack(">I", i)
    I = hmac.new(c_par, data, hashlib.sha512).digest()
    IL, IR = I[:32], I[32:]
    k_i = int.from_bytes(IL, "big")
    if k_i >= N:
        raise ValueError("IL fuera de rango")
    K_child = point_add(scalar_mult(k_i, G), K_par)
    if K_child is None:
        raise ValueError("Punto inválido")
    return K_child, IR

def pubkey_to_p2pkh_address(P):
    sec = serP(P)
    sha = hashlib.sha256(sec).digest()
    rip = hashlib.new("ripemd160", sha).digest()
    versioned = b"\x00" + rip
    checksum = hashlib.sha256(hashlib.sha256(versioned).digest()).digest()[:4]
    return b58encode_check(versioned + checksum)

def fetch_address_info(addr):
    url = f"https://blockstream.info/api/address/{addr}"
    with urlopen(url) as resp:
        data = resp.read()
    return json.loads(data.decode())

def main():
    if len(sys.argv) < 3:
        print("Uso: python3 scan_xpub_movements.py <XPUB> <cantidad_direcciones>")
        print("Ejemplo: python3 scan_xpub_movements.py xpub... 50")
        sys.exit(1)

    xpub = sys.argv[1].strip()
    count = int(sys.argv[2])

    if not xpub.startswith("xpub"):
        print("Solo se admite XPUB en este script (no XPRV).")
        sys.exit(1)

    version, depth, parent_fp, child_num, chain_code, pubkey = parse_xpub(xpub)
    K0 = parse_pubkey(pubkey)
    c0 = chain_code

    print(f"XPUB depth={depth}, child={child_num}")
    print(f"Escaneando {count} direcciones de la rama m/0/i ...\n")

    # Derivamos primero la rama externa m/0 (no endurecida)
    # m/0 hijo de m
    branch_index = 0
    K_branch, c_branch = CKDpub(K0, c0, branch_index)

    for i in range(count):
        try:
            K_i, c_i = CKDpub(K_branch, c_branch, i)
        except Exception as e:
            print(f"[m/0/{i}] error derivando: {e}")
            continue

        addr = pubkey_to_p2pkh_address(K_i)
        try:
            info = fetch_address_info(addr)
        except Exception as e:
            print(f"[m/0/{i}] {addr} - error consultando API: {e}")
            continue

        txs = info.get("chain_stats", {}).get("tx_count", 0) + \
              info.get("mempool_stats", {}).get("tx_count", 0)
        funded = info.get("chain_stats", {}).get("funded_txo_sum", 0)
        spent = info.get("chain_stats", {}).get("spent_txo_sum", 0)
        balance = funded - spent

        if txs > 0:
            print(f"[USADA] m/0/{i}  {addr}  txs={txs}  balance={balance} sats")
        else:
            print(f"[vacía] m/0/{i}  {addr}")

if __name__ == "__main__":
    main()
