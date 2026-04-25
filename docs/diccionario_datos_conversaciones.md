# Dataset: dataset_50k_anonymized

Customer support conversations between users and an AI assistant for a financial services platform.

## Overview

| Metric | Value |
|--------|-------|
| Rows (interactions) | 49,999 |
| Conversations | 24,119 |
| Unique users | 15,025 |
| Date range | January 2025 – November 2025 |
| Format | Parquet |

## Schema

| Column | Type | Description |
|--------|------|-------------|
| `input` | string | The user's message |
| `output` | string | Havi's response |
| `date` | string | Date of the interaction. Format is `YYYY-MM-DD` for most rows; some include a timestamp (`YYYY-MM-DD HH:MM:SS.ffffff`) |
| `conv_id` | string | Unique conversation identifier (UUID). Multiple rows can share the same `conv_id`, representing a multi-turn conversation |
| `user_id` | string | Anonymized user identifier in the format `USR-00001` through `USR-15025` |
| `channel_source` | string | Channel through which the conversation occurred. Values: `1` (text channel), `2` (voice channel) |

## Structure

Each row is a single interaction (one user message and one assistant response). Conversations may span multiple rows — group by `conv_id` to reconstruct full conversations.

### Interactions per conversation

| Interactions | Conversations |
|-------------|---------------|
| 1 | 15,000 |
| 3 | 4,987 |
| 4 | 2,329 |
| 5 | 979 |
| 6 | 438 |
| 7 | 189 |
| 8+ | 197 |

## Usage

```python
import pandas as pd

df = pd.read_parquet("dataset_50k_anonymized.parquet")

# Reconstruct a conversation
conv = df[df["conv_id"] == "some-conv-id"].sort_values("date")

# All conversations for a user
user_convs = df[df["user_id"] == "USR-00042"].groupby("conv_id")
```

## Notes

- Dates are anonymized and do not correspond to real dates. Chronological order within and across conversations per user is preserved.
- User IDs are anonymized. There is no mapping back to original identifiers.
- The dataset is in Spanish.
