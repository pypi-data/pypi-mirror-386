# Limits Architecture

This document describes the architecture of Concurry's Limit system, which provides flexible resource protection, rate limiting, and multi-region/multi-account support.

## Table of Contents

1. [Overview](#overview)
2. [Three-Layer Architecture](#three-layer-architecture)
3. [Layer 1: Limit Definitions](#layer-1-limit-definitions-data-containers)
4. [Layer 2: LimitSet](#layer-2-limitset-thread-safe-executor)
5. [Layer 3: LimitPool](#layer-3-limitpool-load-balanced-multi-limitset-wrapper)
6. [Worker Integration](#worker-integration)
7. [Thread-Safety Model](#thread-safety-model)
8. [Acquisition Flow](#acquisition-flow)
9. [Shared State Management](#shared-state-management)
10. [Serialization and Remote Execution](#serialization-and-remote-execution)
11. [Extension Points](#extension-points)
12. [Gotchas and Limitations](#gotchas-and-limitations)

## Overview

The Limit system provides:
- **Resource protection**: Semaphore-based resource limits (e.g., connection pools)
- **Rate limiting**: Time-based limits with multiple algorithms (TokenBucket, GCRA, etc.)
- **Multi-dimensional limiting**: Atomic acquisition of multiple limits simultaneously
- **Multi-region/multi-account support**: Load-balanced distribution across independent limit pools
- **Worker integration**: Seamless integration with all worker execution modes

**Design Philosophy:**
- **Separation of concerns**: Data containers (Limit) separate from executors (LimitSet) separate from load balancers (LimitPool)
- **Thread-safety at the right level**: Limits are NOT thread-safe; LimitSets provide all synchronization
- **Always available**: Workers always have `self.limits` even without configuration (empty LimitSet)
- **Private load balancing**: LimitPool is private to each worker (fast, scalable)
- **Shared enforcement**: LimitSets are shared across workers (coordinated limiting)

## Three-Layer Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                         Layer 3                             │
│                       LimitPool                             │
│  (Private per worker, load-balanced LimitSet selection)     │
│                                                             │
│  ┌────────────┐ ┌────────────┐ ┌────────────┐            │
│  │ LimitSet 1 │ │ LimitSet 2 │ │ LimitSet N │            │
│  │ (shared)   │ │ (shared)   │ │ (shared)   │            │
│  └────────────┘ └────────────┘ └────────────┘            │
└─────────────────────────────────────────────────────────────┘
                         │
                         ├─ Selects LimitSet (round-robin/random)
                         ├─ Delegates acquire() to selected LimitSet
                         └─ Exposes config from selected LimitSet
                         
┌─────────────────────────────────────────────────────────────┐
│                         Layer 2                             │
│                       LimitSet                              │
│     (Thread-safe executor, atomic multi-limit acquisition)  │
│                                                             │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐                  │
│  │  Limit 1 │ │  Limit 2 │ │  Limit N │                  │
│  │  (data)  │ │  (data)  │ │  (data)  │                  │
│  └──────────┘ └──────────┘ └──────────┘                  │
│                                                             │
│  Provides:                                                  │
│  - Thread-safe acquisition/release                          │
│  - Atomic multi-limit acquisition                           │
│  - Partial acquisition support                              │
│  - Config dict for metadata                                 │
└─────────────────────────────────────────────────────────────┘
                         │
                         ├─ Acquires limits atomically
                         ├─ Manages synchronization
                         └─ Returns LimitSetAcquisition
                         
┌─────────────────────────────────────────────────────────────┐
│                         Layer 1                             │
│                    Limit Definitions                        │
│              (Data containers, NOT thread-safe)             │
│                                                             │
│  RateLimit:                                                 │
│    - Time-based rate limiting                               │
│    - Multiple algorithms (TokenBucket, GCRA, etc.)          │
│    - Requires explicit update() call                        │
│                                                             │
│  CallLimit:                                                 │
│    - Special RateLimit for call counting                    │
│    - Usage always 1, no update needed                       │
│                                                             │
│  ResourceLimit:                                             │
│    - Semaphore-based resource limiting                      │
│    - No time component                                      │
│    - No update needed                                       │
└─────────────────────────────────────────────────────────────┘
```

## Layer 1: Limit Definitions (Data Containers)

### Purpose
Limit classes are simple data containers that define constraints. They are **NOT thread-safe** and cannot be acquired directly.

### Classes

#### `Limit` (Abstract Base)
```python
class Limit(Typed, ABC):
    key: str  # Unique identifier within a LimitSet
    
    @abstractmethod
    def can_acquire(self, requested: int) -> bool:
        """Check if limit can accommodate amount (NOT thread-safe)."""
        
    @abstractmethod
    def validate_usage(self, requested: int, used: int) -> None:
        """Validate actual usage vs requested."""
        
    @abstractmethod
    def get_stats(self) -> Dict[str, Any]:
        """Get current statistics."""
```

**Key Properties:**
- **NOT thread-safe**: All internal state is unprotected
- **Data container**: Only stores configuration and provides query methods
- **Morphic Typed**: Immutable after creation, validated at construction

#### `RateLimit`
Time-based rate limiting with multiple algorithms.

```python
class RateLimit(Limit):
    key: str
    window_seconds: float
    capacity: int
    algorithm: RateLimitAlgorithm  # TokenBucket, GCRA, SlidingWindow, etc.
    _impl: BaseRateLimiter  # Algorithm implementation (NOT thread-safe!)
```

**Characteristics:**
- Requires explicit `acq.update(usage={key: amount})` call
- Usage can be less than requested (refunds unused tokens, algorithm-dependent)
- Usage cannot exceed requested
- Internal `_impl` is NOT thread-safe

**Supported Algorithms:**
- `TokenBucket`: Burst-friendly, continuous refill
- `LeakyBucket`: Smooth traffic shaping
- `SlidingWindow`: Precise rolling window
- `FixedWindow`: Simple but allows 2x burst at boundaries
- `GCRA`: Most precise, theoretical arrival time tracking

#### `CallLimit`
Special case of RateLimit for counting calls.

```python
class CallLimit(RateLimit):
    key: str = "call_count"  # Fixed key
```

**Characteristics:**
- Usage is always 1 (validated and enforced)
- No update needed - handled automatically
- Perfect for call rate limits independent of resource usage

#### `ResourceLimit`
Semaphore-based resource limiting (e.g., connection pools).

```python
class ResourceLimit(Limit):
    key: str
    capacity: int
    _current_usage: int  # Tracked internally (NOT thread-safe!)
```

**Characteristics:**
- No time component (unlike RateLimit)
- No update needed - acquired amount is always used
- Automatic release on context exit
- Internal `_current_usage` is NOT thread-safe

### Thread-Safety Contract

**CRITICAL**: Limit objects provide ZERO thread-safety guarantees:
- `can_acquire()`: NOT thread-safe, pure query
- Internal state (`_impl`, `_current_usage`): NOT protected by locks
- Multiple threads calling `can_acquire()` simultaneously: UNDEFINED BEHAVIOR

**Responsibility**: LimitSet provides ALL thread-safety via external locking.

### Adding New Limit Types

To add a new limit type:

1. **Inherit from `Limit`**:
   ```python
   class MyCustomLimit(Limit):
       key: str
       my_config: int
   ```

2. **Implement required methods**:
   - `can_acquire(requested: int) -> bool`: Check availability
   - `validate_usage(requested: int, used: int)`: Validate usage
   - `get_stats() -> Dict[str, Any]`: Return statistics

3. **Update `BaseLimitSet._acquire_all()`**:
   - Add case for your limit type
   - Implement acquisition logic
   
4. **Update `BaseLimitSet._release_acquisitions()`**:
   - Add case for your limit type
   - Implement release logic

5. **Handle in multiprocess/Ray implementations**:
   - Override `_can_acquire_all()` in `MultiprocessSharedLimitSet` if shared state needed
   - Override `_can_acquire_all()` in `RaySharedLimitSet` if centralized state needed

## Layer 2: LimitSet (Thread-Safe Executor)

### Purpose
LimitSet is a **factory function** that creates thread-safe limit executors. It handles:
- Thread-safe acquisition and release
- Atomic multi-limit acquisition
- Partial acquisition (nested patterns)
- Backend selection based on execution mode
- Config dict for metadata

### Factory Function

```python
def LimitSet(
    limits: List[Limit],
    shared: bool = False,  # Default: False for single workers
    mode: Union[str, ExecutionMode] = "sync",  # Default: sync (threading.Lock)
    config: Optional[dict] = None,  # Metadata accessible via acquisition.config
) -> Union[InMemorySharedLimitSet, MultiprocessSharedLimitSet, RaySharedLimitSet]:
    """Factory function to create appropriate LimitSet implementation."""
```

**Backend Selection:**
| Mode | Implementation | Synchronization | Use Case |
|------|----------------|----------------|----------|
| `sync`, `thread`, `asyncio` | `InMemorySharedLimitSet` | `threading.Lock`, `threading.Semaphore` | Same process |
| `process` | `MultiprocessSharedLimitSet` | `multiprocessing.Manager` | Multiple processes |
| `ray` | `RaySharedLimitSet` | Ray actor | Distributed cluster |

### Base Class: `BaseLimitSet`

```python
class BaseLimitSet(ABC):
    def __init__(
        self, 
        limits: List[Limit], 
        shared: bool, 
        config: Optional[dict] = None
    ):
        self.limits = limits
        self._limits_by_key: Dict[str, Limit] = {}
        self.shared = shared
        self.config = config if config is not None else {}
        
    @abstractmethod
    def acquire(
        self, 
        requested: Optional[Dict[str, int]] = None, 
        timeout: Optional[float] = None
    ) -> LimitSetAcquisition:
        """Acquire all limits atomically, blocking until available."""
        
    @abstractmethod
    def try_acquire(
        self, 
        requested: Optional[Dict[str, int]] = None
    ) -> LimitSetAcquisition:
        """Try to acquire without blocking."""
        
    @abstractmethod
    def release_limit_set_acquisition(
        self, 
        acquisition: LimitSetAcquisition
    ) -> None:
        """Release an acquisition."""
```

**Common Logic (in base class):**
- `_build_requested_amounts()`: Handle defaults and partial acquisition
- `_can_acquire_all()`: Check if all limits can be acquired
- `_acquire_all()`: Acquire all limits atomically
- `_release_acquisitions()`: Release all acquired limits
- `__getitem__()`: Get limit by key
- `get_stats()`: Get statistics for all limits

### Partial Acquisition Support

**Key Feature**: Supports acquiring subset of limits.

**Rules:**
1. **Empty `requested` (None or `{}`)**: Acquire ALL limits with defaults
   - CallLimit/ResourceLimit: default = 1
   - RateLimit: MUST specify (raises ValueError)

2. **Non-empty `requested`**: Acquire specified limits + auto-include CallLimit/ResourceLimit
   - Explicitly requested: Use specified amounts
   - CallLimit/ResourceLimit not in requested: Auto-add with default = 1
   - RateLimit not in requested: NOT acquired (intentional)

**Example:**
```python
limits = LimitSet(limits=[
    CallLimit(window_seconds=60, capacity=100),
    RateLimit(key="tokens", window_seconds=60, capacity=1000),
    ResourceLimit(key="connections", capacity=10)
])

# Partial acquisition: only tokens
# CallLimit automatically acquired with default 1
# ResourceLimit NOT acquired (not specified)
with limits.acquire(requested={"tokens": 100}) as acq:
    # Only tokens and call_count acquired
    pass
```

### Config Parameter

**Purpose**: Attach metadata to LimitSet accessible during acquisition.

**Use Cases:**
- Multi-region: `{"region": "us-east-1", "endpoint": "..."}`
- Multi-account: `{"account_id": "12345", "api_key": "..."}`
- Service tiers: `{"tier": "premium", "priority": "high"}`

**Properties:**
- Immutable during acquisition (copy made in `LimitSetAcquisition`)
- Empty dict by default
- Accessible via `acquisition.config`

### Implementations

#### `InMemorySharedLimitSet`

**Synchronization:**
- `threading.Lock`: Protects atomic multi-limit acquisition
- `threading.Semaphore` per ResourceLimit: Blocking/unblocking for resources

**Shared State:**
- Limit objects (`_impl` instances) naturally shared in same process
- `can_acquire()` checks local Limit object state

**Acquire Flow:**
```python
def acquire(self, requested, timeout):
    start_time = time.time()
    while True:
        with self._lock:
            if self._can_acquire_all(requested):
                acquisitions = self._acquire_all(requested)
                return LimitSetAcquisition(...)
        
        # Check timeout
        if timeout is not None and (time.time() - start_time) >= timeout:
            raise TimeoutError(...)
        
        time.sleep(global_config.defaults.limit_set_acquire_sleep)
```

**Performance:** 1-5 μs per acquisition (very fast)

#### `MultiprocessSharedLimitSet`

**Challenge**: Each process has its own copy of Limit objects after pickling.

**Solution**: Maintain all limit state in Manager-managed shared data structures.

**Synchronization:**
- `Manager.Lock()`: Protects atomic multi-limit acquisition
- `Manager.Semaphore()` per ResourceLimit: Blocking for resources
- `Manager.dict()`: Shared state for rate/call limit history
- `Manager.dict()`: Shared state for resource limit current usage

**Shared State:**
```python
# Resource limits: {limit_key: {"current": int}}
self._resource_state: Dict[str, Any] = self._manager.dict()

# Rate/call limits: {limit_key: {"available_tokens": int, "history": List[(timestamp, amount)]}}
self._rate_limit_state: Dict[str, Any] = self._manager.dict()
```

**Override `_can_acquire_all()`:**
- MUST use Manager-managed shared state, NOT local Limit objects
- Each process's Limit._impl is a separate instance
- Manager dict provides single source of truth

```python
def _can_acquire_all(self, requested_amounts):
    current_time = time.time()
    for key, amount in requested_amounts.items():
        limit = self._limits_by_key[key]
        
        if isinstance(limit, ResourceLimit):
            # Check shared state, not local limit._current_usage
            resource_state = self._resource_state[key]
            if resource_state["current"] + amount > limit.capacity:
                return False
                
        elif isinstance(limit, (RateLimit, CallLimit)):
            # Check shared state, not local limit._impl
            rate_state = self._rate_limit_state[key]
            if rate_state["available_tokens"] < amount:
                return False
    
    return True
```

**Performance:** 50-100 μs per acquisition (Manager overhead)

#### `RaySharedLimitSet`

**Challenge**: Distributed workers across cluster, each with own Limit object copy.

**Solution**: Centralized Ray actor (`LimitTrackerActor`) maintains all state.

**Architecture:**
```
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│   Worker 1   │     │   Worker 2   │     │   Worker N   │
│ (Ray Actor)  │     │ (Ray Actor)  │     │ (Ray Actor)  │
└──────────────┘     └──────────────┘     └──────────────┘
        │                   │                     │
        │                   │                     │
        └───────────────────┼─────────────────────┘
                            │
                            │ Ray remote calls
                            ▼
                  ┌────────────────────┐
                  │  LimitTrackerActor │
                  │  (Centralized)     │
                  │                    │
                  │  - All limit state │
                  │  - Acquisition     │
                  │  - Release         │
                  └────────────────────┘
```

**LimitTrackerActor:**
```python
@ray.remote(num_cpus=0.01)
class LimitTrackerActor:
    def __init__(self, limits: List[Limit]):
        # Deep copy limits to avoid sharing across actors
        # Maintains all state centrally
        
    def can_acquire_all(self, requested: Dict[str, int]) -> bool:
        """Check if all can be acquired."""
        
    def acquire_all(self, requested: Dict[str, int]) -> Dict[str, Any]:
        """Acquire all limits atomically."""
        
    def release_acquisitions(self, ...):
        """Release acquisitions."""
```

**Override `_can_acquire_all()`:**
```python
def _can_acquire_all(self, requested_amounts):
    # Delegate to centralized actor
    return ray.get(self._tracker.can_acquire_all.remote(requested_amounts))
```

**Performance:** 500-1000 μs per acquisition (network + actor overhead)

### LimitSetAcquisition

**Purpose**: Track acquisition state and coordinate release.

```python
class LimitSetAcquisition:
    limit_set: "LimitSet"
    acquisitions: Dict[str, Acquisition]  # Per-limit acquisitions
    successful: bool
    config: dict  # Copy of LimitSet.config (immutable)
    _updated_keys: Set[str]  # Track which RateLimits were updated
    _released: bool
    
    def update(self, usage: Dict[str, int]) -> None:
        """Update usage for RateLimits."""
        
    def __enter__(self) -> "LimitSetAcquisition":
        """Context manager entry."""
        
    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Context manager exit - releases acquisition."""
```

**Update Requirements:**
- **RateLimits**: MUST call `update()` before context exit
- **CallLimits**: No update needed (usage always 1)
- **ResourceLimits**: No update needed (acquired = used)

**Validation on `__exit__`:**
```python
def __exit__(self, exc_type, exc_val, exc_tb):
    if not self.successful:
        return  # Failed acquisition, nothing to release
    
    if self._released:
        return  # Already released
    
    # Check that all RateLimits were updated
    for key, acq in self.acquisitions.items():
        if isinstance(acq.limit, RateLimit):
            if key not in self._updated_keys:
                raise RuntimeError(
                    f"RateLimit '{key}' was not updated. "
                    f"Call acq.update(usage={{'{key}': amount}}) before exit."
                )
    
    # Release via LimitSet
    self.limit_set.release_limit_set_acquisition(self)
    self._released = True
```

## Layer 3: LimitPool (Load-Balanced Multi-LimitSet Wrapper)

### Purpose
LimitPool aggregates multiple independent LimitSets with load balancing. It enables:
- **Multi-region/multi-account**: Each LimitSet represents different region/account
- **Reduced contention**: Workers acquire from different LimitSets
- **Higher throughput**: More concurrent acquisitions without blocking
- **Scalability**: Add more LimitSets to increase capacity

### Architecture

**Key Design Decision**: LimitPool is **private** to each worker (NOT shared).

**Why Private?**
- **No synchronization overhead**: Load balancing is local, no locks needed
- **Fast selection**: Direct array indexing or random selection
- **Scalable**: 1000 workers = 1000 LimitPools (no shared bottleneck)

**What IS Shared?**
- **LimitSets within the pool**: All workers use same shared LimitSets
- **Limit enforcement**: Coordinated across all workers via shared LimitSets

```python
class LimitPool(Typed):
    # Public immutable attributes
    limit_sets: List[BaseLimitSet]
    load_balancing: Optional[LoadBalancingAlgorithm] = None  # Defaults from global_config
    worker_index: Optional[int] = None  # Defaults from global_config
    
    # Private mutable attribute
    _balancer: Any = PrivateAttr()  # Load balancer instance
```

**Inheritance**: Uses `morphic.Typed` (Pydantic BaseModel) for:
- Immutable public attributes after creation
- Validation at construction
- Private attributes via `PrivateAttr`

### Load Balancing

**Supported Algorithms:**

1. **Round-Robin** (default):
   - Sequential selection: 0, 1, 2, 0, 1, 2, ...
   - With offset: Worker N starts at index N
   - Minimizes overlap between workers
   - Best for persistent worker pools

2. **Random**:
   - Random selection from pool
   - Stateless, zero overhead
   - Best for on-demand workers or bursty workloads

**Implementation:**
```python
def post_initialize(self):
    # Apply defaults from global_config if not specified
    if self.load_balancing is None:
        self.load_balancing = global_config.defaults.limit_pool_load_balancing
    if self.worker_index is None:
        self.worker_index = global_config.defaults.limit_pool_worker_index
    
    # Create balancer
    if self.load_balancing == LoadBalancingAlgorithm.Random:
        balancer = RandomBalancer()
    elif self.load_balancing == LoadBalancingAlgorithm.RoundRobin:
        balancer = RoundRobinBalancer(offset=self.worker_index)
    
    object.__setattr__(self, "_balancer", balancer)
```

**Round-Robin with Offset:**
- Worker 0: selects 0, 1, 2, 0, 1, 2, ...
- Worker 1: selects 1, 2, 0, 1, 2, 0, ...
- Worker 2: selects 2, 0, 1, 2, 0, 1, ...

This staggers starting points to minimize contention.

### Acquisition Flow

```python
def acquire(self, requested, timeout):
    # 1. Select LimitSet using load balancing
    selected_limitset = self._select_limit_set()
    
    # 2. Delegate to selected LimitSet
    return selected_limitset.acquire(requested=requested, timeout=timeout)

def _select_limit_set(self):
    # Use balancer to select index
    index = self._balancer.select_worker(num_workers=len(self.limit_sets))
    return self.limit_sets[index]
```

**Key Points:**
- No acquisition lock in LimitPool (fast)
- All blocking/synchronization happens in selected LimitSet
- Config from selected LimitSet propagates to acquisition

### Serialization for Remote Execution

**Challenge**: `RoundRobinBalancer` contains `threading.Lock` which cannot be pickled.

**Solution**: Custom `__getstate__` and `__setstate__`:

```python
def __getstate__(self):
    """Custom pickle - exclude non-serializable balancer."""
    state = self.__dict__.copy()
    state.pop("_balancer", None)  # Remove balancer with lock
    return state

def __setstate__(self, state):
    """Custom unpickle - recreate balancer."""
    self.__dict__.update(state)
    
    # Recreate balancer based on algorithm and worker_index
    if self.load_balancing == LoadBalancingAlgorithm.Random:
        balancer = RandomBalancer()
    elif self.load_balancing == LoadBalancingAlgorithm.RoundRobin:
        balancer = RoundRobinBalancer(offset=self.worker_index)
    
    object.__setattr__(self, "_balancer", balancer)
```

This allows LimitPool to be serialized for process/Ray workers.

### Index Access

**Integer Indexing ONLY:**
```python
def __getitem__(self, index: int) -> BaseLimitSet:
    """Get LimitSet by integer index."""
    if not isinstance(index, int):
        raise TypeError(
            "LimitPool indices must be integers. "
            "String key access not supported because LimitSets may have different keys."
        )
    return self.limit_sets[index]
```

**Why No String Keys?**
- Different LimitSets may have different limit keys
- Ambiguous which LimitSet to query for a key
- Forces explicit: `pool[0]["tokens"]` (clear which LimitSet)

## Worker Integration

### Goal
Workers **always** have `self.limits` available, even without configuration.

### Transformation Pipeline

```
User Input (limits parameter)
        │
        ├─ None
        ├─ List[Limit]
        ├─ LimitSet (BaseLimitSet)
        ├─ List[LimitSet]
        └─ LimitPool
        │
        ▼
_transform_worker_limits(limits, mode, is_pool, worker_index)
        │
        ├─ Validates mode compatibility
        ├─ Handles shared vs non-shared
        ├─ Wraps in LimitPool if needed
        │
        ▼
    LimitPool instance
        │
        ▼
_create_worker_wrapper(worker_cls, limits, retry_config)
        │
        ├─ Creates wrapper class
        ├─ Sets self.limits in __init__
        ├─ Handles List[Limit] for Ray/Process
        │     (creates LimitSet + LimitPool inside actor/process)
        │
        ▼
Worker instance with self.limits
```

### `_transform_worker_limits()`

**Purpose**: Convert user input to LimitPool.

**Cases:**

1. **None → Empty LimitPool**:
   ```python
   empty_limitset = LimitSet(limits=[], shared=False, mode=ExecutionMode.Sync)
   return LimitPool(limit_sets=[empty_limitset], worker_index=worker_index)
   ```

2. **List[Limit] → LimitPool with single LimitSet**:
   ```python
   # For pool
   limitset = LimitSet(limits=limits, shared=True, mode=mode)
   return LimitPool(limit_sets=[limitset], worker_index=worker_index)
   
   # For Ray/Process single worker
   return limits  # List - will be wrapped remotely
   ```

3. **List[LimitSet] → LimitPool**:
   ```python
   # Validate all are shared and compatible with mode
   for ls in limits:
       if not ls.shared:
           raise ValueError("All LimitSets must be shared")
       _validate_mode_compatibility(ls, mode)
   
   return LimitPool(limit_sets=limits, worker_index=worker_index)
   ```

4. **LimitSet → LimitPool with single LimitSet**:
   ```python
   # Validate mode compatibility
   _validate_mode_compatibility(limits, mode)
   return LimitPool(limit_sets=[limits], worker_index=worker_index)
   ```

5. **LimitPool → Pass through**:
   ```python
   return limits  # Already a LimitPool
   ```

**Mode Compatibility Validation:**
```python
def _validate_mode_compatibility(limit_set, mode):
    if isinstance(limit_set, InMemorySharedLimitSet):
        if mode not in (ExecutionMode.Sync, ExecutionMode.Asyncio, ExecutionMode.Threads):
            raise ValueError(f"InMemorySharedLimitSet incompatible with {mode}")
    
    elif isinstance(limit_set, MultiprocessSharedLimitSet):
        if mode != ExecutionMode.Processes:
            raise ValueError(f"MultiprocessSharedLimitSet incompatible with {mode}")
    
    elif isinstance(limit_set, RaySharedLimitSet):
        if mode != ExecutionMode.Ray:
            raise ValueError(f"RaySharedLimitSet incompatible with {mode}")
```

### `_create_worker_wrapper()`

**Purpose**: Create wrapper class that injects `self.limits`.

**For Ray/Process Workers:**
- If `limits` is `List[Limit]`: Keep as list, wrap in worker's `__init__`
- This avoids serializing LimitSet (which contains locks)

```python
class WorkerWithLimits(worker_cls):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # If limits is a list, create LimitSet + LimitPool (inside actor/process)
        if isinstance(limits, list):
            limit_set = LimitSet(limits=limits, shared=False, mode=ExecutionMode.Sync)
            limit_pool = LimitPool(limit_sets=[limit_set])
        else:
            limit_pool = limits  # Already a LimitPool
        
        # Set on instance (bypasses Typed/BaseModel frozen protection)
        object.__setattr__(self, "limits", limit_pool)
```

### Worker Pool Integration

**Key Requirement**: Each worker needs unique `worker_index` for round-robin.

**Implementation in `WorkerProxyPool`:**

```python
def _initialize_pool(self):
    """Create persistent workers with unique indices."""
    for i in range(self.max_workers):
        worker = self._create_worker(worker_index=i)
        self._workers.append(worker)

def _create_worker(self, worker_index: int = 0):
    """Create worker with specific index."""
    # Transform limits with this worker's index
    worker_limits = _transform_worker_limits(
        limits=self.limits,
        mode=self.mode,
        is_pool=False,  # Each worker gets its own LimitPool
        worker_index=worker_index,
    )
    
    # Create worker proxy with limits
    return WorkerProxy(
        worker_cls=self.worker_cls,
        limits=worker_limits,
        init_args=self.init_args,
        init_kwargs=self.init_kwargs,
    )
```

**On-Demand Workers:**
- Use `_on_demand_counter` to assign unique indices
- Increment counter for each on-demand worker created

```python
def method_wrapper(*args, **kwargs):
    if self.on_demand:
        # Get next worker index
        with self._on_demand_lock:
            worker_index = self._on_demand_counter
            self._on_demand_counter += 1
        
        # Create worker with unique index
        worker = self._create_worker(worker_index=worker_index)
        # ...
```

## Thread-Safety Model

### Three Levels of Thread-Safety

1. **Limit (Layer 1): NOT thread-safe**
   - Pure data containers
   - No internal locking
   - Caller responsible for synchronization

2. **LimitSet (Layer 2): Thread-safe**
   - All public methods protected by locks
   - Atomic multi-limit acquisition
   - Safe for concurrent use

3. **LimitPool (Layer 3): No thread-safety needed**
   - Private per worker (no sharing)
   - Local load balancing (no synchronization)
   - Delegates to thread-safe LimitSets

### Synchronization Primitives by Backend

| Backend | Atomic Acquisition | Resource Blocking |
|---------|-------------------|-------------------|
| `InMemorySharedLimitSet` | `threading.Lock` | `threading.Semaphore` |
| `MultiprocessSharedLimitSet` | `Manager.Lock()` | `Manager.Semaphore()` |
| `RaySharedLimitSet` | Ray actor (single-threaded) | Actor state |

### Critical Sections

**InMemorySharedLimitSet:**
```python
def acquire(self, requested, timeout):
    while True:
        with self._lock:  # CRITICAL SECTION START
            if self._can_acquire_all(requested):
                acquisitions = self._acquire_all(requested)
                return LimitSetAcquisition(...)
        # CRITICAL SECTION END
        
        time.sleep(sleep_time)
```

**Why Entire Check + Acquire is Locked:**
- Prevents TOCTOU (Time-Of-Check-Time-Of-Use) races
- Ensures atomicity across multiple limits
- Brief lock hold (microseconds)

**Release Flow:**
```python
def release_limit_set_acquisition(self, acquisition):
    with self._lock:  # CRITICAL SECTION
        self._release_acquisitions(acquisition.acquisitions, ...)
```

## Acquisition Flow

### Complete Acquisition Flow

```
User Code
    │
    └─► limits.acquire(requested={"tokens": 100})
            │
            ▼
        LimitPool
            │
            ├─► _select_limit_set()  [No lock, fast]
            │       │
            │       └─► _balancer.select_worker(num_workers)
            │               │
            │               └─► Returns index (round-robin or random)
            │
            ▼
        selected_limitset.acquire(requested={"tokens": 100})
            │
            ▼
        InMemorySharedLimitSet.acquire()
            │
            ├─► while True:
            │       │
            │       ├─► with self._lock:  [LOCK ACQUIRED]
            │       │       │
            │       │       ├─► _build_requested_amounts()
            │       │       │       └─► Add CallLimit/ResourceLimit defaults
            │       │       │
            │       │       ├─► _can_acquire_all()
            │       │       │       └─► Check each limit.can_acquire()
            │       │       │
            │       │       └─► if True:
            │       │               │
            │       │               ├─► _acquire_all()
            │       │               │       │
            │       │               │       ├─► ResourceLimit: Acquire semaphore
            │       │               │       ├─► RateLimit: Call _impl.try_acquire()
            │       │               │       └─► CallLimit: Automatic (usage=1)
            │       │               │
            │       │               └─► return LimitSetAcquisition(
            │       │                       acquisitions=...,
            │       │                       config=self.config  [COPIED]
            │       │                   )
            │       │   [LOCK RELEASED]
            │       │
            │       └─► if timeout exceeded:
            │               raise TimeoutError(...)
            │
            └─► time.sleep(sleep_time)
                    │
                    └─► Loop back
                    
LimitSetAcquisition.__enter__()
    │
    └─► return self

User Code (inside with block)
    │
    ├─► Access acq.config (copied, immutable)
    ├─► Do work
    └─► acq.update(usage={"tokens": 80})  [Track which RateLimits updated]

LimitSetAcquisition.__exit__()
    │
    ├─► Validate all RateLimits were updated
    │       └─► if not: raise RuntimeError(...)
    │
    └─► limit_set.release_limit_set_acquisition(self)
            │
            ▼
        InMemorySharedLimitSet.release_limit_set_acquisition()
            │
            └─► with self._lock:  [LOCK ACQUIRED]
                    │
                    └─► _release_acquisitions()
                            │
                            ├─► ResourceLimit: Release semaphore, decrement usage
                            ├─► RateLimit: Refund unused tokens (requested - used)
                            └─► CallLimit: Nothing (usage always 1)
                    [LOCK RELEASED]
```

### Key Points

1. **Lock Granularity**: Lock held only during check + acquire and release (brief)
2. **Config Copying**: `self.config` copied to `acquisition.config` to prevent mutations
3. **Atomic Multi-Limit**: All limits acquired under single lock hold
4. **Rollback on Partial Failure**: If any limit fails, all are released
5. **Refunding**: Unused tokens refunded to RateLimits (algorithm-dependent)

## Shared State Management

### Problem: Multiprocess and Ray

**Challenge**: After pickling, each process/actor has its own copy of Limit objects.

**Impact:**
- `limit.can_acquire()` checks LOCAL state (process-specific copy)
- Different processes have divergent views of limit state
- No coordination = no limiting!

### Solution: Centralized Shared State

#### MultiprocessSharedLimitSet

**Strategy**: Manager-managed dicts for all limit state.

**State Storage:**
```python
# Resource limits: Current usage
self._resource_state: Dict[str, Any] = {
    "connections": {"current": 5}  # Example
}

# Rate/call limits: Available tokens and history
self._rate_limit_state: Dict[str, Any] = {
    "tokens": {
        "available_tokens": 850,
        "history": [(timestamp1, 100), (timestamp2, 50), ...]
    }
}
```

**Override `_can_acquire_all()`:**
```python
def _can_acquire_all(self, requested_amounts):
    for key, amount in requested_amounts.items():
        limit = self._limits_by_key[key]
        
        if isinstance(limit, ResourceLimit):
            # Check SHARED state, not limit._current_usage
            state = self._resource_state[key]
            if state["current"] + amount > limit.capacity:
                return False
        
        elif isinstance(limit, (RateLimit, CallLimit)):
            # Check SHARED state, not limit._impl
            state = self._rate_limit_state[key]
            
            # Simulate rate limiter check using shared history
            available = self._compute_available_tokens(limit, state, current_time)
            if available < amount:
                return False
    
    return True
```

**Synchronization:**
- `Manager.Lock()`: Protects check + acquire atomicity
- `Manager.Semaphore()`: Provides ResourceLimit blocking
- `Manager.dict()`: Single source of truth for all state

#### RaySharedLimitSet

**Strategy**: Centralized Ray actor maintains all state.

**LimitTrackerActor:**
```python
@ray.remote(num_cpus=0.01)
class LimitTrackerActor:
    def __init__(self, limits: List[Limit]):
        # Deep copy limits (each instance has own _impl)
        self._limits = [copy.deepcopy(limit) for limit in limits]
        self._limits_by_key = {limit.key: limit for limit in self._limits}
    
    def can_acquire_all(self, requested: Dict[str, int]) -> bool:
        """Check if all can be acquired (centralized)."""
        for key, amount in requested.items():
            limit = self._limits_by_key[key]
            if not limit.can_acquire(amount):
                return False
        return True
    
    def acquire_all(self, requested: Dict[str, int]) -> Dict[str, Any]:
        """Acquire all limits atomically (centralized)."""
        # ... similar to BaseLimitSet._acquire_all() ...
```

**RaySharedLimitSet delegates all operations:**
```python
def _can_acquire_all(self, requested_amounts):
    # Call actor remotely
    return ray.get(self._tracker.can_acquire_all.remote(requested_amounts))

def _acquire_all(self, requested_amounts):
    # Call actor remotely
    return ray.get(self._tracker.acquire_all.remote(requested_amounts))
```

**Synchronization:**
- Ray actor is single-threaded (no explicit locks needed)
- Actor processes requests serially
- State naturally coordinated

### Performance Implications

| Backend | Overhead | Cause |
|---------|----------|-------|
| InMemory | 1-5 μs | Local lock + memory access |
| Multiprocess | 50-100 μs | Manager IPC + serialization |
| Ray | 500-1000 μs | Network + actor dispatch |

**Trade-off**: Scalability vs latency
- More processes/actors = more parallelism
- But each acquisition has higher latency
- LimitPool helps by reducing contention on single LimitSet

## Serialization and Remote Execution

### Challenge

**Problem**: Python's `threading` primitives cannot be pickled.

**Affected Classes:**
- `threading.Lock` (in InMemorySharedLimitSet)
- `threading.Semaphore` (in InMemorySharedLimitSet)
- `RoundRobinBalancer` (contains `threading.Lock`)

### Solutions

#### 1. List[Limit] for Ray/Process Single Workers

**Strategy**: Don't serialize LimitSet; serialize Limit list instead.

```python
def _transform_worker_limits(limits, mode, is_pool, worker_index):
    if isinstance(limits, list) and all(isinstance(item, Limit) for item in limits):
        if mode in (ExecutionMode.Ray, ExecutionMode.Processes) and not is_pool:
            # Return list - will be wrapped remotely
            return limits
```

**In `_create_worker_wrapper()`:**
```python
if isinstance(limits, list):
    # Inside actor/process: create LimitSet + LimitPool
    limit_set = LimitSet(limits=limits, shared=False, mode=ExecutionMode.Sync)
    limit_pool = LimitPool(limit_sets=[limit_set])
    object.__setattr__(self, "limits", limit_pool)
```

**Benefits:**
- Avoids pickling locks
- Each actor/process has own private LimitSet (threading.Lock works locally)

#### 2. Custom Pickling for LimitPool

**Strategy**: Exclude balancer during pickle, recreate on unpickle.

```python
def __getstate__(self):
    state = self.__dict__.copy()
    state.pop("_balancer", None)  # Remove balancer (has lock)
    return state

def __setstate__(self, state):
    self.__dict__.update(state)
    
    # Recreate balancer based on configuration
    if self.load_balancing == LoadBalancingAlgorithm.Random:
        balancer = RandomBalancer()
    elif self.load_balancing == LoadBalancingAlgorithm.RoundRobin:
        balancer = RoundRobinBalancer(offset=self.worker_index)
    
    object.__setattr__(self, "_balancer", balancer)
```

**Benefits:**
- LimitPool can be pickled for Ray/Process
- Balancer recreated with same configuration
- Lock recreated fresh in new process

#### 3. Manager/Ray Actor for Shared State

**Strategy**: Use serializable shared state primitives.

**Multiprocess:**
- `Manager.Lock()` - Serializable
- `Manager.Semaphore()` - Serializable
- `Manager.dict()` - Serializable

**Ray:**
- Ray actor reference - Serializable
- All state lives in actor (no local state to pickle)

## Extension Points

### Adding New Limit Types

**Steps:**

1. **Create Limit subclass** (Layer 1):
   ```python
   class MyCustomLimit(Limit):
       key: str
       my_capacity: int
       _my_state: int = 0  # NOT thread-safe!
       
       def can_acquire(self, requested: int) -> bool:
           return self._my_state + requested <= self.my_capacity
       
       def validate_usage(self, requested: int, used: int):
           if used > requested:
               raise ValueError(...)
       
       def get_stats(self):
           return {"key": self.key, "usage": self._my_state, ...}
   ```

2. **Update `BaseLimitSet._acquire_all()`**:
   ```python
   elif isinstance(limit, MyCustomLimit):
       # Custom acquisition logic
       limit._my_state += amount
       acquisitions[key] = Acquisition(...)
   ```

3. **Update `BaseLimitSet._release_acquisitions()`**:
   ```python
   elif isinstance(limit, MyCustomLimit):
       # Custom release logic
       limit._my_state -= amount
   ```

4. **Update `MultiprocessSharedLimitSet`**:
   ```python
   # Add shared state
   self._my_custom_state = self._manager.dict()
   
   # Override _can_acquire_all() to use shared state
   def _can_acquire_all(self, requested_amounts):
       # ...
       elif isinstance(limit, MyCustomLimit):
           state = self._my_custom_state[key]
           if state["current"] + amount > limit.my_capacity:
               return False
   ```

5. **Update `RaySharedLimitSet`**:
   - Ensure `LimitTrackerActor` handles new limit type
   - May need to add actor methods if complex state

### Adding New Load Balancing Algorithms

**Steps:**

1. **Add to enum** (`constants.py`):
   ```python
   class LoadBalancingAlgorithm(str, Enum):
       RoundRobin = "round_robin"
       Random = "random"
       MyAlgorithm = "my_algorithm"  # NEW
   ```

2. **Create balancer class** (`algorithms/load_balancing.py`):
   ```python
   class MyBalancer(BaseLoadBalancer):
       def select_worker(self, num_workers: int) -> int:
           # Your selection logic
           return selected_index
       
       def get_stats(self):
           return {"algorithm": "MyAlgorithm", ...}
   ```

3. **Update `LimitPool.post_initialize()`**:
   ```python
   elif self.load_balancing == LoadBalancingAlgorithm.MyAlgorithm:
       balancer = MyBalancer()
   ```

4. **Handle serialization** if balancer has non-picklable state:
   - Add logic to `__getstate__` and `__setstate__`

### Adding New LimitSet Backends

**Steps:**

1. **Create backend class**:
   ```python
   class MyCustomLimitSet(BaseLimitSet):
       def __init__(self, limits, shared=True, config=None):
           super().__init__(limits, shared=True, config=config)
           # Initialize your synchronization primitives
       
       def acquire(self, requested, timeout):
           # Your acquisition logic
       
       def try_acquire(self, requested):
           # Your non-blocking acquisition logic
       
       def release_limit_set_acquisition(self, acquisition):
           # Your release logic
       
       def _acquire_resource(self, limit, amount):
           # Your resource acquisition logic
       
       def _release_resource(self, limit, amount):
           # Your resource release logic
   ```

2. **Update `LimitSet` factory** (`limit_set.py`):
   ```python
   def LimitSet(limits, shared, mode, config):
       # ...
       elif mode == ExecutionMode.MyMode:
           return MyCustomLimitSet(limits, shared=True, config=config)
   ```

3. **Update `_validate_mode_compatibility()`** (`base_worker.py`):
   ```python
   elif isinstance(ls, MyCustomLimitSet):
       if mode != ExecutionMode.MyMode:
           raise ValueError(...)
   ```

4. **Handle shared state** if not naturally shared:
   - Override `_can_acquire_all()` to use shared state source
   - Ensure all processes/actors see same state

## Gotchas and Limitations

### 1. Limit Objects Are NOT Thread-Safe

**CRITICAL**: Never use Limit objects directly from multiple threads without external locking.

```python
# ❌ WRONG - Race condition!
limit = RateLimit(key="tokens", window_seconds=60, capacity=1000)

def worker():
    if limit.can_acquire(100):  # NOT thread-safe!
        # Another thread might acquire between check and acquire
        pass

# ✅ CORRECT - Use LimitSet
limitset = LimitSet(limits=[limit], shared=True, mode="thread")

def worker():
    with limitset.acquire(requested={"tokens": 100}):  # Thread-safe
        pass
```

### 2. RateLimit Requires Update

**CRITICAL**: Must call `acq.update()` for RateLimits before context exit.

```python
# ❌ WRONG - RuntimeError on exit!
with limits.acquire(requested={"tokens": 100}) as acq:
    result = operation()
    # Missing acq.update()!

# ✅ CORRECT
with limits.acquire(requested={"tokens": 100}) as acq:
    result = operation()
    acq.update(usage={"tokens": result.actual_tokens})  # Required!
```

### 3. Mode Compatibility

**CRITICAL**: LimitSet mode must match worker mode.

```python
# ❌ WRONG - ValueError!
thread_limitset = LimitSet(limits=[...], shared=True, mode="thread")
worker = Worker.options(mode="process", limits=thread_limitset).init()

# ✅ CORRECT
process_limitset = LimitSet(limits=[...], shared=True, mode="process")
worker = Worker.options(mode="process", limits=process_limitset).init()
```

**Why**: Different backends use different synchronization primitives:
- `thread` uses `threading.Lock` (doesn't work across processes)
- `process` uses `Manager.Lock()` (works across processes)
- `ray` uses Ray actor (works across distributed workers)

### 4. Shared vs Non-Shared

**GOTCHA**: `shared=False` only works with `mode="sync"`.

```python
# ❌ WRONG - ValueError!
limitset = LimitSet(limits=[...], shared=False, mode="thread")

# ✅ CORRECT
limitset = LimitSet(limits=[...], shared=False, mode="sync")
```

**Why**: Non-shared means "no synchronization needed" → only safe for single-threaded sync mode.

### 5. LimitPool String Indexing

**GOTCHA**: `pool["key"]` does NOT work.

```python
pool = LimitPool(limit_sets=[ls1, ls2])

# ❌ WRONG - TypeError!
limit = pool["tokens"]

# ✅ CORRECT - Access LimitSet first, then limit
limit = pool[0]["tokens"]  # Explicit which LimitSet

# OR
limitset = pool[0]
limit = limitset["tokens"]
```

**Why**: Different LimitSets may have different limit keys. Ambiguous which LimitSet to query.

### 6. Config Immutability

**GOTCHA**: `acquisition.config` is a copy, modifying it doesn't affect LimitSet.

```python
limitset = LimitSet(limits=[...], config={"region": "us-east-1"})

with limitset.acquire() as acq:
    acq.config["region"] = "modified"  # Local change only!
    
print(limitset.config["region"])  # Still "us-east-1"
```

**Why**: Config is copied during acquisition to prevent mutations. This is intentional for thread-safety.

### 7. Empty LimitSet Still Requires Context Manager

**GOTCHA**: Even empty LimitSet must use context manager or manual release.

```python
empty_limitset = LimitSet(limits=[])

# ❌ WRONG - Acquisition never released
acq = empty_limitset.acquire()
do_work()

# ✅ CORRECT
with empty_limitset.acquire():
    do_work()
```

**Why**: Consistent API, even if empty LimitSet is no-op.

### 8. Partial Acquisition Automatic Inclusion

**GOTCHA**: CallLimit/ResourceLimit automatically included even if not requested.

```python
limits = LimitSet(limits=[
    CallLimit(window_seconds=60, capacity=100),
    RateLimit(key="tokens", window_seconds=60, capacity=1000)
])

# Requesting only "tokens"
with limits.acquire(requested={"tokens": 100}) as acq:
    # CallLimit ALSO acquired automatically with default=1!
    pass
```

**Why**: CallLimit/ResourceLimit are almost always needed. Explicit exclusion not supported.

### 9. Serialization of LimitPool

**GOTCHA**: LimitPool with RoundRobinBalancer contains lock, but pickling works via custom methods.

```python
# ✅ This works - custom __getstate__ handles it
pool = LimitPool(limit_sets=[...], load_balancing="round_robin")
pickled = pickle.dumps(pool)
unpickled = pickle.loads(pickled)
# Balancer recreated correctly
```

**But**: If you subclass LimitPool and add non-serializable state, you must handle it in `__getstate__` / `__setstate__`.

### 10. Worker Pools Get Different worker_index

**GOTCHA**: Each worker in pool gets different `worker_index`.

```python
pool = Worker.options(
    mode="thread",
    max_workers=5,
    limits=[ls1, ls2, ls3]  # Creates LimitPool per worker
).init()

# Worker 0: LimitPool with worker_index=0 (starts round-robin at 0)
# Worker 1: LimitPool with worker_index=1 (starts round-robin at 1)
# Worker 2: LimitPool with worker_index=2 (starts round-robin at 2)
# ...
```

**Why**: Staggers round-robin starting points to reduce contention.

### 11. Multiprocess/Ray Shared State Overhead

**GOTCHA**: `MultiprocessSharedLimitSet` and `RaySharedLimitSet` are 10-100x slower than `InMemorySharedLimitSet`.

**Why**: IPC/network overhead for every acquisition.

**Mitigation**: Use LimitPool to reduce contention on single LimitSet.

### 12. RateLimit Algorithms Have Different Refund Behavior

**GOTCHA**: Not all algorithms support refunding unused tokens.

| Algorithm | Refund Support |
|-----------|----------------|
| TokenBucket | Yes |
| GCRA | Yes |
| SlidingWindow | No |
| LeakyBucket | No |
| FixedWindow | No |

```python
limit = RateLimit(key="tokens", algorithm=RateLimitAlgorithm.SlidingWindow, ...)

with limitset.acquire(requested={"tokens": 100}) as acq:
    acq.update(usage={"tokens": 50})  # Requested 100, used 50
    # 50 unused tokens NOT refunded (SlidingWindow doesn't support refund)
```

**Why**: Algorithm-specific implementation. TokenBucket/GCRA continuously refill; others don't.

### 13. Timeout Only Applies to Acquisition

**GOTCHA**: `timeout` parameter only applies to `acquire()`, not to work inside context manager.

```python
# timeout=5 applies to ACQUIRING limits, not to do_work()
with limitset.acquire(requested={"tokens": 100}, timeout=5.0) as acq:
    do_work()  # This can take as long as needed
    acq.update(usage={"tokens": 80})
```

**Why**: Timeout is for blocking on limits, not for user code execution.

### 14. try_acquire Still Needs Context Manager

**GOTCHA**: Even failed `try_acquire` should use context manager (or manual check).

```python
acq = limitset.try_acquire(requested={"tokens": 100})

if acq.successful:
    with acq:  # Still use context manager for successful acquisition
        do_work()
        acq.update(usage={"tokens": 80})
else:
    # Handle failure
    pass
```

**Why**: Successful acquisition must be released via context manager.

## Summary

**Key Architectural Principles:**

1. **Separation of concerns**: Limits (data) → LimitSet (executor) → LimitPool (load balancer)
2. **Thread-safety at the right level**: Only LimitSet is thread-safe, not Limits or LimitPool
3. **Always available**: Workers always have `self.limits`, even when empty
4. **Private load balancing**: LimitPool is private per worker (fast, scalable)
5. **Shared enforcement**: LimitSets are shared across workers (coordinated limiting)
6. **Config propagation**: Config flows from LimitSet → acquisition.config
7. **Atomic multi-limit**: All limits acquired atomically under single lock
8. **Centralized state for distributed**: Multiprocess/Ray use centralized shared state

**Extension Points:**

- New Limit types: Subclass `Limit`, update `BaseLimitSet._acquire_all()` and `_release_acquisitions()`
- New load balancing: Add to enum, create balancer, update `LimitPool.post_initialize()`
- New LimitSet backends: Subclass `BaseLimitSet`, update `LimitSet` factory

**Common Pitfalls:**

- Using Limit objects directly without LimitSet
- Forgetting to call `acq.update()` for RateLimits
- Mode incompatibility between LimitSet and Worker
- String indexing on LimitPool
- Expecting config mutations to affect LimitSet

For usage examples and best practices, see [User Guide: Limits](../user-guide/limits.md).

