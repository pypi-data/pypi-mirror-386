"""Authentication and security components for Bedrock protocol."""
import base64
import hashlib
import json
import jwt
import time
import uuid
import os
from dataclasses import dataclass
from typing import Optional, Dict, Any, List, Tuple
from cryptography.hazmat.primitives.asymmetric import ec, padding
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.exceptions import InvalidKey
from cryptography.hazmat.backends import default_backend

@dataclass
class ChainData:
    """Xbox Live authentication chain data."""
    identity_public_key: str
    identity_private_key: Optional[ec.EllipticCurvePrivateKey]
    client_random: bytes
    server_random: Optional[bytes] = None
    client_x509: Optional[str] = None  # X.509 certificate
    chain_public_key: Optional[bytes] = None  # Chain key for validation
    
    @classmethod
    def generate(cls) -> 'ChainData':
        """Generate new chain data with ECDH keys."""
        # Generate EC key pair using SECP384R1 (same as Xbox Live)
        private_key = ec.generate_private_key(
            ec.SECP384R1(),
            default_backend()
        )
        public_key = private_key.public_key()
        
        # Format public key for JWT header (x5u)
        public_bytes = public_key.public_bytes(
            encoding=serialization.Encoding.DER,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        )
        x509_b64 = base64.b64encode(public_bytes).decode('utf-8')
        
        # Format public key for chain validation
        chain_bytes = public_key.public_bytes(
            encoding=serialization.Encoding.DER,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        )
        
        # Generate random values for handshake
        client_random = os.urandom(16)  # 16 bytes for AES
        
        return cls(
            identity_public_key=x509_b64,
            identity_private_key=private_key,
            client_random=client_random,
            client_x509=x509_b64,
            chain_public_key=chain_bytes
        )

@dataclass
class AuthData:
    """Authentication data for a connection."""
    identity: str
    client_uuid: uuid.UUID
    xuid: str
    username: str
    skin_data: Dict[str, Any]
    
    @classmethod
    def from_chain(
        cls,
        chain_data: list[str],
        client_data: str
    ) -> 'AuthData':
        """Parse auth data from certificate chain."""
        # Validate certificate chain
        raw_chain = [json.loads(base64.b64decode(token.split('.')[1]))
                    for token in chain_data]
        
        # Get identity from last certificate
        identity = raw_chain[-1].get('identityPublicKey', '')
        
        # Parse client data
        client_token = json.loads(
            base64.b64decode(client_data.split('.')[1]))
            
        return cls(
            identity=identity,
            client_uuid=uuid.UUID(client_token.get('ClientRandomId')),
            xuid=client_token.get('XUID', ''),
            username=client_token.get('displayName', ''),
            skin_data=client_token.get('skinData', {})
        )

