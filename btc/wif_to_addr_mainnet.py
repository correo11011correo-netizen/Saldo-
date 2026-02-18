import sys, hashlib

alphabet = "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"

def b58decode_check(s):
    num = 0
    for ch in s:
        num = num * 58 + alphabet.index(ch)
    full = num.to_bytes(50, "big")
    full = full.lstrip(b"\x00")
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

# ====== secp256k1 ======
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

def b58encode_check(payload):
    num = int.from_bytes(payload, "big")
    res = ""
    while num > 0:
        num, rem = divmod(num, 58)
        res = alphabet[rem] + res
    for b in payload:
        if b == 0:
            res = "1" + res
        else:
            break
    return res

if len(sys.argv) != 2:
    print("Uso: python3 wif_to_addr_mainnet.py <WIF_testnet>")
    sys.exit(1)

wif = sys.argv[1]

data = b58decode_check(wif)
version = data[0]
body = data[1:]

if version != 0xEF:
    print("Advertencia: este WIF no es testnet, versión:", hex(version))

if len(body) == 33 and body[-1] == 0x01:
    priv = body[:-1]
    compressed = True
else:
    priv = body
    compressed = False

priv_int = int.from_bytes(priv, "big")
Pub = scalar_mult(priv_int, G)
Px, Py = Pub

if compressed:
    prefix = b"\x02" if (Py % 2 == 0) else b"\x03"
    pubkey_bytes = prefix + Px.to_bytes(32, "big")
else:
    pubkey_bytes = b"\x04" + Px.to_bytes(32, "big") + Py.to_bytes(32, "big")

sha = hashlib.sha256(pubkey_bytes).digest()
rip = hashlib.new("ripemd160", sha).digest()

# MAINNET P2PKH = 0x00
versioned = b"\x00" + rip
checksum = hashlib.sha256(hashlib.sha256(versioned).digest()).digest()[:4]
payload = versioned + checksum
addr = b58encode_check(payload)

print("Privkey hex:", priv.hex())
print("Pubkey:", pubkey_bytes.hex())
print("Dirección MAINNET:", addr)
