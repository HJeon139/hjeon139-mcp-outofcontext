# Bug: AppState Not Initializing Components

**Date**: 2025-12-04  
**Severity**: High  
**Component**: `app_state.py`  
**Status**: Not Fixed

## Description

The `AppState.initialize()` method has all component initialization code commented out, meaning components are never actually created. This prevents the server from functioning.

## Design Specification

According to `docs/v1/tasks/05_context_manager.md` and the component architecture, AppState should initialize:
1. Storage Layer
2. Analysis Engine  
3. GC Engine
4. Context Manager

## Current Implementation

In `src/hjeon139_mcp_outofcontext/app_state.py` (lines 36-68):

```python
async def initialize(self) -> None:
    """Initialize all components with dependency injection."""
    if self._initialized:
        return

    # Components will be implemented in later tasks
    # For now, this is a placeholder structure

    # 1. Initialize Storage Layer (no dependencies)
    # self.storage = StorageLayer(config=self.config)

    # 2. Initialize Analysis Engine (depends on config)
    # self.analysis_engine = AnalysisEngine(config=self.config)

    # 3. Initialize GC Engine (depends on storage)
    # self.gc_engine = GCEngine(storage=self.storage)

    # 4. Initialize Context Manager (depends on all above)
    # self.context_manager = ContextManager(
    #     storage=self.storage,
    #     gc_engine=self.gc_engine,
    #     analysis_engine=self.analysis_engine,
    # )

    self._initialized = True
```

All initialization code is commented out with a note saying "Components will be implemented in later tasks", but tasks 1-5 are complete and components are implemented.

## Impact

- **Critical**: Server cannot function because components are `None`
- Tool handlers will fail when trying to access `app_state.storage`, `app_state.context_manager`, etc.
- Tests may pass because they mock components, but production code won't work

## Location

- `src/hjeon139_mcp_outofcontext/app_state.py:36-68`

## Fix Required

1. Uncomment and fix component initialization code
2. Import the actual component classes:
   - `from .storage import StorageLayer`
   - `from .analysis_engine import AnalysisEngine`
   - `from .gc_engine import GCEngine`
   - `from .context_manager import ContextManager`
   - `from .tokenizer import Tokenizer`
3. Initialize components in correct dependency order:
   ```python
   # 1. Storage Layer (no dependencies)
   self.storage = StorageLayer()
   
   # 2. Tokenizer (no dependencies)
   tokenizer = Tokenizer()
   
   # 3. Analysis Engine (depends on tokenizer)
   self.analysis_engine = AnalysisEngine(tokenizer=tokenizer)
   
   # 4. GC Engine (no dependencies on other components)
   self.gc_engine = GCEngine()
   
   # 5. Context Manager (depends on all above)
   self.context_manager = ContextManager(
       storage=self.storage,
       gc_engine=self.gc_engine,
       analysis_engine=self.analysis_engine,
       tokenizer=tokenizer,
   )
   ```

## References

- Design: `docs/v1/tasks/05_context_manager.md`
- Implementation: `src/hjeon139_mcp_outofcontext/app_state.py`