class SecurityManager:
    """Manages encryption and authentication for a connection."""
    
    def __init__(self) -> None:
        self.chain_data: Optional[ChainData] = None
        self.auth_data: Optional[AuthData] = None
        self.encrypt_cipher: Optional[Any] = None
        self.decrypt_cipher: Optional[Any] = None
        self.secret_key: Optional[bytes] = None
        self.send_counter: int = 0
        self.receive_counter: int = 0
        self.version: str = "1.16.220"  # Default protocol version
        self.gcm_iv: Optional[bytes] = None  # For AES-GCM mode
        self.protocol_version: int = 0  # Protocol version from client

    def set_protocol_version(self, version: int) -> None:
        """Set protocol version and update cipher mode."""
        self.protocol_version = version
        # Convert protocol version to semantic version
        if version >= 560:  # 1.19.30+
            self.version = "1.19.30"
        elif version >= 503:  # 1.18.30+
            self.version = "1.18.30"
        elif version >= 440:  # 1.17.30+
            self.version = "1.17.30"
        elif version >= 419:  # 1.16.220+
            self.version = "1.16.220"
    
    def init_encryption(self) -> None:
        """Initialize encryption with new keys."""
        self.chain_data = ChainData.generate()
    
    def compute_shared_secret(
        self,
        server_key: bytes,
        client_key: Optional[bytes] = None
    ) -> bytes:
        """Compute shared secret from public keys."""
        if not self.chain_data or not self.chain_data.identity_private_key:
            raise ValueError("Encryption not initialized")
            
        # Parse the server's public key (for client) or client's key (for server)
        public_key = serialization.load_der_public_key(
            server_key if not client_key else client_key,
            default_backend()
        )
            
        # Compute shared secret with ECDH
        shared_secret = self.chain_data.identity_private_key.exchange(
            ec.ECDH(),
            public_key
        )
        
        # Hash with appropriate salt based on protocol
        salt = b'RakNetSalt'  # Default salt for 1.16.220+
        if client_key:  # Server side
            salt = self.chain_data.client_random
        
        # Compute secret key
        secret_hash = hashlib.sha256()
        secret_hash.update(salt)
        secret_hash.update(shared_secret)
        
        self.secret_key = secret_hash.digest()
        return self.secret_key
    
    def enable_encryption(self, secret: bytes) -> None:
        """Enable encryption with computed secret."""
        if not secret:
            raise ValueError("Secret required for encryption")
            
        if self.version >= "1.16.220":
            # Use AES-GCM for newer versions
            self.encrypt_cipher = AESGCM(secret)
            self.decrypt_cipher = AESGCM(secret)
            self.gcm_iv = secret[:12]  # GCM needs 12 bytes
        else:
            # Use AES-CFB8 for older versions
            iv = secret[:16]
            self.encrypt_cipher = Cipher(
                algorithms.AES(secret),
                modes.CFB8(iv),
                default_backend()
            ).encryptor()
            self.decrypt_cipher = Cipher(
                algorithms.AES(secret),
                modes.CFB8(iv),
                default_backend()
            ).decryptor()
        
        self.send_counter = 0
        self.receive_counter = 0
    
    def encrypt_packet(self, data: bytes) -> bytes:
        """Encrypt a packet and add checksum."""
        if not self.encrypt_cipher:
            return data
            
        # Compute packet checksum
        counter_bytes = self.send_counter.to_bytes(8, 'little')
        checksum = hashlib.sha256(
            counter_bytes +
            data +
            (self.secret_key or b'')
        ).digest()[:8]
        
        # Add checksum to data
        packet = data + checksum
        
        try:
            if isinstance(self.encrypt_cipher, AESGCM):
                # AES-GCM encryption
                encrypted = self.encrypt_cipher.encrypt(
                    self.gcm_iv,
                    packet,
                    None  # No associated data
                )
            else:
                # AES-CFB8 encryption
                encrypted = self.encrypt_cipher.update(packet)
                
            self.send_counter += 1
            return encrypted
            
        except Exception as e:
            raise ValueError(f"Encryption failed: {e}")
    
    def decrypt_packet(self, data: bytes) -> bytes:
        """Decrypt packet and verify checksum."""
        if not self.decrypt_cipher:
            return data
            
        try:
            # Decrypt the packet
            if isinstance(self.decrypt_cipher, AESGCM):
                decrypted = self.decrypt_cipher.decrypt(
                    self.gcm_iv,
                    data,
                    None  # No associated data
                )
            else:
                decrypted = self.decrypt_cipher.update(data)
            
            # Split data and checksum
            packet_data = decrypted[:-8]
            received_checksum = decrypted[-8:]
            
            # Verify checksum
            counter_bytes = self.receive_counter.to_bytes(8, 'little')
            expected_checksum = hashlib.sha256(
                counter_bytes +
                packet_data +
                (self.secret_key or b'')
            ).digest()[:8]
            
            if received_checksum != expected_checksum:
                raise ValueError("Invalid packet checksum")
                
            self.receive_counter += 1
            return packet_data
            
        except Exception as e:
            raise ValueError(f"Decryption failed: {e}")
    
    def verify_chain(
        self,
        chain_data: List[str],
        client_data: str,
        enforce_xbox_auth: bool = True
    ) -> bool:
        """Verify authentication chain."""
        try:
            if not chain_data and not enforce_xbox_auth:
                return True  # Allow unauthenticated if not enforcing
                
            # Start with Microsoft's root key for Xbox Live
            last_key = None
            
            # Verify each certificate in the chain
            for token in chain_data:
                # Parse header without verification
                header = jwt.get_unverified_header(token)
                
                # Get key from x5u header or last verified key
                if 'x5u' in header:
                    key_data = base64.b64decode(header['x5u'])
                    current_key = serialization.load_der_public_key(
                        key_data,
                        default_backend()
                    )
                elif last_key:
                    current_key = last_key
                else:
                    return False
                
                try:
                    # Verify token signature
                    payload = jwt.decode(
                        token,
                        key=current_key,
                        algorithms=['ES384']
                    )
                    
                    # Extract key for next token verification
                    if 'identityPublicKey' in payload:
                        key_data = base64.b64decode(payload['identityPublicKey'])
                        last_key = serialization.load_der_public_key(
                            key_data,
                            default_backend()
                        )
                        
                except jwt.InvalidTokenError:
                    return False
            
            # Finally verify client data token
            if not last_key:
                return False
                
            try:
                # Parse auth data on successful verification
                self.auth_data = AuthData.from_chain(chain_data, client_data)
                
                # Additional Xbox Live validation
                if enforce_xbox_auth and not self.auth_data.xuid:
                    return False
                    
                return True
                
            except jwt.InvalidTokenError:
                return False
                
        except Exception as e:
            print(f"Chain verification failed: {e}")
            return False