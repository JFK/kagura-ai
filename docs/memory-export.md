# Memory Export/Import Guide

**Kagura AI v4.0.0** - Universal AI Memory Platform

This guide explains how to export and import your Kagura memory data for backup, migration, or GDPR compliance.

---

## 📋 Overview

Kagura provides export/import functionality in JSONL (JSON Lines) format:

- **Human-readable** - Plain text JSON, one record per line
- **Portable** - Works across different machines and versions
- **Comprehensive** - Exports memories, graph data, and metadata
- **GDPR-compliant** - Complete data export for user requests

---

## 🚀 Quick Start

### Export All Data

```bash
# Export everything to ./backup directory
kagura memory export --output ./backup

# Output:
# ✓ Export completed successfully!
#
# Exported:
#   • Memories: 150
#   • Graph nodes: 87
#   • Graph edges: 42
#
# Files created:
#   • memories.jsonl
#   • graph.jsonl
#   • metadata.json
```

### Import from Backup

```bash
# Import from backup directory
kagura memory import --input ./backup

# Output:
# ✓ Import completed successfully!
#
# Imported:
#   • Memories: 150
#   • Graph nodes: 87
#   • Graph edges: 42
```

---

## 🔧 Export Options

### Selective Export

```bash
# Export only persistent memory (skip working memory)
kagura memory export --output ./backup --no-working

# Export only working memory (skip persistent)
kagura memory export --output ./backup --no-persistent

# Export without graph data
kagura memory export --output ./backup --no-graph
```

### User-Specific Export

```bash
# Export for specific user
kagura memory export --output ./alice-backup --user-id user_alice

# Export for specific agent
kagura memory export --output ./backup --agent-name my_agent
```

---

## 📥 Import Options

### Clear Existing Data

```bash
# Clear existing data before import (⚠️ DESTRUCTIVE)
kagura memory import --input ./backup --clear

# WARNING: This will delete all existing memory data!
```

### Import for Specific User

```bash
# Import into specific user's memory
kagura memory import --input ./backup --user-id user_alice --agent-name global
```

---

## 📁 Export Format

### Directory Structure

```
backup/
├── memories.jsonl       # All memory records
├── graph.jsonl          # Graph nodes and edges (if enabled)
└── metadata.json        # Export metadata
```

### JSONL Format

#### Memory Records (`memories.jsonl`)

```jsonl
{"type":"memory","scope":"working","key":"user_preference","value":"Python backend","user_id":"user_jfk","agent_name":"global","exported_at":"2025-10-27T10:30:00Z"}
{"type":"memory","scope":"persistent","key":"api_key","value":"***","user_id":"user_jfk","agent_name":"global","created_at":"2025-10-26T12:00:00Z","updated_at":"2025-10-27T10:00:00Z","metadata":{"tags":["config"],"importance":0.9},"exported_at":"2025-10-27T10:30:00Z"}
```

**Fields**:
- `type`: Always "memory"
- `scope`: "working" or "persistent"
- `key`: Memory key
- `value`: Stored value (any JSON type)
- `user_id`: User identifier
- `agent_name`: Agent name
- `created_at`, `updated_at`: Timestamps (persistent only)
- `metadata`: Optional metadata dict
- `exported_at`: Export timestamp

#### Graph Records (`graph.jsonl`)

```jsonl
{"type":"node","id":"mem_001","node_type":"memory","data":{"key":"user_preference"},"exported_at":"2025-10-27T10:30:00Z"}
{"type":"edge","src":"mem_001","dst":"mem_002","rel_type":"related_to","weight":0.8,"data":{},"exported_at":"2025-10-27T10:30:00Z"}
```

**Node Fields**:
- `type`: "node"
- `id`: Node identifier
- `node_type`: Node type (e.g., "memory", "user", "topic")
- `data`: Node attributes

**Edge Fields**:
- `type`: "edge"
- `src`: Source node ID
- `dst`: Destination node ID
- `rel_type`: Relationship type
- `weight`: Edge weight (0.0-1.0)

#### Metadata (`metadata.json`)

```json
{
  "exported_at": "2025-10-27T10:30:00Z",
  "user_id": "user_jfk",
  "agent_name": "global",
  "stats": {
    "memories": 150,
    "graph_nodes": 87,
    "graph_edges": 42
  },
  "format_version": "1.0"
}
```

---

## 🔄 Use Cases

### 1. Backup Before Major Changes

```bash
# Before upgrading Kagura
kagura memory export --output ./backup-before-upgrade

# Upgrade Kagura
pip install --upgrade kagura-ai

# If something goes wrong, restore
kagura memory import --input ./backup-before-upgrade --clear
```

### 2. Migration to New Machine

```bash
# On old machine
kagura memory export --output ./kagura-backup

# Copy ./kagura-backup to new machine

# On new machine
pip install kagura-ai
kagura memory import --input ./kagura-backup
```

### 3. GDPR Data Export

```bash
# Export all user data for GDPR request
kagura memory export --output ./gdpr-export --user-id user_alice

# Provide ./gdpr-export to user
```

### 4. Selective Backup

```bash
# Daily backup (working memory only)
kagura memory export --output ./daily-backup-$(date +%Y%m%d) --no-persistent

# Weekly full backup
kagura memory export --output ./weekly-backup-$(date +%Y%m%d)
```

---

## ⚠️ Important Notes

### Data Loss Prevention

- **Always backup before** using `--clear` flag
- **Test import** on a copy first
- **Verify roundtrip** with critical data

### Large Exports

For large memory databases (>10,000 records):
- Export may take several minutes
- JSONL files can be large (100MB+)
- Consider selective exports by user or scope

### Version Compatibility

- Format version 1.0 (current)
- Future versions will maintain backward compatibility
- Metadata includes `format_version` for validation

---

## 🧪 Testing Export/Import

### Verify Export

```bash
# Export
kagura memory export --output ./test-export

# Check files exist
ls -lh ./test-export/

# Expected:
# memories.jsonl
# graph.jsonl
# metadata.json
```

### Verify Roundtrip

```bash
# Store test data
echo 'manager.working.set("test", "value")' | python -c "..."

# Export
kagura memory export --output ./roundtrip-test

# Clear (⚠️ for testing only)
rm ~/.kagura/memory.db

# Import
kagura memory import --input ./roundtrip-test

# Verify data restored
# (check with kagura mcp tools)
```

---

## 📚 API Reference

### Python API

```python
from kagura.core.memory import MemoryManager
from kagura.core.memory.export import MemoryExporter, MemoryImporter

# Create manager
manager = MemoryManager(user_id="user_jfk", agent_name="global")

# Export
exporter = MemoryExporter(manager)
stats = await exporter.export_all(
    output_dir="./backup",
    include_working=True,
    include_persistent=True,
    include_graph=True,
)
print(f"Exported {stats['memories']} memories")

# Import
importer = MemoryImporter(manager)
stats = await importer.import_all(
    input_dir="./backup",
    clear_existing=False,  # Merge with existing data
)
print(f"Imported {stats['memories']} memories")
```

---

## 🔗 Related Documentation

- [API Reference](./api-reference.md)
- [Memory Management](./memory-management.md)
- [Graph Memory](./graph-memory.md)

---

**Last Updated**: 2025-10-27
**Version**: 4.0.0
