"""
Data models for CampfireValley using Pydantic for type validation.
Extends the base pyCampfires models with CampfireValley-specific functionality.
"""

from pydantic import BaseModel, Field, field_validator
from typing import Optional, Dict, List, Any, Union
from datetime import datetime
from enum import Enum
import json
import base64
import gzip
from campfires import Torch as BaseTorch


class DockMode(str, Enum):
    """Dock visibility modes"""
    PUBLIC = "public"
    PARTIAL = "partial"
    PRIVATE = "private"


class SecurityLevel(str, Enum):
    """Security levels for valley operations"""
    BASIC = "basic"
    STANDARD = "standard"
    HIGH = "high"


class TrustLevel(str, Enum):
    """Trust levels for community membership"""
    BASIC = "basic"
    TRUSTED = "trusted"
    ADMIN = "admin"


class Torch(BaseTorch):
    """
    CampfireValley Torch extending the base pyCampfires Torch.
    Message container for inter-valley communication with enhanced routing and security.
    """
    # CampfireValley-specific fields
    sender_valley: str = Field(..., description="Valley that sent this torch")
    target_address: str = Field(..., description="Target address in format valley:name/campfire/camper")
    attachments: List[str] = Field(default_factory=list, description="List of attachment references")
    signature: str = Field(..., description="Digital signature for authentication")
    
    # Override base fields with CampfireValley defaults
    source: str = Field(default="", description="Source campfire/camper")
    destination: str = Field(default="", description="Destination campfire/camper")
    data: Dict[str, Any] = Field(default_factory=dict, description="Torch data payload")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Torch metadata")
    
    @field_validator('target_address')
    @classmethod
    def validate_address_format(cls, v):
        """Validate hierarchical address format: valley:name/campfire/camper"""
        if not v or ':' not in v:
            raise ValueError("Address must contain valley name with colon separator")
        return v
    
    @property
    def id(self) -> str:
        """Compatibility property that maps to torch_id"""
        return self.torch_id
    
    def to_redis_message(self, compress: bool = True) -> Dict[str, Any]:
        """
        Serialize torch to Redis-compatible message format
        
        Args:
            compress: Whether to compress the payload for large messages
            
        Returns:
            Dictionary ready for Redis transport
        """
        # Convert to dict with ISO timestamp
        data = self.dict()
        data['timestamp'] = self.timestamp.isoformat()
        
        # Optionally compress large payloads
        if compress and len(json.dumps(data['data'])) > 1024:  # 1KB threshold
            payload_json = json.dumps(data['data'])
            compressed = gzip.compress(payload_json.encode('utf-8'))
            data['data'] = {
                '_compressed': True,
                '_data': base64.b64encode(compressed).decode('ascii')
            }
        
        return {
            'type': 'torch',
            'version': '1.0',
            'data': data,
            'routing': {
                'sender': self.sender_valley,
                'target': self.target_address,
                'channel': self._get_routing_channel()
            }
        }
    
    @classmethod
    def from_redis_message(cls, message: Dict[str, Any]) -> 'Torch':
        """
        Deserialize torch from Redis message format
        
        Args:
            message: Redis message dictionary
            
        Returns:
            Torch instance
            
        Raises:
            ValueError: If message format is invalid
        """
        if message.get('type') != 'torch':
            raise ValueError(f"Invalid message type: {message.get('type')}")
        
        data = message.get('data', {})
        
        # Handle compressed payloads
        payload = data.get('data', {})
        if isinstance(payload, dict) and payload.get('_compressed'):
            compressed_data = base64.b64decode(payload['_data'])
            decompressed = gzip.decompress(compressed_data)
            data['data'] = json.loads(decompressed.decode('utf-8'))
        
        # Convert timestamp back to datetime
        if 'timestamp' in data:
            data['timestamp'] = datetime.fromisoformat(data['timestamp'])
        
        return cls(**data)
    
    def _get_routing_channel(self) -> str:
        """
        Generate Redis channel name for routing
        
        Returns:
            Channel name for Redis pub/sub
        """
        # Extract valley name from target address
        target_valley = self.target_address.split(':')[0]
        return f"campfire.valley.{target_valley}"
    
    def get_mcp_envelope(self) -> Dict[str, Any]:
        """
        Create MCP protocol envelope for this torch
        
        Returns:
            MCP-compatible message envelope
        """
        return {
            'jsonrpc': '2.0',
            'method': 'torch/deliver',
            'params': {
                'torch': self.to_redis_message(compress=False),
                'routing': {
                    'sender_valley': self.sender_valley,
                    'target_address': self.target_address,
                    'message_id': self.id,
                    'timestamp': self.timestamp.isoformat()
                }
            },
            'id': self.id
        }
    
    @classmethod
    def from_mcp_envelope(cls, envelope: Dict[str, Any]) -> 'Torch':
        """
        Extract torch from MCP protocol envelope
        
        Args:
            envelope: MCP message envelope
            
        Returns:
            Torch instance
            
        Raises:
            ValueError: If envelope format is invalid
        """
        if envelope.get('method') != 'torch/deliver':
            raise ValueError(f"Invalid MCP method: {envelope.get('method')}")
        
        params = envelope.get('params', {})
        torch_data = params.get('torch', {})
        
        return cls.from_redis_message(torch_data)
    
    def is_encrypted(self) -> bool:
        """
        Check if torch payload is encrypted
        
        Returns:
            True if payload appears to be encrypted
        """
        return (
            isinstance(self.payload, dict) and 
            '_encrypted' in self.payload and
            self.payload.get('_encrypted') is True
        )
    
    def get_size_estimate(self) -> int:
        """
        Estimate torch size in bytes for transport planning
        
        Returns:
            Estimated size in bytes
        """
        return len(json.dumps(self.dict(), default=str).encode('utf-8'))


