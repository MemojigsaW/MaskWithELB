import hashlib, binascii
import random

def encrypt_to_hex(s_pw:str, s_salt:str) -> str:
    b_dk = hashlib.pbkdf2_hmac('sha256', s_pw.encode(),s_salt.encode(), 100000)
    return str(binascii.hexlify(b_dk), 'utf-8')

def gen_salt() -> str:
    ALPHABET = "0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"
    return "".join(random.choice(ALPHABET) for i in range(16))
