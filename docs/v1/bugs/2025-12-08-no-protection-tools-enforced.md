# Issue: No enforced protection/pinning tools in pruning/stashing flows

**Date**: 2025-12-08  
**Severity**: Medium  
**Component**: protection / pruning  
**Status**: Open

## Description
There is no implemented MCP tool to set/clear protection (pin) flags, and pruning/stashing does not enforce protection by default. Critical segments can be pruned/stashed unintentionally.

## Impact
- Risk of losing essential context during pruning/stashing.
- Users cannot explicitly safeguard high-priority segments.

## Proposed Solution (if known)
- Add pin/unpin tools (or extend existing) and honor `pinned` in pruning/stashing defaults.
- Surface protected segments in monitoring outputs for visibility.

