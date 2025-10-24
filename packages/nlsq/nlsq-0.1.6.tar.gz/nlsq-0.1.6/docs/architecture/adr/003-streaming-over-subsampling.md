# ADR-003: Streaming Optimization Over Subsampling

**Status**: Accepted

**Date**: 2025-10-17

**Deciders**: Wei Chen (Maintainer), Code Quality Review

## Context

NLSQ v0.1.x included a subsampling feature for large datasets that randomly sampled data when datasets exceeded a threshold. This approach had several issues:

### Problems with Subsampling
1. **Accuracy Loss**: Random sampling reduced data from 85-95% accuracy to potential information loss
2. **Non-deterministic Results**: Different runs could produce different results even with same seed
3. **Complexity**: Added ~250 lines of code with complex chunking logic
4. **User Confusion**: Parameters like `enable_sampling`, `sampling_threshold`, `max_sampled_size` were poorly understood
5. **False Economy**: Tried to save memory but lost scientific accuracy

### Alternative Considered
**Streaming Optimization**: Process 100% of data in chunks using online optimization algorithms, integrated with existing chunked fitting infrastructure.

## Decision

**Remove subsampling entirely in favor of streaming optimization.**

### Key Changes
1. Removed ~250 lines of subsampling code from `large_dataset.py`
2. Deprecated parameters: `enable_sampling`, `sampling_threshold`, `max_sampled_size`
   - Parameters still accepted but emit DeprecationWarning
   - Will be removed in a future major version
3. Integrated streaming optimizer for datasets that don't fit in memory
4. Maintained backward compatibility with deprecation warnings
5. Updated `LargeDatasetFitter` to use streaming by default

### Migration Path
- Deprecation warnings guide users to remove old parameters
- Old code still works (with warnings) to ease transition
- Simply remove the deprecated parameters from your code

## Consequences

### Positive
✅ **100% Data Utilization**: No accuracy loss from random sampling
✅ **Deterministic Results**: Same data always produces same fit
✅ **Simpler Code**: 250 fewer lines to maintain
✅ **Better Science**: Processes all data for maximum statistical power
✅ **Streaming Integration**: Reuses existing chunked fitting infrastructure
✅ **Clear API**: Fewer confusing parameters

### Negative
⚠️ **Deprecation**: Old parameters emit warnings (backward compatible)
  - **Mitigation**: Clear warning messages guide migration
❌ **Slightly Slower**: Processing 100% of data takes longer than sampling 85%
  - **Mitigation**: Minimal impact due to efficient streaming implementation
❌ **Requires h5py**: Now a required dependency instead of optional
  - **Mitigation**: h5py is standard in scientific Python ecosystem

### Performance Impact
- **Before** (subsampling): 85-95% of data, faster but less accurate
- **After** (streaming): 100% of data, slightly slower but scientifically correct
- **Typical overhead**: 10-20% longer runtime for 100% accuracy

## References

- [Large Dataset Implementation](../../../nlsq/large_dataset.py)
- [Streaming Optimizer](../../../nlsq/streaming_optimizer.py)
- [Large Dataset Guide](../../guides/large_datasets.rst)

## Status Updates

- **2025-10-17**: Accepted and parameters deprecated
- **2025-10-18**: Verified with 1241 tests passing, 100% success rate
- **Note**: Full removal deferred to future major version (backward compatibility maintained)
