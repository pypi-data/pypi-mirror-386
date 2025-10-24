import json
import os
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
from cryptography import x509
from cryptography.x509.oid import NameOID
import datetime

def generate_keypair():
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048,
        backend=default_backend()
    )
    public_key = private_key.public_key()
    return private_key, public_key

def serialize_public_key(public_key):
    return public_key.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo
    ).decode()

def deserialize_public_key(pem_data):
    return serialization.load_pem_public_key(
        pem_data.encode(),
        backend=default_backend()
    )

def serialize_private_key(private_key):
    return private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption()
    ).decode()

def deserialize_private_key(pem_data):
    return serialization.load_pem_private_key(
        pem_data.encode(),
        password=None,
        backend=default_backend()
    )

def encrypt_private_key(private_key, password):
    return private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.BestAvailableEncryption(password.encode())
    ).decode()

def decrypt_private_key(pem_data, password):
    return serialization.load_pem_private_key(
        pem_data.encode(),
        password=password.encode(),
        backend=default_backend()
    )

def encrypt_message(public_key, message):
    return public_key.encrypt(
        message.encode(),
        padding.OAEP(
            mgf=padding.MGF1(algorithm=hashes.SHA256()),
            algorithm=hashes.SHA256(),
            label=None
        )
    )

def decrypt_message(private_key, encrypted):
    return private_key.decrypt(
        encrypted,
        padding.OAEP(
            mgf=padding.MGF1(algorithm=hashes.SHA256()),
            algorithm=hashes.SHA256(),
            label=None
        )
    ).decode()

def sign_message(private_key, message):
    return private_key.sign(
        message.encode(),
        padding.PSS(
            mgf=padding.MGF1(hashes.SHA256()),
            salt_length=padding.PSS.MAX_LENGTH
        ),
        hashes.SHA256()
    )

def verify_signature(public_key, message, signature):
    try:
        public_key.verify(
            signature,
            message.encode(),
            padding.PSS(
                mgf=padding.MGF1(hashes.SHA256()),
                salt_length=padding.PSS.MAX_LENGTH
            ),
            hashes.SHA256()
        )
        return True
    except:
        return False

def generate_self_signed_cert(cert_file, key_file):
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048,
        backend=default_backend()
    )
    subject = issuer = x509.Name([
        x509.NameAttribute(NameOID.COUNTRY_NAME, "US"),
        x509.NameAttribute(NameOID.STATE_OR_PROVINCE_NAME, "CA"),
        x509.NameAttribute(NameOID.LOCALITY_NAME, "San Francisco"),
        x509.NameAttribute(NameOID.ORGANIZATION_NAME, "SecureChat"),
        x509.NameAttribute(NameOID.COMMON_NAME, "securechat.local"),
    ])
    cert = x509.CertificateBuilder().subject_name(
        subject
    ).issuer_name(
        issuer
    ).public_key(
        private_key.public_key()
    ).serial_number(
        x509.random_serial_number()
    ).not_valid_before(
        datetime.datetime.utcnow()
    ).not_valid_after(
        datetime.datetime.utcnow() + datetime.timedelta(days=365)
    ).add_extension(
        x509.SubjectAlternativeName([
            x509.DNSName("securechat.local"),
            x509.DNSName("localhost"),
        ]),
        critical=False,
    ).sign(private_key, hashes.SHA256(), default_backend())

    with open(cert_file, "wb") as f:
        f.write(cert.public_bytes(serialization.Encoding.PEM))
    
    with open(key_file, "wb") as f:
        f.write(private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption()
        ))

def validate_certificate(cert_pem, hostname=None):
    """Validate certificate is not expired and optionally matches hostname"""
    try:
        cert = x509.load_pem_x509_certificate(cert_pem.encode(), default_backend())
        current_time = datetime.datetime.now(datetime.timezone.utc)
        
        # Check expiration
        if current_time < cert.not_valid_before_utc or current_time > cert.not_valid_after_utc:
            return False, "Certificate expired or not yet valid"
        
        # Check hostname if provided
        if hostname:
            try:
                cert.verify_directly_issued_by(cert)  # Self-signed check
                # For self-signed, we accept localhost
                if hostname not in ['localhost', '127.0.0.1', '::1']:
                    return False, "Certificate hostname mismatch"
            except:
                return False, "Certificate validation failed"
        
        return True, "Certificate valid"
    except Exception as e:
        return False, f"Certificate parsing error: {e}"

def get_certificate_fingerprint(cert_pem, hash_algorithm=hashes.SHA256()):
    """Get certificate fingerprint"""
    try:
        cert = x509.load_pem_x509_certificate(cert_pem.encode(), default_backend())
        fingerprint = cert.fingerprint(hash_algorithm)
        return fingerprint.hex()
    except Exception as e:
        return None

def validate_certificate_pin(cert_pem, expected_fingerprints):
    """Validate certificate against pinned fingerprints"""
    if not expected_fingerprints:
        return True, "No pins configured"
    
    fingerprint = get_certificate_fingerprint(cert_pem)
    if fingerprint and fingerprint in expected_fingerprints:
        return True, "Certificate pinned"
    return False, f"Certificate fingerprint {fingerprint} not in pinned list"

def get_certificate_expiry(cert_pem):
    """Get certificate expiry date"""
    try:
        cert = x509.load_pem_x509_certificate(cert_pem.encode(), default_backend())
        return cert.not_valid_after_utc
    except:
        return None

def derive_group_key(group_name, master_key=b'securechat_master_key'):
    """Derive a symmetric key for group encryption"""
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=group_name.encode(),
        iterations=100000,
    )
    return kdf.derive(master_key)

def encrypt_symmetric(key, plaintext):
    """Encrypt with AES-GCM"""
    iv = os.urandom(12)
    cipher = Cipher(algorithms.AES(key), modes.GCM(iv))
    encryptor = cipher.encryptor()
    ciphertext = encryptor.update(plaintext.encode()) + encryptor.finalize()
    return iv + encryptor.tag + ciphertext

def decrypt_symmetric(key, ciphertext):
    """Decrypt with AES-GCM"""
    iv = ciphertext[:12]
    tag = ciphertext[12:28]
    encrypted_data = ciphertext[28:]
    cipher = Cipher(algorithms.AES(key), modes.GCM(iv, tag))
    decryptor = cipher.decryptor()
    return (decryptor.update(encrypted_data) + decryptor.finalize()).decode()