class ValleyConfig(BaseModel):
    """Valley configuration from manifest.yaml following GitHub Actions/Ansible format"""
    name: str = Field(..., description="Valley name")
    version: str = Field(default="1.0", description="Configuration version")
    
    # Environment and runtime configuration
    env: Dict[str, Union[str, bool]] = Field(default_factory=lambda: {
        "dock_mode": DockMode.PRIVATE,
        "security_level": SecurityLevel.STANDARD,
        "auto_create_dock": True
    })
    
    # Campfire definitions similar to GitHub Actions jobs
    campfires: Dict[str, List[str]] = Field(default_factory=lambda: {
        "visible": [],
        "hidden": []
    })
    
    # Step-based dock configuration like Ansible tasks
    dock: Dict[str, List[Dict[str, Any]]] = Field(default_factory=lambda: {
        "steps": []
    })
    
    # Community and networking
    community: Dict[str, Union[bool, List[str]]] = Field(default_factory=lambda: {
        "discovery": False,
        "trusted_valleys": []
    })


class CampfireConfig(BaseModel):
    """Configuration for provisioned campfires following GitHub Actions job format"""
    name: str = Field(..., description="Campfire name")
    type: str = Field(default="Campfire", description="Type of campfire (Campfire, LLMCampfire, etc.)")
    runs_on: str = Field(default="valley", description="Where the campfire runs")
    
    # Environment variables like GitHub Actions
    env: Dict[str, str] = Field(default_factory=dict)
    
    # Strategy matrix for multiple configurations
    strategy: Dict[str, Dict[str, Any]] = Field(default_factory=lambda: {"matrix": {}})
    
    # Steps similar to GitHub Actions/Ansible tasks
    steps: List[Dict[str, Any]] = Field(default_factory=list)
    
    # Needs/dependencies like GitHub Actions
    needs: List[str] = Field(default_factory=list)
    
    # Conditional execution
    if_condition: Optional[str] = Field(None, alias="if")
    
    # Outputs for other campfires to use
    outputs: Dict[str, str] = Field(default_factory=dict)
    
    # Traditional campfire settings
    rag_paths: List[str] = Field(default_factory=list)
    auditor_enabled: bool = Field(default=True)
    channels: List[str] = Field(default_factory=list)
    
    # Additional configuration fields for specialized campfires
    description: Optional[str] = Field(None, description="Campfire description")
    llm: Dict[str, Any] = Field(default_factory=dict, description="LLM configuration")
    behavior: Dict[str, Any] = Field(default_factory=dict, description="Behavior configuration")
    torch_processing: Dict[str, Any] = Field(default_factory=dict, description="Torch processing rules")
    prompts: Dict[str, Any] = Field(default_factory=dict, description="LLM prompts")
    workflows: Dict[str, Any] = Field(default_factory=dict, description="Workflow definitions")
    performance: Dict[str, Any] = Field(default_factory=dict, description="Performance metrics")
    config: Dict[str, Any] = Field(default_factory=dict, description="Additional configuration")


