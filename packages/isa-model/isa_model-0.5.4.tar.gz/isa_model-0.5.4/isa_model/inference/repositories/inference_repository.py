"""
Inference Repository - Data persistence layer for inference operations

Provides standardized data access for inference requests, usage statistics, and history
following the ISA Model architecture pattern.

Now using PostgreSQL via PostgresClient (similar to auth_service pattern).
"""

import logging
import json
import uuid
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Any, Union
from pathlib import Path
from dataclasses import dataclass, asdict
from enum import Enum
from decimal import Decimal

# Import PostgresClient from isa_common
try:
    import sys
    import os
    # Add path to isa_common if needed
    sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))
    from isa_common.postgres_client import PostgresClient
    POSTGRES_AVAILABLE = True
except ImportError as e:
    logger.warning(f"PostgresClient not available: {e}")
    POSTGRES_AVAILABLE = False
    PostgresClient = None

logger = logging.getLogger(__name__)

class InferenceStatus(str, Enum):
    """Inference status enumeration"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    TIMEOUT = "timeout"
    CANCELLED = "cancelled"

class ServiceType(str, Enum):
    """Service type enumeration"""
    LLM = "llm"
    VISION = "vision"
    EMBEDDING = "embedding"
    TTS = "tts"
    STT = "stt"
    IMAGE_GEN = "image_gen"
    AUDIO = "audio"
    RERANK = "rerank"
    OCR = "ocr"

@dataclass
class InferenceRequest:
    """Inference request record"""
    request_id: str
    service_type: str
    model_id: str
    provider: str
    endpoint: str
    request_data: Dict[str, Any]
    status: str = InferenceStatus.PENDING
    created_at: datetime = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    response_data: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    execution_time_ms: Optional[int] = None
    tokens_used: Optional[int] = None
    cost_usd: Optional[float] = None
    metadata: Optional[Dict[str, Any]] = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now(timezone.utc)

@dataclass
class UsageStatistics:
    """Usage statistics record"""
    stat_id: str
    period_start: datetime
    period_end: datetime
    service_type: str
    model_id: Optional[str] = None
    provider: Optional[str] = None
    user_id: Optional[str] = None
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    total_tokens: int = 0
    total_cost_usd: float = 0.0
    avg_response_time_ms: float = 0.0
    p95_response_time_ms: float = 0.0
    requests_per_hour: float = 0.0
    error_rate: float = 0.0
    created_at: datetime = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now(timezone.utc)

@dataclass
class ModelUsageSnapshot:
    """Model usage snapshot for quick analytics"""
    snapshot_id: str
    model_id: str
    provider: str
    snapshot_time: datetime
    hourly_requests: int = 0
    daily_requests: int = 0
    weekly_requests: int = 0
    monthly_requests: int = 0
    total_tokens_today: int = 0
    total_cost_today: float = 0.0
    avg_response_time_today: float = 0.0
    success_rate_today: float = 100.0
    last_used: Optional[datetime] = None
    
    def __post_init__(self):
        if self.snapshot_time is None:
            self.snapshot_time = datetime.now(timezone.utc)

class InferenceRepository:
    """
    Repository for inference data persistence using PostgreSQL

    Uses PostgresClient (gRPC) following the auth_service architecture pattern.
    Storage backend options removed - PostgreSQL only.
    """

    def __init__(self, host: str = 'isa-postgres-grpc', port: int = 50061,
                 user_id: str = 'inference-service', **kwargs):
        """
        Initialize inference repository with PostgreSQL

        Args:
            host: PostgreSQL gRPC server host
            port: PostgreSQL gRPC server port
            user_id: Service user ID for tracking
            **kwargs: Additional configuration (for backwards compatibility)
        """
        if not POSTGRES_AVAILABLE:
            logger.error("PostgresClient is required but not available")
            # Fallback to file system for backwards compatibility
            self.storage_backend = "file"
            self._init_file_system(kwargs)
            return

        self.storage_backend = "postgres"
        self.db = PostgresClient(host=host, port=port, user_id=user_id)
        self.schema = "model_inference"

        # Table names
        self.requests_table = "inference_requests"
        self.statistics_table = "usage_statistics"
        self.snapshots_table = "model_usage_snapshots"

        logger.info(f"Inference repository initialized with PostgreSQL backend (schema: {self.schema})")

    def _init_file_system(self, config: Dict[str, Any]):
        """Initialize file system backend as fallback"""
        self.data_dir = Path(config.get("data_dir", "./inference_data"))
        self.data_dir.mkdir(parents=True, exist_ok=True)

        # Create subdirectories
        (self.data_dir / "requests").mkdir(exist_ok=True)
        (self.data_dir / "statistics").mkdir(exist_ok=True)
        (self.data_dir / "snapshots").mkdir(exist_ok=True)

        logger.warning(f"File system fallback backend initialized: {self.data_dir}")

    def _init_memory(self):
        """Initialize in-memory backend for testing"""
        self.requests = {}
        self.statistics = {}
        self.snapshots = {}
        logger.info("In-memory backend initialized for inference")
    
    # Request Management Methods

    def create_inference_request(
        self,
        service_type: str,
        model_id: str,
        provider: str,
        endpoint: str,
        request_data: Dict[str, Any],
        user_id: Optional[str] = None,
        session_id: Optional[str] = None,
        client_id: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """Create a new inference request record"""
        request_id = f"inf_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}"

        if self.storage_backend == "postgres":
            return self._create_request_postgres(
                request_id, service_type, model_id, provider, endpoint,
                request_data, user_id, session_id, client_id, ip_address, user_agent, metadata
            )
        elif self.storage_backend == "memory":
            request = InferenceRequest(
                request_id=request_id, service_type=service_type, model_id=model_id,
                provider=provider, endpoint=endpoint, request_data=request_data,
                user_id=user_id, session_id=session_id, client_id=client_id,
                ip_address=ip_address, user_agent=user_agent, metadata=metadata
            )
            return self._create_request_memory(request)
        else:
            request = InferenceRequest(
                request_id=request_id, service_type=service_type, model_id=model_id,
                provider=provider, endpoint=endpoint, request_data=request_data,
                user_id=user_id, session_id=session_id, client_id=client_id,
                ip_address=ip_address, user_agent=user_agent, metadata=metadata
            )
            return self._create_request_file(request)
    
    def update_inference_status(
        self,
        request_id: str,
        status: str,
        response_data: Optional[Dict[str, Any]] = None,
        error_message: Optional[str] = None,
        error_category: Optional[str] = None,
        execution_time_ms: Optional[int] = None,
        tokens_used: Optional[int] = None,
        input_tokens: Optional[int] = None,
        output_tokens: Optional[int] = None,
        cost_usd: Optional[float] = None,
        additional_updates: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Update inference request status and results"""
        now = datetime.now(timezone.utc)
        updates = {"status": status}

        # Update timestamps based on status
        if status == InferenceStatus.PROCESSING:
            updates["started_at"] = now
        elif status in [InferenceStatus.COMPLETED, InferenceStatus.FAILED,
                       InferenceStatus.TIMEOUT, InferenceStatus.CANCELLED]:
            updates["completed_at"] = now

        # Add optional fields
        if response_data is not None:
            updates["response_data"] = response_data
        if error_message is not None:
            updates["error_message"] = error_message
        if error_category is not None:
            updates["error_category"] = error_category
        if execution_time_ms is not None:
            updates["execution_time_ms"] = execution_time_ms
        if tokens_used is not None:
            updates["tokens_used"] = tokens_used
        if input_tokens is not None:
            updates["input_tokens"] = input_tokens
        if output_tokens is not None:
            updates["output_tokens"] = output_tokens
        if cost_usd is not None:
            updates["cost_usd"] = Decimal(str(cost_usd))

        if additional_updates:
            updates.update(additional_updates)

        if self.storage_backend == "postgres":
            return self._update_request_postgres(request_id, updates)
        elif self.storage_backend == "memory":
            return self._update_request_memory(request_id, updates)
        else:
            return self._update_request_file(request_id, updates)
    
    def get_inference_request(self, request_id: str) -> Optional[InferenceRequest]:
        """Get inference request by ID"""
        if self.storage_backend == "postgres":
            return self._get_request_postgres(request_id)
        elif self.storage_backend == "memory":
            return self._get_request_memory(request_id)
        else:
            return self._get_request_file(request_id)

    def list_recent_requests(
        self,
        service_type: Optional[str] = None,
        model_id: Optional[str] = None,
        user_id: Optional[str] = None,
        status: Optional[str] = None,
        hours: int = 24,
        limit: int = 100
    ) -> List[InferenceRequest]:
        """List recent inference requests with optional filtering"""
        if self.storage_backend == "postgres":
            return self._list_requests_postgres(service_type, model_id, user_id, status, hours, limit)
        elif self.storage_backend == "memory":
            return self._list_requests_memory(service_type, model_id, user_id, status, hours, limit)
        else:
            return self._list_requests_file(service_type, model_id, user_id, status, hours, limit)
    
    # Usage Statistics Methods
    
    def record_usage_statistics(
        self,
        period_start: datetime,
        period_end: datetime,
        service_type: str,
        model_id: Optional[str] = None,
        provider: Optional[str] = None,
        user_id: Optional[str] = None,
        total_requests: int = 0,
        successful_requests: int = 0,
        failed_requests: int = 0,
        total_tokens: int = 0,
        total_cost_usd: float = 0.0,
        avg_response_time_ms: float = 0.0,
        p95_response_time_ms: float = 0.0,
        requests_per_hour: float = 0.0,
        error_rate: float = 0.0
    ) -> str:
        """Record usage statistics for a time period"""
        stat_id = f"stat_{period_start.strftime('%Y%m%d_%H')}_{uuid.uuid4().hex[:6]}"
        
        stats = UsageStatistics(
            stat_id=stat_id,
            period_start=period_start,
            period_end=period_end,
            service_type=service_type,
            model_id=model_id,
            provider=provider,
            user_id=user_id,
            total_requests=total_requests,
            successful_requests=successful_requests,
            failed_requests=failed_requests,
            total_tokens=total_tokens,
            total_cost_usd=total_cost_usd,
            avg_response_time_ms=avg_response_time_ms,
            p95_response_time_ms=p95_response_time_ms,
            requests_per_hour=requests_per_hour,
            error_rate=error_rate
        )
        
        if self.storage_backend == "postgres":
            return self._record_stats_postgres(stats)
        elif self.storage_backend == "memory":
            return self._record_stats_memory(stats)
        else:
            return self._record_stats_file(stats)

    def get_usage_statistics(
        self,
        service_type: Optional[str] = None,
        model_id: Optional[str] = None,
        user_id: Optional[str] = None,
        days: int = 7,
        limit: int = 100
    ) -> List[UsageStatistics]:
        """Get usage statistics for specified period"""
        if self.storage_backend == "postgres":
            return self._get_stats_postgres(service_type, model_id, user_id, days, limit)
        elif self.storage_backend == "memory":
            return self._get_stats_memory(service_type, model_id, user_id, days, limit)
        else:
            return self._get_stats_file(service_type, model_id, user_id, days, limit)
    
    def get_aggregated_usage(
        self,
        service_type: Optional[str] = None,
        model_id: Optional[str] = None,
        user_id: Optional[str] = None,
        days: int = 30
    ) -> Dict[str, Any]:
        """Get aggregated usage statistics"""
        stats = self.get_usage_statistics(service_type, model_id, user_id, days, 1000)
        
        if not stats:
            return {
                "total_requests": 0,
                "total_cost_usd": 0.0,
                "total_tokens": 0,
                "avg_response_time_ms": 0.0,
                "success_rate": 100.0,
                "period_days": days
            }
        
        total_requests = sum(s.total_requests for s in stats)
        total_successful = sum(s.successful_requests for s in stats)
        total_cost = sum(s.total_cost_usd for s in stats)
        total_tokens = sum(s.total_tokens for s in stats)
        
        # Weighted average for response time
        weighted_response_times = [s.avg_response_time_ms * s.total_requests for s in stats if s.total_requests > 0]
        avg_response_time = sum(weighted_response_times) / total_requests if total_requests > 0 else 0.0
        
        success_rate = (total_successful / total_requests * 100) if total_requests > 0 else 100.0
        
        return {
            "total_requests": total_requests,
            "successful_requests": total_successful,
            "total_cost_usd": round(total_cost, 4),
            "total_tokens": total_tokens,
            "avg_response_time_ms": round(avg_response_time, 2),
            "success_rate": round(success_rate, 2),
            "period_days": days,
            "stats_count": len(stats)
        }
    
    # Model Usage Snapshots Methods
    
    def update_model_snapshot(
        self,
        model_id: str,
        provider: str,
        hourly_requests: int = 0,
        daily_requests: int = 0,
        weekly_requests: int = 0,
        monthly_requests: int = 0,
        total_tokens_today: int = 0,
        total_cost_today: float = 0.0,
        avg_response_time_today: float = 0.0,
        success_rate_today: float = 100.0
    ) -> str:
        """Update or create model usage snapshot"""
        snapshot_id = f"snap_{model_id}_{provider}_{datetime.now().strftime('%Y%m%d')}"
        
        snapshot = ModelUsageSnapshot(
            snapshot_id=snapshot_id,
            model_id=model_id,
            provider=provider,
            snapshot_time=datetime.now(timezone.utc),
            hourly_requests=hourly_requests,
            daily_requests=daily_requests,
            weekly_requests=weekly_requests,
            monthly_requests=monthly_requests,
            total_tokens_today=total_tokens_today,
            total_cost_today=total_cost_today,
            avg_response_time_today=avg_response_time_today,
            success_rate_today=success_rate_today,
            last_used=datetime.now(timezone.utc)
        )
        
        if self.storage_backend == "postgres":
            return self._update_snapshot_postgres(snapshot)
        elif self.storage_backend == "memory":
            return self._update_snapshot_memory(snapshot)
        else:
            return self._update_snapshot_file(snapshot)

    def get_model_snapshots(
        self,
        model_id: Optional[str] = None,
        provider: Optional[str] = None,
        days: int = 7
    ) -> List[ModelUsageSnapshot]:
        """Get model usage snapshots"""
        if self.storage_backend == "postgres":
            return self._get_snapshots_postgres(model_id, provider, days)
        elif self.storage_backend == "memory":
            return self._get_snapshots_memory(model_id, provider, days)
        else:
            return self._get_snapshots_file(model_id, provider, days)
    
    def get_top_models(self, metric: str = "daily_requests", limit: int = 10) -> List[Dict[str, Any]]:
        """Get top models by specified metric"""
        snapshots = self.get_model_snapshots(days=1)  # Get latest snapshots
        
        if not snapshots:
            return []
        
        # Sort by the specified metric
        valid_metrics = ["hourly_requests", "daily_requests", "weekly_requests", "monthly_requests", 
                        "total_tokens_today", "total_cost_today"]
        
        if metric not in valid_metrics:
            metric = "daily_requests"
        
        sorted_snapshots = sorted(
            snapshots, 
            key=lambda x: getattr(x, metric, 0), 
            reverse=True
        )[:limit]
        
        return [
            {
                "model_id": s.model_id,
                "provider": s.provider,
                "metric_value": getattr(s, metric, 0),
                "daily_requests": s.daily_requests,
                "total_cost_today": s.total_cost_today,
                "success_rate_today": s.success_rate_today,
                "last_used": s.last_used.isoformat() if s.last_used else None
            }
            for s in sorted_snapshots
        ]
    
    # Cleanup and Maintenance Methods
    
    def cleanup_old_requests(self, days: int = 30) -> int:
        """Clean up old inference requests"""
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=days)

        if self.storage_backend == "postgres":
            return self._cleanup_requests_postgres(cutoff_date)
        elif self.storage_backend == "memory":
            return self._cleanup_requests_memory(cutoff_date)
        else:
            return self._cleanup_requests_file(cutoff_date)

    def cleanup_old_statistics(self, days: int = 90) -> int:
        """Clean up old usage statistics"""
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=days)

        if self.storage_backend == "postgres":
            return self._cleanup_stats_postgres(cutoff_date)
        elif self.storage_backend == "memory":
            return self._cleanup_stats_memory(cutoff_date)
        else:
            return self._cleanup_stats_file(cutoff_date)

    def check_connection(self) -> bool:
        """Check database connection"""
        if self.storage_backend == "postgres":
            try:
                with self.db:
                    health = self.db.health_check()
                return health and health.get('healthy', False)
            except Exception as e:
                logger.error(f"PostgreSQL connection check failed: {e}")
                return False
        return True  # File/memory backends don't need connection check
    
    # Backend-specific implementations
    
    def _create_request_file(self, request: InferenceRequest) -> str:
        """Create request in file system"""
        try:
            request_file = self.data_dir / "requests" / f"{request.request_id}.json"
            request_data = asdict(request)
            
            # Convert datetime objects to ISO strings
            for key in ['created_at', 'started_at', 'completed_at']:
                if request_data[key] and isinstance(request_data[key], datetime):
                    request_data[key] = request_data[key].isoformat()
            
            with open(request_file, 'w') as f:
                json.dump(request_data, f, indent=2, ensure_ascii=False)
            
            return request.request_id
        except Exception as e:
            logger.error(f"Failed to create request in file system: {e}")
            raise
    
    def _create_request_memory(self, request: InferenceRequest) -> str:
        """Create request in memory"""
        self.requests[request.request_id] = request
        return request.request_id
    
    def _update_request_file(self, request_id: str, updates: Dict[str, Any]) -> bool:
        """Update request in file system"""
        try:
            request_file = self.data_dir / "requests" / f"{request_id}.json"
            if not request_file.exists():
                return False
            
            with open(request_file, 'r') as f:
                request_data = json.load(f)
            
            request_data.update(updates)
            
            with open(request_file, 'w') as f:
                json.dump(request_data, f, indent=2, ensure_ascii=False)
            
            return True
        except Exception as e:
            logger.error(f"Failed to update request in file system: {e}")
            return False
    
    def _update_request_memory(self, request_id: str, updates: Dict[str, Any]) -> bool:
        """Update request in memory"""
        if request_id not in self.requests:
            return False
        
        request_dict = asdict(self.requests[request_id])
        request_dict.update(updates)
        
        # Convert datetime strings back to datetime objects if needed
        for key in ['created_at', 'started_at', 'completed_at']:
            if key in request_dict and isinstance(request_dict[key], str):
                request_dict[key] = datetime.fromisoformat(request_dict[key])
        
        self.requests[request_id] = InferenceRequest(**request_dict)
        return True
    
    def _get_request_file(self, request_id: str) -> Optional[InferenceRequest]:
        """Get request from file system"""
        try:
            request_file = self.data_dir / "requests" / f"{request_id}.json"
            if not request_file.exists():
                return None
            
            with open(request_file, 'r') as f:
                request_data = json.load(f)
            
            # Convert ISO strings back to datetime objects
            for key in ['created_at', 'started_at', 'completed_at']:
                if request_data[key]:
                    request_data[key] = datetime.fromisoformat(request_data[key])
            
            return InferenceRequest(**request_data)
        except Exception as e:
            logger.error(f"Failed to get request from file system: {e}")
            return None
    
    def _get_request_memory(self, request_id: str) -> Optional[InferenceRequest]:
        """Get request from memory"""
        return self.requests.get(request_id)
    
    def _list_requests_file(
        self, service_type: Optional[str], model_id: Optional[str], 
        user_id: Optional[str], status: Optional[str], hours: int, limit: int
    ) -> List[InferenceRequest]:
        """List requests from file system"""
        try:
            requests = []
            requests_dir = self.data_dir / "requests"
            cutoff_time = datetime.now(timezone.utc) - timedelta(hours=hours)
            
            for request_file in requests_dir.glob("*.json"):
                with open(request_file, 'r') as f:
                    request_data = json.load(f)
                
                # Convert datetime fields
                for key in ['created_at', 'started_at', 'completed_at']:
                    if request_data[key]:
                        request_data[key] = datetime.fromisoformat(request_data[key])
                
                request = InferenceRequest(**request_data)
                
                # Apply filters
                if request.created_at < cutoff_time:
                    continue
                if service_type and request.service_type != service_type:
                    continue
                if model_id and request.model_id != model_id:
                    continue
                if user_id and request.user_id != user_id:
                    continue
                if status and request.status != status:
                    continue
                
                requests.append(request)
                
                if len(requests) >= limit:
                    break
            
            return sorted(requests, key=lambda x: x.created_at, reverse=True)
        except Exception as e:
            logger.error(f"Failed to list requests from file system: {e}")
            return []
    
    def _list_requests_memory(
        self, service_type: Optional[str], model_id: Optional[str], 
        user_id: Optional[str], status: Optional[str], hours: int, limit: int
    ) -> List[InferenceRequest]:
        """List requests from memory"""
        cutoff_time = datetime.now(timezone.utc) - timedelta(hours=hours)
        requests = []
        
        for request in self.requests.values():
            # Apply filters
            if request.created_at < cutoff_time:
                continue
            if service_type and request.service_type != service_type:
                continue
            if model_id and request.model_id != model_id:
                continue
            if user_id and request.user_id != user_id:
                continue
            if status and request.status != status:
                continue
            
            requests.append(request)
            
            if len(requests) >= limit:
                break
        
        return sorted(requests, key=lambda x: x.created_at, reverse=True)
    
    # Simplified placeholder implementations for statistics and snapshots
    def _record_stats_file(self, stats: UsageStatistics) -> str:
        """Record statistics in file system"""
        try:
            stats_file = self.data_dir / "statistics" / f"{stats.stat_id}.json"
            stats_data = asdict(stats)
            
            # Convert datetime objects to ISO strings
            for key in ['period_start', 'period_end', 'created_at']:
                if stats_data[key] and isinstance(stats_data[key], datetime):
                    stats_data[key] = stats_data[key].isoformat()
            
            with open(stats_file, 'w') as f:
                json.dump(stats_data, f, indent=2, ensure_ascii=False)
            
            return stats.stat_id
        except Exception as e:
            logger.error(f"Failed to record statistics in file system: {e}")
            raise
    
    def _record_stats_memory(self, stats: UsageStatistics) -> str:
        """Record statistics in memory"""
        self.statistics[stats.stat_id] = stats
        return stats.stat_id
    
    def _update_snapshot_file(self, snapshot: ModelUsageSnapshot) -> str:
        """Update snapshot in file system"""
        try:
            snapshot_file = self.data_dir / "snapshots" / f"{snapshot.snapshot_id}.json"
            snapshot_data = asdict(snapshot)
            
            # Convert datetime objects to ISO strings
            for key in ['snapshot_time', 'last_used']:
                if snapshot_data[key] and isinstance(snapshot_data[key], datetime):
                    snapshot_data[key] = snapshot_data[key].isoformat()
            
            with open(snapshot_file, 'w') as f:
                json.dump(snapshot_data, f, indent=2, ensure_ascii=False)
            
            return snapshot.snapshot_id
        except Exception as e:
            logger.error(f"Failed to update snapshot in file system: {e}")
            raise
    
    def _update_snapshot_memory(self, snapshot: ModelUsageSnapshot) -> str:
        """Update snapshot in memory"""
        self.snapshots[snapshot.snapshot_id] = snapshot
        return snapshot.snapshot_id
    
    # Cleanup implementations
    def _cleanup_requests_file(self, cutoff_date: datetime) -> int:
        """Cleanup old requests from file system"""
        count = 0
        try:
            requests_dir = self.data_dir / "requests"
            for request_file in requests_dir.glob("*.json"):
                if request_file.stat().st_mtime < cutoff_date.timestamp():
                    request_file.unlink()
                    count += 1
        except Exception as e:
            logger.error(f"Failed to cleanup requests from file system: {e}")
        return count
    
    def _cleanup_requests_memory(self, cutoff_date: datetime) -> int:
        """Cleanup old requests from memory"""
        count = 0
        to_remove = []
        for request_id, request in self.requests.items():
            if request.created_at < cutoff_date:
                to_remove.append(request_id)
        
        for request_id in to_remove:
            del self.requests[request_id]
            count += 1
        
        return count
    
    # PostgreSQL backend implementations
    def _create_request_postgres(
        self, request_id: str, service_type: str, model_id: str, provider: str,
        endpoint: str, request_data: Dict[str, Any], user_id: Optional[str],
        session_id: Optional[str], client_id: Optional[str], ip_address: Optional[str],
        user_agent: Optional[str], metadata: Optional[Dict[str, Any]]
    ) -> str:
        """Create inference request in PostgreSQL"""
        try:
            # Generate request hash for deduplication
            import hashlib
            request_hash = hashlib.sha256(
                json.dumps(request_data, sort_keys=True).encode()
            ).hexdigest()[:16]

            # Prepare data - let database handle created_at, updated_at
            data = {
                "request_id": request_id,
                "service_type": service_type,
                "model_id": model_id,
                "provider": provider,
                "endpoint": endpoint,
                "request_data": request_data,  # JSONB field
                "user_id": user_id,
                "session_id": session_id,
                "client_id": client_id,
                "ip_address": ip_address,
                "user_agent": user_agent,
                "request_hash": request_hash,
                "status": InferenceStatus.PENDING,
                "metadata": metadata or {}  # JSONB field
            }

            # Insert into database
            with self.db:
                count = self.db.insert_into(self.requests_table, [data], schema=self.schema)

            if count is not None and count > 0:
                logger.debug(f"Created inference request: {request_id}")
                return request_id
            else:
                raise Exception("Failed to insert inference request")

        except Exception as e:
            logger.error(f"Failed to create inference request in PostgreSQL: {e}")
            raise

    def _update_request_postgres(self, request_id: str, updates: Dict[str, Any]) -> bool:
        """Update inference request in PostgreSQL"""
        try:
            # Build UPDATE query with parameterized values
            set_clause = ", ".join([f"{k} = ${i+1}" for i, k in enumerate(updates.keys())])
            params = list(updates.values()) + [request_id]

            query = f"""
                UPDATE {self.schema}.{self.requests_table}
                SET {set_clause}
                WHERE request_id = ${len(params)}
            """

            with self.db:
                result = self.db.execute(query, params, schema=self.schema)

            return result is not None and result > 0

        except Exception as e:
            logger.error(f"Failed to update inference request in PostgreSQL: {e}")
            return False

    def _get_request_postgres(self, request_id: str) -> Optional[InferenceRequest]:
        """Get inference request from PostgreSQL"""
        try:
            with self.db:
                result = self.db.query_row(
                    f"SELECT * FROM {self.schema}.{self.requests_table} WHERE request_id = $1",
                    [request_id],
                    schema=self.schema
                )

            # Convert row dict to InferenceRequest if found
            if result:
                # PostgreSQL returns dict directly, no need for proto conversion for JSONB
                return InferenceRequest(**result)
            return None

        except Exception as e:
            logger.error(f"Failed to get inference request from PostgreSQL: {e}")
            return None

    def _list_requests_postgres(
        self, service_type: Optional[str], model_id: Optional[str],
        user_id: Optional[str], status: Optional[str], hours: int, limit: int
    ) -> List[InferenceRequest]:
        """List inference requests from PostgreSQL"""
        try:
            cutoff_time = datetime.now(timezone.utc) - timedelta(hours=hours)

            # Build query with filters
            conditions = [f"created_at > $1"]
            params = [cutoff_time]
            param_idx = 2

            if service_type:
                conditions.append(f"service_type = ${param_idx}")
                params.append(service_type)
                param_idx += 1

            if model_id:
                conditions.append(f"model_id = ${param_idx}")
                params.append(model_id)
                param_idx += 1

            if user_id:
                conditions.append(f"user_id = ${param_idx}")
                params.append(user_id)
                param_idx += 1

            if status:
                conditions.append(f"status = ${param_idx}")
                params.append(status)
                param_idx += 1

            where_clause = " AND ".join(conditions)
            query = f"""
                SELECT * FROM {self.schema}.{self.requests_table}
                WHERE {where_clause}
                ORDER BY created_at DESC
                LIMIT {limit}
            """

            with self.db:
                results = self.db.query(query, params, schema=self.schema)

            # Convert to InferenceRequest objects
            return [InferenceRequest(**row) for row in (results or [])]

        except Exception as e:
            logger.error(f"Failed to list inference requests from PostgreSQL: {e}")
            return []

    def _record_stats_postgres(self, stats: UsageStatistics) -> str:
        """Record usage statistics in PostgreSQL"""
        try:
            stats_dict = asdict(stats)

            # Convert datetime to ISO strings for any datetime fields
            for key in ['period_start', 'period_end', 'created_at']:
                if key in stats_dict and isinstance(stats_dict[key], datetime):
                    stats_dict[key] = stats_dict[key].isoformat()

            # Convert float to Decimal for precision
            for key in ['total_cost_usd', 'avg_response_time_ms', 'p50_response_time_ms',
                       'p95_response_time_ms', 'p99_response_time_ms', 'error_rate',
                       'timeout_rate', 'cache_hit_rate', 'cost_per_token', 'cost_per_request']:
                if key in stats_dict and stats_dict[key] is not None:
                    stats_dict[key] = Decimal(str(stats_dict[key]))

            # Remove created_at to let database handle it
            stats_dict.pop('created_at', None)

            with self.db:
                count = self.db.insert_into(self.statistics_table, [stats_dict], schema=self.schema)

            if count is not None and count > 0:
                logger.debug(f"Recorded usage statistics: {stats.stat_id}")
                return stats.stat_id
            else:
                raise Exception("Failed to insert usage statistics")

        except Exception as e:
            logger.error(f"Failed to record usage statistics in PostgreSQL: {e}")
            raise

    def _get_stats_postgres(
        self, service_type: Optional[str], model_id: Optional[str],
        user_id: Optional[str], days: int, limit: int
    ) -> List[UsageStatistics]:
        """Get usage statistics from PostgreSQL"""
        try:
            cutoff_date = datetime.now(timezone.utc) - timedelta(days=days)

            conditions = [f"period_end > $1"]
            params = [cutoff_date]
            param_idx = 2

            if service_type:
                conditions.append(f"service_type = ${param_idx}")
                params.append(service_type)
                param_idx += 1

            if model_id:
                conditions.append(f"model_id = ${param_idx}")
                params.append(model_id)
                param_idx += 1

            if user_id:
                conditions.append(f"user_id = ${param_idx}")
                params.append(user_id)
                param_idx += 1

            where_clause = " AND ".join(conditions)
            query = f"""
                SELECT * FROM {self.schema}.{self.statistics_table}
                WHERE {where_clause}
                ORDER BY period_end DESC
                LIMIT {limit}
            """

            with self.db:
                results = self.db.query(query, params, schema=self.schema)

            # Convert to UsageStatistics objects
            return [UsageStatistics(**row) for row in (results or [])]

        except Exception as e:
            logger.error(f"Failed to get usage statistics from PostgreSQL: {e}")
            return []
    
    def _get_stats_memory(self, service_type, model_id, user_id, days, limit) -> List[UsageStatistics]:
        return list(self.statistics.values())[:limit]
    
    def _get_stats_file(self, service_type, model_id, user_id, days, limit) -> List[UsageStatistics]:
        return []  # Implementation needed
    def _update_snapshot_postgres(self, snapshot: ModelUsageSnapshot) -> str:
        """Update or create model snapshot in PostgreSQL"""
        try:
            snapshot_dict = asdict(snapshot)

            # Convert datetime fields
            for key in ['snapshot_time', 'last_used']:
                if key in snapshot_dict and isinstance(snapshot_dict[key], datetime):
                    snapshot_dict[key] = snapshot_dict[key].isoformat()

            # Convert float to Decimal for cost/performance fields
            for key in ['total_cost_hour', 'total_cost_day', 'total_cost_week', 'total_cost_month',
                       'avg_response_time_hour', 'avg_response_time_day',
                       'success_rate_hour', 'success_rate_day',
                       'cache_hit_rate_hour', 'cache_hit_rate_day']:
                if key in snapshot_dict and snapshot_dict[key] is not None:
                    snapshot_dict[key] = Decimal(str(snapshot_dict[key]))

            with self.db:
                # Try to check if exists
                existing = self.db.query_row(
                    f"SELECT id FROM {self.schema}.{self.snapshots_table} WHERE snapshot_id = $1",
                    [snapshot.snapshot_id],
                    schema=self.schema
                )

                if existing:
                    # Update existing snapshot
                    update_fields = [k for k in snapshot_dict.keys() if k != 'snapshot_id']
                    set_clause = ", ".join([f"{k} = ${i+1}" for i, k in enumerate(update_fields)])
                    params = [snapshot_dict[k] for k in update_fields] + [snapshot.snapshot_id]

                    update_query = f"""
                        UPDATE {self.schema}.{self.snapshots_table}
                        SET {set_clause}
                        WHERE snapshot_id = ${len(params)}
                    """
                    self.db.execute(update_query, params, schema=self.schema)
                else:
                    # Insert new snapshot
                    self.db.insert_into(self.snapshots_table, [snapshot_dict], schema=self.schema)

            logger.debug(f"Updated model snapshot: {snapshot.snapshot_id}")
            return snapshot.snapshot_id

        except Exception as e:
            logger.error(f"Failed to update model snapshot in PostgreSQL: {e}")
            raise

    def _get_snapshots_postgres(
        self, model_id: Optional[str], provider: Optional[str], days: int
    ) -> List[ModelUsageSnapshot]:
        """Get model snapshots from PostgreSQL"""
        try:
            cutoff_date = datetime.now(timezone.utc) - timedelta(days=days)

            conditions = [f"snapshot_time > $1"]
            params = [cutoff_date]
            param_idx = 2

            if model_id:
                conditions.append(f"model_id = ${param_idx}")
                params.append(model_id)
                param_idx += 1

            if provider:
                conditions.append(f"provider = ${param_idx}")
                params.append(provider)
                param_idx += 1

            where_clause = " AND ".join(conditions)
            query = f"""
                SELECT * FROM {self.schema}.{self.snapshots_table}
                WHERE {where_clause}
                ORDER BY snapshot_time DESC
            """

            with self.db:
                results = self.db.query(query, params, schema=self.schema)

            # Convert to ModelUsageSnapshot objects
            return [ModelUsageSnapshot(**row) for row in (results or [])]

        except Exception as e:
            logger.error(f"Failed to get model snapshots from PostgreSQL: {e}")
            return []

    def _get_snapshots_memory(self, model_id, provider, days) -> List[ModelUsageSnapshot]:
        return list(self.snapshots.values())

    def _get_snapshots_file(self, model_id, provider, days) -> List[ModelUsageSnapshot]:
        return []  # Implementation needed

    def _cleanup_requests_postgres(self, cutoff_date: datetime) -> int:
        """Clean up old requests from PostgreSQL"""
        try:
            query = f"""
                DELETE FROM {self.schema}.{self.requests_table}
                WHERE created_at < $1
            """

            with self.db:
                count = self.db.execute(query, [cutoff_date], schema=self.schema)

            logger.info(f"Cleaned up {count} old inference requests from PostgreSQL")
            return count if count is not None else 0

        except Exception as e:
            logger.error(f"Failed to cleanup old requests from PostgreSQL: {e}")
            return 0

    def _cleanup_stats_postgres(self, cutoff_date: datetime) -> int:
        """Clean up old statistics from PostgreSQL"""
        try:
            query = f"""
                DELETE FROM {self.schema}.{self.statistics_table}
                WHERE period_end < $1
            """

            with self.db:
                count = self.db.execute(query, [cutoff_date], schema=self.schema)

            logger.info(f"Cleaned up {count} old usage statistics from PostgreSQL")
            return count if count is not None else 0

        except Exception as e:
            logger.error(f"Failed to cleanup old statistics from PostgreSQL: {e}")
            return 0
    
    def _cleanup_stats_memory(self, cutoff_date: datetime) -> int:
        count = 0
        to_remove = []
        for stat_id, stat in self.statistics.items():
            if stat.created_at < cutoff_date:
                to_remove.append(stat_id)
        
        for stat_id in to_remove:
            del self.statistics[stat_id]
            count += 1
        
        return count
    
    def _cleanup_stats_file(self, cutoff_date: datetime) -> int:
        count = 0
        try:
            stats_dir = self.data_dir / "statistics"
            for stats_file in stats_dir.glob("*.json"):
                if stats_file.stat().st_mtime < cutoff_date.timestamp():
                    stats_file.unlink()
                    count += 1
        except Exception as e:
            logger.error(f"Failed to cleanup statistics from file system: {e}")
        return count