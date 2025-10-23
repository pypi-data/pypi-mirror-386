#IMAD 213 RSA PYTHON
import sys, base64, zlib, os
from Crypto.Cipher import AES

def fake1(x): return x[::-1]
def unfake1(x): return x[::-1]
def fake2(x): return ''.join(chr(ord(c) ^ 0x5A) for c in x)
def unfake2(x): return ''.join(chr(ord(c) ^ 0x5A) for c in x)
def fake3(x): return ''.join(chr((ord(c)+7)%256) for c in x)
def unfake3(x): return ''.join(chr((ord(c)-7)%256) for c in x)
def fake4(x): return ''.join(chr((ord(c)-7)%256) for c in x)
def unfake4(x): return ''.join(chr((ord(c)+7)%256) for c in x)
def fake5(x): return x.swapcase()
def unfake5(x): return x.swapcase()
fake_funcs = [fake1, fake2, fake3, fake4, fake5]
unfake_funcs = [unfake1, unfake2, unfake3, unfake4, unfake5]

def xor_decrypt(data: bytes, key: bytes):
    return bytes([b ^ key[i % len(key)] for i, b in enumerate(data)])

def reconstruct_key(parts, indices, types):
    ordered = [None]*len(parts)
    for i, idx in enumerate(indices):
        part = parts[i][2:-2]
        func = unfake_funcs[types[i]]
        part = func(part)
        ordered[idx] = part
    key_b64 = ''.join(ordered)
    missing = len(key_b64) % 4
    if missing: key_b64 += "=" * (4-missing)
    return base64.b64decode(key_b64)

#IMAD 213 FUCK RSA
def TSFgpvxf78(): return 41
def z5qaFa0V4r(): return 59
def wuX9GUDikH(): return 99
def V7mpwVAuYA(): return 35
def yF6F44ZrKy(): return 68
def Bp3Fcvo4GQ(): return 48
def Jqo0UrqPwI(): return 2
def fVLE6rnTI0(): return 80
def x2P8WGAWt2(): return 72
def twBYgYRyRC(): return 32
def VQsACvpaLv(): return 85
def VHRa73VTXP(): return 80

parts = ['LJ1Li1^apV', 'R6uj3CloiO', 'Id``:6<;ut', 'arSN:MrrNs', 'ra;Dsq', 'kY9jQ\\U~KK', 'A2n\x11\x1en\t0GK', 'gZ\x1f q\x19\x19\x13H6']
indices = [3, 2, 4, 1, 7, 6, 0, 5]
types = [3, 4, 2, 3, 2, 2, 1, 1]

nonce = base64.b64decode("jV6lAZJTXbsTi+xd")
tag = base64.b64decode("gICMt7JSoyswcnb8twWx3A==")
ciphertext_b64 = "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"
xorkey_b64 = "Mbi7+dHZEnWUFhHJdhJypA=="

if any(x in os.environ for x in ["PYCHARM_HOSTED", "VIRTUAL_ENV"]) or "PYDEV_DEBUGGER" in sys.modules:
    print("Debugging/VM Detected! Exiting.")
    sys.exit(1)

try:
    key = reconstruct_key(parts, indices, types)
    xorkey = base64.b64decode(xorkey_b64)
    data = base64.b64decode(ciphertext_b64)
    data = xor_decrypt(data, xorkey)
    cipher = AES.new(key, AES.MODE_GCM, nonce=nonce)
    dec = cipher.decrypt_and_verify(data, tag)
    exec(zlib.decompress(dec).decode('utf-8'))
except Exception as e:
    print("\n[!] Error during decryption or execution:", e)
    sys.exit(1)