class CommunityMembership(BaseModel):
    """Community membership information"""
    community_name: str = Field(..., description="Name of the community")
    alias: str = Field(..., description="Valley's alias in the community")
    key_hash: str = Field(..., description="Hash of the shared key")
    joined_at: datetime = Field(default_factory=datetime.utcnow)
    trust_level: TrustLevel = Field(default=TrustLevel.BASIC)


class VALIServiceRequest(BaseModel):
    """Valley Application Layer Interface service request"""
    service_type: str = Field(..., description="Type of service requested")
    request_id: str = Field(..., description="Unique request identifier")
    payload: Dict[str, Any] = Field(default_factory=dict)
    requirements: Dict[str, Any] = Field(default_factory=dict)
    deadline: Optional[datetime] = None


class VALIServiceResponse(BaseModel):
    """Valley Application Layer Interface service response"""
    request_id: str = Field(..., description="Original request identifier")
    status: str = Field(..., description="Response status: completed, in_progress, failed")
    deliverables: Dict[str, Any] = Field(default_factory=dict)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ScanResult(BaseModel):
    """Result from content security scanning"""
    is_safe: bool = Field(..., description="Whether content passed security checks")
    violations: List[str] = Field(default_factory=list)
    confidence_score: float = Field(default=1.0, ge=0.0, le=1.0)
    scan_timestamp: datetime = Field(default_factory=datetime.utcnow)


class Violation(BaseModel):
    """Security or policy violation record"""
    violation_id: str = Field(..., description="Unique violation identifier")
    violation_type: str = Field(..., description="Type of violation")
    severity: str = Field(..., description="Violation severity level")
    description: str = Field(..., description="Violation description")
    source_valley: str = Field(..., description="Valley that caused the violation")
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class Action(BaseModel):
    """Action to be taken in response to a violation"""
    action_type: str = Field(..., description="Type of action to take")
    target: str = Field(..., description="Target of the action")
    parameters: Dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class Decision(BaseModel):
    """Decision made during quarantine review"""
    decision_type: str = Field(..., description="Type of decision: approve, reject, escalate")
    reasoning: str = Field(..., description="Reasoning for the decision")
    reviewer: str = Field(..., description="Who made the decision")
    timestamp: datetime = Field(default_factory=datetime.utcnow)


# Federation-aware data models following the design specifications

