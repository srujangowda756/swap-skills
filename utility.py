from passlib.context import CryptContext

crypto=CryptContext(schemes=["bycrypt"])

def hash_password(password):
    return crypto.hash(password)

def verify_password(plain_password,hashed_password):
    return crypto.verify(plain_password,hash_password)