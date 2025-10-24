# Free-Text Search Builder (`dtpyfw.db.search_utils.free_search`)

## Overview

The `free_search` module provides functions to build WHERE conditions and ORDER BY clauses for full-text search using PostgreSQL's text search capabilities and similarity functions. It supports exact matching, fuzzy matching, and tokenized search.

## Module Location

```python
from dtpyfw.db.search_utils.free_search import free_search
```

**Note:** This module is primarily for internal use by `get_list()`.

## Functions

### `free_search`

```python
free_search(
    columns: Sequence[ColumnElement],
    query: str,
    threshold: float,
    exact: bool = True,
    tokenize: bool = True,
) -> Tuple[Sequence[ColumnElement], Sequence[UnaryExpression]]
```

Build WHERE conditions and ORDER BY clauses for a free-text search.

Creates SQL conditions and sorting expressions for searching across multiple columns using PostgreSQL full-text search and similarity functions.

**Parameters:**

- `columns` (Sequence[ColumnElement]): List of SQLAlchemy column expressions to search
- `query` (str): The search string entered by the user
- `threshold` (float): Minimum similarity score (0.0-1.0) for fuzzy matching
- `exact` (bool): If `True`, perform exact phrase matching; otherwise, fuzzy matching. Default: `True`
- `tokenize` (bool): If `True`, use PostgreSQL full-text search; otherwise, use simple string comparison or similarity. Default: `True`

**Returns:**

- `Tuple[conditions, order_by]`:
  - `conditions`: List of SQL boolean expressions for WHERE clause
  - `order_by`: List of SQL expressions for ORDER BY clause (relevance ranking)

**Example:**

```python
# This is called internally by get_list()
conditions, order_by = free_search(
    columns=[User.name, User.email, User.bio],
    query="john doe",
    threshold=0.1,
    exact=False,  # Fuzzy search
    tokenize=True  # Use full-text search
)

# Conditions are added to the query
query = query.where(*conditions).order_by(*order_by)
```

## Search Modes

### Exact + Tokenized (Default)

```python
conditions, order_by = free_search(
    columns=[User.name],
    query="john doe",
    threshold=0.1,
    exact=True,   # Exact phrase
    tokenize=True  # Full-text search
)
# Uses phraseto_tsquery for exact phrase matching
# Orders by ts_rank_cd for relevance
```

**Use Case:** Finding exact phrases like "John Doe" or "San Francisco"

### Fuzzy + Tokenized

```python
conditions, order_by = free_search(
    columns=[User.name],
    query="jon do",  # Misspelled
    threshold=0.1,
    exact=False,   # Allow fuzzy
    tokenize=True  # Full-text search
)
# Combines full-text search with similarity matching
# Orders by combined rank and similarity score
```

**Use Case:** Handling typos and partial matches

### Exact + Non-Tokenized

```python
conditions, order_by = free_search(
    columns=[User.email],
    query="example.com",
    threshold=0.1,
    exact=True,    # Exact match
    tokenize=False  # Simple string matching
)
# Uses lowercase string comparison
# No relevance ranking
```

**Use Case:** Searching structured data like emails or IDs

### Fuzzy + Non-Tokenized

```python
conditions, order_by = free_search(
    columns=[User.name],
    query="john",
    threshold=0.3,
    exact=False,   # Fuzzy
    tokenize=False  # Similarity only
)
# Uses PostgreSQL similarity() function
# Orders by similarity score
```

**Use Case:** Simple fuzzy matching without full-text overhead

## PostgreSQL Functions Used

### Full-Text Search Functions

- `to_tsvector()`: Converts text to searchable token vector
- `websearch_to_tsquery()`: Converts search query to token query
- `phraseto_tsquery()`: Creates phrase search query
- `ts_rank_cd()`: Calculates relevance ranking

### Similarity Functions

- `similarity()`: Calculates trigram similarity (0.0-1.0)
- `greatest()`: Selects maximum similarity across columns

## Configuration

### Language Setting

The function uses English for full-text search:

```python
tsv = func.to_tsvector(literal("english", type_=REGCONFIG), concatenated)
```

This can affect:
- Stop word filtering
- Stemming rules
- Token parsing

### Similarity Threshold

The `threshold` parameter (0.0-1.0) controls fuzzy matching sensitivity:

- `0.0`: Very permissive (matches almost anything)
- `0.1`: Default (good balance)
- `0.3`: Moderately strict
- `0.5`: Very strict (only close matches)

## Usage in get_list

This function is automatically called by `get_list()` when a `search` parameter is provided:

```python
result = get_list(
    current_query={"search": "john doe"},
    db=session,
    model=User,
    searchable_columns=[User.name, User.email],  # Triggers free_search()
    exact_search=False,  # Passed to free_search()
    search_tokenizer=True,  # Passed to free_search()
    search_similarity_threshold=0.1  # Passed to free_search()
)
```

## Performance Considerations

### Indexes Required

For optimal performance, create appropriate indexes:

```sql
-- GIN index for full-text search
CREATE INDEX idx_user_search ON users 
USING GIN (to_tsvector('english', name || ' ' || email));

-- GIN index for trigram similarity
CREATE INDEX idx_user_name_trgm ON users 
USING GIN (name gin_trgm_ops);
```

### Query Performance

- **Tokenized search**: Requires GIN indexes for good performance
- **Similarity search**: Benefits from trigram indexes
- **Combined mode**: Uses both index types
- **Multi-column**: Concatenates columns before searching

## Examples

### Basic Text Search

```python
# Search across name and bio
conditions, order_by = free_search(
    columns=[User.name, User.bio],
    query="software engineer",
    threshold=0.1,
    exact=False,
    tokenize=True
)
```

### Email Search

```python
# Exact email search
conditions, order_by = free_search(
    columns=[User.email],
    query="user@example.com",
    threshold=0.1,
    exact=True,
    tokenize=False  # Don't tokenize emails
)
```

### Multi-Column Fuzzy Search

```python
# Search across multiple text fields with typo tolerance
conditions, order_by = free_search(
    columns=[Product.name, Product.description, Product.category],
    query="lapto",  # Misspelled "laptop"
    threshold=0.2,  # More lenient for typos
    exact=False,
    tokenize=True
)
```

## Related Documentation

- [../search.md](../search.md) - Main search functionality
- [PostgreSQL Full-Text Search](https://www.postgresql.org/docs/current/textsearch.html)
- [PostgreSQL pg_trgm](https://www.postgresql.org/docs/current/pgtrgm.html)

## Notes

- Optimized specifically for PostgreSQL
- Requires `pg_trgm` extension for similarity search
- Full-text search uses English language rules by default
- Performance depends heavily on proper indexing
- This is an internal utility used by `get_list()`
