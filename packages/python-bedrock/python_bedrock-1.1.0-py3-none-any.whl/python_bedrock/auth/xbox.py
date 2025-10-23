"""Xbox Live authentication components."""
import aiohttp
import asyncio
import base64
import json
import time
import uuid
import jwt
from dataclasses import dataclass
from typing import Optional, Dict, Any, List, Tuple, Union
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.backends import default_backend

@dataclass
class XboxToken:
    """Xbox Live authentication token."""
    token: str
    user_hash: str
    xuid: str
    expires: int
    username: str = ""  # Gamertag
    identity: str = ""  # Identity string
    
    @property
    def is_expired(self) -> bool:
        """Check if token is expired."""
        return time.time() > self.expires
        
    @classmethod
    def from_token(cls, token: str) -> 'XboxToken':
        """Parse token data into XboxToken."""
        try:
            # Decode without verification
            payload = jwt.decode(
                token,
                options={"verify_signature": False}
            )
            claims = payload.get("DisplayClaims", {}).get("xui", [{}])[0]
            
            return cls(
                token=token,
                user_hash=claims.get("uhs", ""),
                xuid=claims.get("xid", ""),
                expires=int(time.time()) + payload.get("NotAfter", 0),
                username=claims.get("gtg", ""),
                identity=claims.get("agg", "")
            )
        except jwt.InvalidTokenError as e:
            raise ValueError(f"Invalid Xbox token: {e}")

@dataclass
class DeviceToken:
    """Xbox Live device token."""
    token: str
    device_id: str
    expires: int
    
    @property
    def is_expired(self) -> bool:
        """Check if token is expired."""
        return time.time() > self.expires

@dataclass
class TitleToken:
    """Xbox Live title token."""
    token: str
    title_id: str
    expires: int
    
    @property
    def is_expired(self) -> bool:
        """Check if token is expired."""
        return time.time() > self.expires

