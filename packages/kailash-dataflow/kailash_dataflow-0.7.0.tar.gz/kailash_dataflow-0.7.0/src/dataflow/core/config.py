"""
DataFlow Configuration System

Provides zero-configuration defaults with progressive disclosure for advanced users.
Automatically detects environment and configures optimal settings.
"""

import multiprocessing
import os
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

from .models import Environment


@dataclass
class DatabaseConfig:
    """Database configuration with intelligent defaults"""

    # Core connection settings
    database_url: Optional[str] = None
    url: Optional[str] = None  # Alias for database_url
    driver: Optional[str] = None
    host: Optional[str] = None
    port: Optional[int] = None
    database: Optional[str] = None
    username: Optional[str] = None
    password: Optional[str] = None

    # Connection pool settings
    pool_size: Optional[int] = None
    pool_max_overflow: Optional[int] = None
    max_overflow: Optional[int] = None  # Alias for pool_max_overflow
    pool_timeout: Optional[float] = None
    pool_recycle: Optional[int] = None
    pool_pre_ping: bool = True

    # Monitoring and performance
    monitoring: bool = True
    cache_enabled: bool = True

    # Advanced settings
    echo: bool = False
    echo_pool: bool = False
    connect_args: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        """Post-initialization to handle aliases."""
        # Handle database_url alias
        if self.database_url and not self.url:
            self.url = self.database_url
        elif self.url and not self.database_url:
            self.database_url = self.url

        # Handle pool_max_overflow alias
        if self.pool_max_overflow and not self.max_overflow:
            self.max_overflow = self.pool_max_overflow
        elif self.max_overflow and not self.pool_max_overflow:
            self.pool_max_overflow = self.max_overflow

    def get_connection_url(self, environment: Environment) -> str:
        """Generate connection URL based on configuration and environment"""
        # Check for explicit URL first
        if self.url:
            # Handle :memory: shorthand for SQLite in-memory
            if self.url == ":memory:":
                return "sqlite:///:memory:"
            return self.url

        # Check environment variables
        env_url = os.getenv("DATABASE_URL")
        if env_url:
            return env_url

        # Build URL from components
        if all([self.driver, self.host, self.database]):
            auth = ""
            if self.username:
                auth = self.username
                if self.password:
                    auth += f":{self.password}"
                auth += "@"

            port = f":{self.port}" if self.port else ""
            return f"{self.driver}://{auth}{self.host}{port}/{self.database}"

        # Default based on environment
        if environment == Environment.DEVELOPMENT:
            # Use in-memory SQLite for instant development
            return "sqlite:///:memory:"
        elif environment == Environment.TESTING:
            # Use file-based SQLite for testing
            test_db = Path("test_database.db")
            return f"sqlite:///{test_db.absolute()}"
        else:
            # Production environments should have explicit configuration
            # But for zero-config mode, default to SQLite
            return "sqlite:///dataflow.db"

    def get_pool_size(self, environment: Environment) -> int:
        """Calculate optimal pool size based on environment and resources"""
        if self.pool_size is not None:
            return self.pool_size

        # Calculate based on CPU cores and environment
        cpu_count = multiprocessing.cpu_count()

        if environment == Environment.DEVELOPMENT:
            return min(5, cpu_count)
        elif environment == Environment.TESTING:
            return min(10, cpu_count * 2)
        elif environment == Environment.STAGING:
            return min(20, cpu_count * 3)
        else:  # Production
            return min(50, cpu_count * 4)

    def get_max_overflow(self, environment: Environment) -> int:
        """Calculate max overflow based on pool size"""
        if self.max_overflow is not None:
            return self.max_overflow

        pool_size = self.get_pool_size(environment)
        return pool_size * 2  # Allow 2x overflow


