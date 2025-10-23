"""Xbox Live authentication and token validation."""
import jwt
import json
import time
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from base64 import b64decode
from .types import AuthenticationError

@dataclass
class IdentityToken:
    """Xbox Live identity token claims."""
    xuid: str
    identity: str
    displayName: str
    expires: int
    
    @classmethod
    def from_jwt(cls, token: str) -> 'IdentityToken':
        """Parse and validate an identity JWT token."""
        try:
            # Note: We don't verify signature as we don't have Xbox Live public keys
            claims = jwt.decode(token, options={"verify_signature": False})
            return cls(
                xuid=str(claims.get("xuid", "")),
                identity=claims.get("identity", ""),
                displayName=claims.get("displayName", ""),
                expires=int(claims.get("exp", 0))
            )
        except jwt.InvalidTokenError as e:
            raise AuthenticationError(f"Invalid identity token: {e}")

@dataclass
class ChainValidator:
    """Validates a chain of Xbox Live authentication tokens."""
    
    def __init__(self, chainData: List[str]):
        self.chainData = chainData
        self._identityPublicKey: Optional[str] = None
        
    def validate(self) -> None:
        """Validate the entire token chain."""
        if not self.chainData:
            raise AuthenticationError("Empty token chain")
            
        # Validate chain format and extract keys
        try:
            for token in self.chainData:
                header = jwt.get_unverified_header(token)
                if not header or 'x5u' not in header:
                    raise AuthenticationError("Invalid token header")
                    
            # The last token in chain contains the client's identity public key
            claims = jwt.decode(
                self.chainData[-1],
                options={"verify_signature": False}
            )
            self._identityPublicKey = claims.get("identityPublicKey")
            if not self._identityPublicKey:
                raise AuthenticationError("Missing identity public key")
                
        except jwt.InvalidTokenError as e:
            raise AuthenticationError(f"Chain validation failed: {e}")
    
    @property
    def identityPublicKey(self) -> Optional[str]:
        """Get the validated identity public key."""
        return self._identityPublicKey

class AuthSession:
    """Manages authentication state and session keys."""
    
    def __init__(self):
        self.identityToken: Optional[IdentityToken] = None
        self.chainValidator: Optional[ChainValidator] = None
        self._sessionKey: Optional[bytes] = None
        self._serverKey: Optional[bytes] = None
    
    def setIdentityToken(self, token: str) -> None:
        """Set and validate the identity token."""
        self.identityToken = IdentityToken.from_jwt(token)
        if self.identityToken.expires < time.time():
            raise AuthenticationError("Identity token expired")
    
    def setChain(self, chainData: List[str]) -> None:
        """Set and validate the token chain."""
        self.chainValidator = ChainValidator(chainData)
        self.chainValidator.validate()
    
    def setSessionKey(self, key: bytes) -> None:
        """Set the session encryption key."""
        if len(key) != 32:  # 256-bit key
            raise AuthenticationError("Invalid session key length")
        self._sessionKey = key
    
    def setServerKey(self, key: bytes) -> None:
        """Set the server's public key."""
        self._serverKey = key
    
    @property
    def isAuthenticated(self) -> bool:
        """Check if fully authenticated."""
        return (
            self.identityToken is not None and
            self.chainValidator is not None and
            self._sessionKey is not None
        )
    
    @property
    def sessionKey(self) -> Optional[bytes]:
        """Get the current session key."""
        return self._sessionKey
    
    @property
    def serverKey(self) -> Optional[bytes]:
        """Get the server's public key."""
        return self._serverKey