class XboxLiveAuth:
    """Xbox Live authentication manager."""
    
    USER_AGENT = "MCPE/UWP"
    TITLE_ID = "896928775"
    MS_AUTH_URL = "https://login.live.com/oauth20_token.srf"
    XBL_AUTH_URL = "https://xsts.auth.xboxlive.com/xsts/authorize"
    DEVICE_AUTH_URL = "https://device.auth.xboxlive.com/device/authenticate"
    TITLE_AUTH_URL = "https://title.auth.xboxlive.com/title/authenticate"
    
    def __init__(
        self,
        client_id: str = "0000000048183522",
        scope: str = "service::user.auth.xboxlive.com::MBI_SSL"
    ) -> None:
        """Initialize Xbox Live auth manager."""
        self.client_id = client_id
        self.scope = scope
        self.access_token: Optional[str] = None
        self.refresh_token: Optional[str] = None
        self.xbox_token: Optional[XboxToken] = None
        self.device_token: Optional[DeviceToken] = None
        self.title_token: Optional[TitleToken] = None
        self._session: Optional[aiohttp.ClientSession] = None
    
    async def __aenter__(self) -> 'XboxLiveAuth':
        """Enter async context."""
        self._session = aiohttp.ClientSession()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Exit async context."""
        if self._session:
            await self._session.close()
            
    async def authenticate(
        self,
        email: str,
        password: str
    ) -> Dict[str, Any]:
        """Authenticate with Xbox Live."""
        # Get Microsoft account tokens
        ms_tokens = await self._get_microsoft_token(email, password)
        self.access_token = ms_tokens["access_token"]
        self.refresh_token = ms_tokens["refresh_token"]
        
        # Get Xbox Live tokens
        await self._get_xbox_tokens()
        
        return {
            "access_token": self.access_token,
            "refresh_token": self.refresh_token,
            "xbox_token": self.xbox_token.token,
            "user_hash": self.xbox_token.user_hash,
            "xuid": self.xbox_token.xuid,
            "device_token": self.device_token.token,
            "title_token": self.title_token.token
        }
    
    async def refresh(self) -> Dict[str, Any]:
        """Refresh expired tokens."""
        if not self.refresh_token:
            raise ValueError("No refresh token available")
            
        # Refresh Microsoft token
        tokens = await self._refresh_microsoft_token(self.refresh_token)
        self.access_token = tokens["access_token"]
        self.refresh_token = tokens["refresh_token"]
        
        # Refresh Xbox tokens
        await self._get_xbox_tokens()
        
        return {
            "access_token": self.access_token,
            "refresh_token": self.refresh_token,
            "xbox_token": self.xbox_token.token,
            "user_hash": self.xbox_token.user_hash,
            "xuid": self.xbox_token.xuid,
            "device_token": self.device_token.token,
            "title_token": self.title_token.token
        }
        
    async def _get_xbox_tokens(self) -> None:
        """Get all required Xbox Live tokens."""
        # Get user token
        if not self.xbox_token or self.xbox_token.is_expired:
            self.xbox_token = await self._get_user_token()
            
        # Get device token 
        if not self.device_token or self.device_token.is_expired:
            self.device_token = await self._get_device_token()
            
        # Get title token
        if not self.title_token or self.title_token.is_expired:
            self.title_token = await self._get_title_token()
    
    def generate_chain(
        self,
        identity_public_key: str,
        client_random_id: Optional[str] = None
    ) -> Tuple[List[str], str]:
        """Generate authentication chain for login."""
        if not all([self.xbox_token, self.device_token, self.title_token]):
            raise ValueError("Missing required tokens")
            
        now = int(time.time())
        client_id = client_random_id or str(uuid.uuid4())
        
        # Create chain for auth certificate
        cert_payload = {
            "nbf": now,
            "exp": now + 24 * 60 * 60,  # 24 hours
            "iss": "https://xboxlive.com",
            "certificateAuthority": True,
            "identityPublicKey": identity_public_key
        }
        
        # Create chain for client data
        client_payload = {
            "extraData": {
                "XUID": self.xbox_token.xuid,
                "displayName": self.xbox_token.username,
                "identity": self.xbox_token.identity,
                "titleId": self.TITLE_ID
            },
            "identityPublicKey": identity_public_key,
            "nbf": now,
            "randomNonce": 0,  # Not used in Bedrock
            "iss": "https://xboxlive.com",
            "exp": now + 24 * 60 * 60,
            "iat": now,
            "certificateAuthority": True
        }
        
        # Sign chain and client data with Xbox key
        key = self._get_signing_key()
        chain_token = jwt.encode(
            cert_payload,
            key,
            algorithm="ES384", 
            headers={
                "x5u": identity_public_key,
                "alg": "ES384"
            }
        )
        
        # Add user/device/title tokens
        chain = [
            chain_token,
            self.xbox_token.token,
            self.device_token.token,
            self.title_token.token
        ]
        
        # Sign client data
        client_data = jwt.encode(
            client_payload,
            key,
            algorithm="ES384",
            headers={
                "x5u": identity_public_key,
                "alg": "ES384"
            }
        )
        
        return chain, client_data
        
    async def _get_microsoft_token(
        self,
        email: str,
        password: str
    ) -> Dict[str, Any]:
        """Get Microsoft OAuth tokens."""
        if not self._session:
            raise RuntimeError("Not in async context")
            
        auth_data = {
            "client_id": self.client_id,
            "scope": self.scope,
            "response_type": "token",
            "grant_type": "password",
            "username": email,
            "password": password
        }
        
        async with self._session.post(
            self.MS_AUTH_URL,
            data=auth_data
        ) as resp:
            if resp.status != 200:
                raise ValueError(f"Auth failed: {await resp.text()}")
                
            data = await resp.json()
            return {
                "access_token": data["access_token"],
                "refresh_token": data["refresh_token"],
                "expires_in": data["expires_in"]
            }
            
    async def _refresh_microsoft_token(
        self,
        refresh_token: str
    ) -> Dict[str, Any]:
        """Refresh Microsoft OAuth tokens."""
        if not self._session:
            raise RuntimeError("Not in async context")
            
        refresh_data = {
            "client_id": self.client_id,
            "scope": self.scope,
            "grant_type": "refresh_token",
            "refresh_token": refresh_token
        }
        
        async with self._session.post(
            self.MS_AUTH_URL,
            data=refresh_data
        ) as resp:
            if resp.status != 200:
                raise ValueError(f"Refresh failed: {await resp.text()}")
                
            data = await resp.json()
            return {
                "access_token": data["access_token"],
                "refresh_token": data["refresh_token"],
                "expires_in": data["expires_in"]
            }
            
    async def _get_user_token(self) -> XboxToken:
        """Get Xbox Live user token."""
        if not self._session or not self.access_token:
            raise RuntimeError("Not authenticated")
            
        req_data = {
            "RelyingParty": "http://xboxlive.com",
            "TokenType": "JWT",
            "Properties": {
                "AuthMethod": "RPS",
                "SiteName": "user.auth.xboxlive.com",
                "RpsTicket": f"d={self.access_token}"
            }
        }
        
        async with self._session.post(
            self.XBL_AUTH_URL,
            json=req_data,
            headers={"Content-Type": "application/json"}
        ) as resp:
            if resp.status != 200:
                raise ValueError(f"XBL auth failed: {await resp.text()}")
                
            data = await resp.json()
            return XboxToken(
                token=data["Token"],
                user_hash=data["DisplayClaims"]["xui"][0]["uhs"],
                xuid=data["DisplayClaims"]["xui"][0]["xid"],
                username=data["DisplayClaims"]["xui"][0]["gtg"],
                identity=data["DisplayClaims"]["xui"][0]["agg"],
                expires=int(time.time()) + data["NotAfter"]
            )
            
    async def _get_device_token(self) -> DeviceToken:
        """Get Xbox Live device token."""
        if not self._session:
            raise RuntimeError("Not in async context")
            
        device_id = str(uuid.uuid4())
        req_data = {
            "RelyingParty": "http://auth.xboxlive.com",
            "TokenType": "JWT",
            "Properties": {
                "DeviceType": "Nintendo",
                "DeviceVersion": "0.0.0",
                "DeviceId": device_id
            }
        }
        
        async with self._session.post(
            self.DEVICE_AUTH_URL,
            json=req_data,
            headers={"Content-Type": "application/json"}
        ) as resp:
            if resp.status != 200:
                raise ValueError(f"Device auth failed: {await resp.text()}")
                
            data = await resp.json()
            return DeviceToken(
                token=data["Token"],
                device_id=device_id,
                expires=int(time.time()) + data["NotAfter"]
            )
            
    async def _get_title_token(self) -> TitleToken:
        """Get Xbox Live title token."""
        if not self._session or not self.xbox_token:
            raise RuntimeError("Not authenticated")
            
        req_data = {
            "RelyingParty": "http://auth.xboxlive.com",
            "TokenType": "JWT",
            "Properties": {
                "DeviceToken": self.device_token.token,
                "UserToken": self.xbox_token.token,
                "TitleID": self.TITLE_ID,
                "DeviceId": self.device_token.device_id
            }
        }
        
        async with self._session.post(
            self.TITLE_AUTH_URL,
            json=req_data,
            headers={"Content-Type": "application/json"}
        ) as resp:
            if resp.status != 200:
                raise ValueError(f"Title auth failed: {await resp.text()}")
                
            data = await resp.json()
            return TitleToken(
                token=data["Token"],
                title_id=self.TITLE_ID,
                expires=int(time.time()) + data["NotAfter"]
            )
            
    def _get_signing_key(self) -> ec.EllipticCurvePrivateKey:
        """Get key for signing tokens."""
        return ec.generate_private_key(
            ec.SECP384R1(),
            default_backend()
        )