@dataclass
class MonitoringConfig:
    """Monitoring configuration with production defaults"""

    enabled: Optional[bool] = None
    slow_query_threshold: float = 1.0  # seconds
    query_insights: bool = True
    connection_metrics: bool = True
    transaction_tracking: bool = True

    # Alerting
    alert_on_connection_exhaustion: bool = True
    alert_on_slow_queries: bool = True
    alert_on_failed_transactions: bool = True

    # Export settings
    metrics_export_interval: int = 60  # seconds
    metrics_export_format: str = "prometheus"  # prometheus, json, statsd

    def is_enabled(self, environment: Environment) -> bool:
        """Determine if monitoring should be enabled"""
        if self.enabled is not None:
            return self.enabled

        # Enable for staging and production by default
        return environment in [Environment.STAGING, Environment.PRODUCTION]

    def get_enabled_for_environment(self, environment: Environment) -> bool:
        """Get the effective enabled state for the given environment"""
        return self.is_enabled(environment)


@dataclass
class SecurityConfig:
    """Security configuration with enterprise defaults"""

    # Access control
    access_control_enabled: bool = True
    access_control_strategy: str = "rbac"  # rbac, abac, hybrid

    # Encryption
    encrypt_at_rest: bool = True
    encrypt_in_transit: bool = True

    # Query security
    sql_injection_protection: bool = True
    query_parameter_validation: bool = True

    # Multi-tenancy
    multi_tenant: bool = False
    tenant_isolation_strategy: str = "schema"  # schema, row, database

    # Audit
    audit_enabled: bool = True
    audit_log_retention_days: int = 90

    # Compliance
    gdpr_mode: bool = False
    pii_detection: bool = True
    data_masking: bool = True


