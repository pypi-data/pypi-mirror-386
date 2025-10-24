# ====== IMAD213 RSA v2.2 Protected Code ======
import os, sys, base64, zlib
from Crypto.Cipher import AES

def f1(x): return x[::-1]
def f2(x): return ''.join(chr(ord(c)^0x5A) for c in x)
def f3(x): return ''.join(chr((ord(c)+7)%256) for c in x)
def f4(x): return ''.join(chr((ord(c)-7)%256) for c in x)
def f5(x): return x.swapcase()
uf = [f1, f2, f4, f3, f5]

def xor_decrypt(data, key):
    return bytes(b ^ key[i % len(key)] for i, b in enumerate(data))

def reconstruct_key(parts, indices, types):
    ordered = [None]*len(parts)
    for i, idx in enumerate(indices):
        part = parts[i]
        if len(part) > 6:
            part = part[3:-3]
        func = uf[types[i]]
        ordered[idx] = func(part)
    k = ''.join(ordered)
    while len(k)%4 != 0:
        k += '='
    return base64.b64decode(k)

def db7Ol6h4(): return 574
def tEof5cCs(): return 912
def YPtMyTWE(): return 633
def Ugciy9iH(): return 572
def wO6auRYy(): return 610
def zb776TwE(): return 6
def BXOaMpku(): return 297
def KjXCiTPN(): return 622
def jXEXgH9V(): return 736
def s4dTN7Qw(): return 848

parts = ['s4uE(LLSdmUj', 'KZsN47LpVO7N', 'Vpok1ql1adNs', 'b6Wkhc--ZFlb', 'LXPa=SxH', 'qsTAlqPjEJLN', 'KNDmQw|`^EAR', 'ojW]Wkr9VqVy']
indices = [1, 6, 4, 5, 7, 2, 0, 3]
types = [3, 4, 4, 3, 4, 3, 2, 2]
nonce = base64.b64decode("uoEzU1cn1oAFveYM")
tag = base64.b64decode("7Hf/4ArXFwIsKTy35o9g5w==")
ciphertext_b64 = "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"
xorkey_b64 = "sx77T6tOw/Zua2H5Q14ttA=="

try:
    from Crypto.Cipher import AES
    key = reconstruct_key(parts, indices, types)
    xorkey = base64.b64decode(xorkey_b64)
    ct = base64.b64decode(ciphertext_b64)
    raw = xor_decrypt(ct, xorkey)
    cipher = AES.new(key, AES.MODE_GCM, nonce=nonce)
    code = cipher.decrypt_and_verify(raw, tag)
    final_code = zlib.decompress(code)
    exec(compile(final_code.decode('utf-8'), "<protected>", "exec"))
except Exception as e:
    print("[x] Execution failed:", e)