class ValleyConfig(BaseModel):
    """Valley configuration from manifest.yaml following GitHub Actions/Ansible format"""
    name: str = Field(..., description="Valley name")
    version: str = Field(default="1.0", description="Configuration version")
    
    # Environment and runtime configuration
    env: Dict[str, Any] = Field(default_factory=lambda: {
        "dock_mode": "private",  # public, partial, private
        "security_level": "standard",  # basic, standard, high
        "auto_create_dock": True
    })
    
    # Campfire definitions similar to GitHub Actions jobs
    campfires: Dict[str, List[str]] = Field(default_factory=lambda: {
        "visible": [],
        "hidden": []
    })
    
    # Step-based dock configuration like Ansible tasks
    dock: Dict[str, List[Dict[str, Any]]] = Field(default_factory=lambda: {
        "steps": []  # Sequential dock setup steps
    })
    
    # Community and networking
    community: Dict[str, Any] = Field(default_factory=lambda: {
        "discovery": False,
        "trusted_valleys": []
    })
    
    @field_validator('env')
    @classmethod
    def validate_env_config(cls, v):
        """Validate environment configuration"""
        valid_dock_modes = ["public", "partial", "private"]
        valid_security_levels = ["basic", "standard", "high"]
        
        if v.get("dock_mode") not in valid_dock_modes:
            raise ValueError(f"dock_mode must be one of: {valid_dock_modes}")
        
        if v.get("security_level") not in valid_security_levels:
            raise ValueError(f"security_level must be one of: {valid_security_levels}")
        
        return v


class CommunityMembership(BaseModel):
    """Community membership information for federation"""
    community_name: str = Field(..., description="Name of the community")
    alias: str = Field(..., description="Valley's alias in the community")
    key_hash: str = Field(..., description="Hash of the community key")
    joined_at: datetime = Field(default_factory=datetime.utcnow)
    trust_level: TrustLevel = Field(default=TrustLevel.BASIC)
    
    @field_validator('community_name')
    @classmethod
    def validate_community_name(cls, v):
        """Validate community name format"""
        if not v or len(v) < 3:
            raise ValueError("Community name must be at least 3 characters")
        return v





class FederationMembership(BaseModel):
    """Federation membership tracking for valleys"""
    valley_id: str = Field(..., description="Unique valley identifier")
    federation_name: str = Field(..., description="Name of the federation")
    public_key: str = Field(..., description="Valley's public key for the federation")
    joined_at: datetime = Field(default_factory=datetime.utcnow)
    last_seen: datetime = Field(default_factory=datetime.utcnow)
    status: str = Field(default="active", description="Membership status: active, inactive, suspended")
    capabilities: List[str] = Field(default_factory=list, description="Services this valley provides")
    
    @field_validator('status')
    @classmethod
    def validate_status(cls, v):
        """Validate membership status"""
        valid_statuses = ["active", "inactive", "suspended"]
        if v not in valid_statuses:
            raise ValueError(f"Status must be one of: {valid_statuses}")
        return v


class VALIServiceRequest(BaseModel):
    """VALI (Valley Application Layer Interface) service request"""
    service_type: str = Field(..., description="Type of service requested")
    request_id: str = Field(..., description="Unique request identifier")
    payload: Dict[str, Any] = Field(default_factory=dict)
    requirements: Dict[str, Any] = Field(default_factory=dict)
    deadline: Optional[datetime] = Field(None, description="Service deadline")
    priority: str = Field(default="normal", description="Request priority: low, normal, high, urgent")
    
    @field_validator('priority')
    @classmethod
    def validate_priority(cls, v):
        """Validate request priority"""
        valid_priorities = ["low", "normal", "high", "urgent"]
        if v not in valid_priorities:
            raise ValueError(f"Priority must be one of: {valid_priorities}")
        return v


class VALIServiceResponse(BaseModel):
    """VALI service response"""
    request_id: str = Field(..., description="Original request identifier")
    status: str = Field(..., description="Response status")
    deliverables: Dict[str, Any] = Field(default_factory=dict)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    completed_at: Optional[datetime] = Field(None)
    
    @field_validator('status')
    @classmethod
    def validate_status(cls, v):
        """Validate response status"""
        valid_statuses = ["completed", "in_progress", "failed", "cancelled"]
        if v not in valid_statuses:
            raise ValueError(f"Status must be one of: {valid_statuses}")
        return v