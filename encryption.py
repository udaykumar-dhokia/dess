import nacl.encoding
import nacl.public
import nacl.secret
import nacl.utils
import base64
import json

# Function to generate NaCl keys
def generate_keys():
    # Generate a new key pair
    private_key = nacl.public.PrivateKey.generate()
    public_key = private_key.public_key

    # Encode the keys to a format that can be stored and transmitted
    return public_key.encode(encoder=nacl.encoding.Base64Encoder).decode('utf-8'), \
           private_key.encode(encoder=nacl.encoding.Base64Encoder).decode('utf-8')

def load_private_key(private_key_str):
    return nacl.public.PrivateKey(private_key_str.encode('utf-8'), encoder=nacl.encoding.Base64Encoder)

def load_public_key(public_key_str):
    return nacl.public.PublicKey(public_key_str.encode('utf-8'), encoder=nacl.encoding.Base64Encoder)

# Function to encrypt the email body
def encrypt_message(message, public_key_str):
    public_key = load_public_key(public_key_str)
    box = nacl.public.SealedBox(public_key)
    encrypted_message = box.encrypt(message.encode('utf-8'))
    return base64.b64encode(encrypted_message).decode('utf-8')

# Function to decrypt the email body
def decrypt_message(encrypted_message, private_key_str):
    private_key = load_private_key(private_key_str)
    box = nacl.public.SealedBox(private_key)

    # Decode the base64 encoded message
    encrypted_data = base64.b64decode(encrypted_message)
    decrypted_message = box.decrypt(encrypted_data)
    return decrypted_message.decode('utf-8')
