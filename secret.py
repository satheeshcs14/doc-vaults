import os

# Generate a random 24-byte (192-bit) secret key
secret_key = os.urandom(24)

# Convert the bytes to a hexadecimal representation
secret_key_hex = secret_key.hex()

# Print or store the secret_key_hex for later use in your Flask app
print(secret_key_hex)
