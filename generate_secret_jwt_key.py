import secrets

def generate_secret_key():
    return secrets.token_hex(32)  # Generates a 64-character hexadecimal string

if __name__ == "__main__":
    print(generate_secret_key())