# Enhanced DataFlowConfig with backward compatibility and direct attribute access
class DataFlowConfig:
    """Main configuration object with intelligent defaults"""

    def __init__(self, **kwargs):
        """Initialize configuration with flexible parameter handling"""
        # Default values
        self.environment = kwargs.get("environment", Environment.DEVELOPMENT)
        self.debug = kwargs.get("debug", False)
        self.auto_commit = kwargs.get("auto_commit", True)
        self.batch_size = kwargs.get("batch_size", 1000)
        self.connection_pool_size = kwargs.get("connection_pool_size", 10)

        # Schema state management settings
        self.schema_cache_ttl = kwargs.get("schema_cache_ttl", 300)  # 5 minutes default
        self.schema_cache_max_size = kwargs.get(
            "schema_cache_max_size", 100
        )  # 100 schemas default

        # Handle database configuration
        if "database" in kwargs and isinstance(kwargs["database"], DatabaseConfig):
            self.database = kwargs["database"]
        else:
            db_config_kwargs = {}
            if "database_url" in kwargs:
                db_config_kwargs["url"] = kwargs["database_url"]
            if "pool_size" in kwargs:
                db_config_kwargs["pool_size"] = kwargs["pool_size"]
                # Validate pool_size
                if kwargs["pool_size"] < 1:
                    raise ValueError("pool_size must be at least 1")
            if "pool_max_overflow" in kwargs:
                db_config_kwargs["max_overflow"] = kwargs["pool_max_overflow"]
            if "pool_recycle" in kwargs:
                db_config_kwargs["pool_recycle"] = kwargs["pool_recycle"]
            if "echo" in kwargs:
                db_config_kwargs["echo"] = kwargs["echo"]
            self.database = DatabaseConfig(**db_config_kwargs)

        # Handle monitoring configuration
        if "monitoring" in kwargs and isinstance(
            kwargs["monitoring"], MonitoringConfig
        ):
            self._monitoring_config = kwargs["monitoring"]
            self._monitoring_bool = kwargs["monitoring"].enabled
        else:
            mon_config_kwargs = {}
            if "monitoring" in kwargs and isinstance(kwargs["monitoring"], bool):
                mon_config_kwargs["enabled"] = kwargs["monitoring"]
                self._monitoring_bool = kwargs["monitoring"]
            if "slow_query_threshold" in kwargs:
                mon_config_kwargs["slow_query_threshold"] = kwargs[
                    "slow_query_threshold"
                ]
            self._monitoring_config = MonitoringConfig(**mon_config_kwargs)
            if not hasattr(self, "_monitoring_bool"):
                self._monitoring_bool = self._monitoring_config.enabled

        # Handle security configuration
        if "security" in kwargs and isinstance(kwargs["security"], SecurityConfig):
            self.security = kwargs["security"]
        else:
            sec_config_kwargs = {}
            if "multi_tenant" in kwargs:
                sec_config_kwargs["multi_tenant"] = kwargs["multi_tenant"]
            if "encryption_key" in kwargs:
                self._encryption_key = kwargs["encryption_key"]
                sec_config_kwargs["encrypt_at_rest"] = (
                    kwargs["encryption_key"] is not None
                )
            if "audit_logging" in kwargs:
                sec_config_kwargs["audit_enabled"] = kwargs["audit_logging"]
            self.security = SecurityConfig(**sec_config_kwargs)

        # Node generation settings
        self.auto_generate_nodes = kwargs.get("auto_generate_nodes", True)
        self.node_prefix = kwargs.get("node_prefix", "")
        self.node_suffix = kwargs.get("node_suffix", "Node")

        # Migration settings
        self.auto_migrate = kwargs.get("auto_migrate", True)
        self.migration_directory = Path(kwargs.get("migration_directory", "migrations"))

        # Cache settings
        self.enable_query_cache = kwargs.get(
            "cache_enabled", kwargs.get("enable_query_cache", True)
        )
        self.cache_ttl = kwargs.get("cache_ttl", 300)

        # Validate cache_ttl
        if self.cache_ttl < 0:
            raise ValueError("cache_ttl cannot be negative")
        self.redis_host = kwargs.get("redis_host", "localhost")
        self.redis_port = kwargs.get("redis_port", 6379)
        self.redis_db = kwargs.get("redis_db", 0)
        self.redis_password = kwargs.get("redis_password", None)
        self.cache_invalidation_strategy = kwargs.get(
            "cache_invalidation_strategy", "pattern_based"
        )
        self.cache_key_prefix = kwargs.get("cache_key_prefix", "dataflow:query")

        # Development settings
        self.hot_reload = kwargs.get("hot_reload", True)

        # Advanced settings
        self.custom_node_templates = kwargs.get("custom_node_templates", None)
        self.plugin_directory = kwargs.get("plugin_directory", None)

        # Private tenant context storage
        self._tenant_context = kwargs.get("_tenant_context", {})

        # Additional compatibility properties
        self._cache_max_size = kwargs.get("cache_max_size", 1000)
        self._max_retries = kwargs.get("max_retries", 3)
        self._encryption_enabled = kwargs.get("encryption_enabled", False)

        # Post-initialization
        self._post_init()

    def _post_init(self):
        """Post-initialization configuration"""
        # Auto-detect environment if not set
        if self.environment is None:
            self.environment = Environment.detect()

        # Set debug based on environment
        if self.debug is None:
            self.debug = self.environment == Environment.DEVELOPMENT

        # Set monitoring defaults based on environment
        if self._monitoring_config.enabled is None:
            self._monitoring_config.enabled = self._monitoring_config.is_enabled(
                self.environment
            )
            self._monitoring_bool = self._monitoring_config.enabled

    @property
    def multi_tenant(self):
        """Direct access to multi_tenant property for compatibility"""
        return self.security.multi_tenant

    @multi_tenant.setter
    def multi_tenant(self, value: bool):
        """Direct setter for multi_tenant property"""
        self.security.multi_tenant = value

    @property
    def database_url(self):
        """Direct access to database URL"""
        # Return the actual URL first, but if None, calculate it based on environment
        if self.database.url:
            return self.database.url
        return self.database.get_connection_url(self.environment)

    @database_url.setter
    def database_url(self, value: str):
        """Direct setter for database URL"""
        self.database.url = value
        self.database.database_url = value

    @property
    def pool_size(self):
        """Direct access to pool size"""
        return self.database.pool_size

    @pool_size.setter
    def pool_size(self, value: int):
        """Direct setter for pool size"""
        self.database.pool_size = value

    @property
    def pool_max_overflow(self):
        """Direct access to pool max overflow"""
        return self.database.max_overflow

    @pool_max_overflow.setter
    def pool_max_overflow(self, value: int):
        """Direct setter for pool max overflow"""
        self.database.max_overflow = value
        self.database.pool_max_overflow = value

    @property
    def pool_recycle(self):
        """Direct access to pool recycle"""
        return self.database.pool_recycle

    @pool_recycle.setter
    def pool_recycle(self, value: int):
        """Direct setter for pool recycle"""
        self.database.pool_recycle = value

    @property
    def slow_query_threshold(self):
        """Direct access to slow query threshold"""
        return self._monitoring_config.slow_query_threshold

    @slow_query_threshold.setter
    def slow_query_threshold(self, value: float):
        """Direct setter for slow query threshold"""
        self._monitoring_config.slow_query_threshold = value

    @property
    def echo(self):
        """Direct access to echo setting"""
        return self.database.echo

    @echo.setter
    def echo(self, value: bool):
        """Direct setter for echo"""
        self.database.echo = value

    @property
    def monitoring_enabled(self):
        """Direct access to monitoring enabled state"""
        return self._monitoring_config.enabled

    @property
    def encryption_key(self):
        """For compatibility - returns the actual key if set"""
        return (
            self._encryption_key
            if hasattr(self, "_encryption_key")
            else ("configured" if self.security.encrypt_at_rest else None)
        )

    @property
    def audit_logging(self):
        """Direct access to audit logging enabled state"""
        return self.security.audit_enabled

    @audit_logging.setter
    def audit_logging(self, value: bool):
        """Direct setter for audit logging"""
        self.security.audit_enabled = value

    @property
    def cache_enabled(self):
        """Direct access to cache enabled state"""
        return self.enable_query_cache

    @cache_enabled.setter
    def cache_enabled(self, value: bool):
        """Direct setter for cache enabled"""
        self.enable_query_cache = value

    def get_tenant_context(self):
        """Get the current tenant context"""
        return self._tenant_context

    def to_dict(self):
        """Convert configuration to dictionary for serialization"""
        return {
            "environment": (
                self.environment.value.lower()
                if hasattr(self.environment, "value")
                else str(self.environment).lower()
            ),
            "database": asdict(self.database),
            "monitoring": asdict(self.monitoring),
            "security": asdict(self.security),
            "debug": self.debug,
            "auto_commit": self.auto_commit,
            "batch_size": self.batch_size,
            "connection_pool_size": self.connection_pool_size,
            "schema_cache_ttl": self.schema_cache_ttl,
            "schema_cache_max_size": self.schema_cache_max_size,
        }

    @property
    def monitoring(self):
        """Direct access to monitoring - returns MonitoringConfig object for structured access"""
        return (
            self._monitoring_config
            if hasattr(self, "_monitoring_config")
            else MonitoringConfig()
        )

    @monitoring.setter
    def monitoring(self, value):
        """Direct setter for monitoring"""
        if isinstance(value, bool):
            self._monitoring_bool = value
            self._monitoring_config.enabled = value
        elif hasattr(value, "enabled"):
            # If value is a config object with enabled property
            self._monitoring_bool = value.enabled
            self._monitoring_config = value
        else:
            # Default to False for any other value
            self._monitoring_bool = False
            self._monitoring_config.enabled = False

    @property
    def cache_max_size(self):
        """Cache max size property for compatibility"""
        return getattr(self, "_cache_max_size", 1000)

    @cache_max_size.setter
    def cache_max_size(self, value: int):
        """Set cache max size"""
        self._cache_max_size = value

    @property
    def max_retries(self):
        """Max retries property for compatibility"""
        return getattr(self, "_max_retries", 3)

    @max_retries.setter
    def max_retries(self, value: int):
        """Set max retries"""
        self._max_retries = value

    @property
    def encryption_enabled(self):
        """Encryption enabled property for compatibility"""
        return getattr(self, "_encryption_enabled", False)

    @encryption_enabled.setter
    def encryption_enabled(self, value: bool):
        """Set encryption enabled"""
        self._encryption_enabled = value

    @classmethod
    def from_env(cls) -> "DataFlowConfig":
        """Create configuration from environment variables"""
        config = cls()

        # Database configuration from env
        if db_url := os.getenv("DATABASE_URL"):
            config.database.url = db_url
            config.database.database_url = db_url
        else:
            # Default to SQLite for zero-config mode
            default_url = "sqlite:///dataflow.db"
            config.database.url = default_url
            config.database.database_url = default_url

        # Pool settings from env
        if pool_size := os.getenv("DATAFLOW_POOL_SIZE", os.getenv("DB_POOL_SIZE")):
            config.database.pool_size = int(pool_size)

        if max_overflow := os.getenv(
            "DATAFLOW_MAX_OVERFLOW", os.getenv("DB_MAX_OVERFLOW")
        ):
            config.database.max_overflow = int(max_overflow)

        # Monitoring from env
        if monitoring := os.getenv(
            "DATAFLOW_ENABLE_MONITORING", os.getenv("DATAFLOW_MONITORING")
        ):
            config._monitoring_config.enabled = monitoring.lower() == "true"
            config._monitoring_bool = config._monitoring_config.enabled

        # Security from env
        if multi_tenant := os.getenv(
            "DATAFLOW_ENABLE_MULTI_TENANT", os.getenv("DATAFLOW_MULTI_TENANT")
        ):
            config.security.multi_tenant = multi_tenant.lower() == "true"

        # Cache settings from env
        if cache_enabled := os.getenv("DATAFLOW_QUERY_CACHE"):
            config.enable_query_cache = cache_enabled.lower() == "true"

        if redis_host := os.getenv("REDIS_HOST"):
            config.redis_host = redis_host

        if redis_port := os.getenv("REDIS_PORT"):
            config.redis_port = int(redis_port)

        if cache_strategy := os.getenv("DATAFLOW_CACHE_STRATEGY"):
            config.cache_invalidation_strategy = cache_strategy

        if cache_ttl := os.getenv("DATAFLOW_CACHE_TTL"):
            config.cache_ttl = int(cache_ttl)

        return config

    def validate(self) -> List[str]:
        """Validate configuration and return any issues"""
        issues = []

        # Production requires explicit database configuration
        if self.environment == Environment.PRODUCTION:
            if not self.database.url and not os.getenv("DATABASE_URL"):
                issues.append(
                    "Production requires explicit database configuration. "
                    "Set DATABASE_URL or provide database configuration."
                )

            # Check for SQLite in production
            db_url = self.database.get_connection_url(self.environment)
            if db_url and "sqlite" in db_url.lower():
                issues.append(
                    "SQLite database is not recommended for production environments"
                )

        # Validation for pool settings
        if self.database.pool_size is not None:
            if self.database.pool_size < 1:
                issues.append("pool_size must be at least 1")
            if self.database.pool_size > 1000:
                issues.append("pool_size should not exceed 1000")

        if self.database.max_overflow is not None:
            if self.database.max_overflow < 0:
                issues.append("max_overflow cannot be negative")

        # Cache TTL validation
        if self.cache_ttl < 0:
            issues.append("cache_ttl cannot be negative")

        # Redis port validation
        if not 1 <= self.redis_port <= 65535:
            issues.append("redis_port must be between 1 and 65535")

        return issues

    def __eq__(self, other):
        """Compare DataFlowConfig instances for equality."""
        if not isinstance(other, DataFlowConfig):
            return False

        # Compare core configuration values
        return (
            self.environment == other.environment
            and self.debug == other.debug
            and self.auto_commit == other.auto_commit
            and self.batch_size == other.batch_size
            and self.database_url == other.database_url
            and self.pool_size == other.pool_size
            and self.multi_tenant == other.multi_tenant
            and self.monitoring == other.monitoring
            and self.cache_enabled == other.cache_enabled
        )
