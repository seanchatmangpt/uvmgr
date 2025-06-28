# Search Optimization Workflow

## Usage
`/project:search-optimize [query] [scope=all]`

## Purpose
Optimize search queries across uvmgr's advanced search system, leveraging AST parsing, dependency analysis, and semantic understanding.

## Search Strategies

### Phase 1: Query Analysis
1. **Parse Search Intent**
   - Natural language understanding
   - Identify search type (code/deps/files/semantic)
   - Extract key patterns

2. **Query Optimization**
   - Convert to optimal search syntax
   - Add relevant filters
   - Suggest alternative queries

### Phase 2: Multi-Strategy Execution
1. **AST-Based Code Search**
   ```bash
   uvmgr search code "[pattern]" --type function --complexity-min 3
   ```
   - Function/class definitions
   - Import analysis
   - Complexity metrics

2. **Dependency Analysis**
   ```bash
   uvmgr search deps "[package]" --show-usage --include-transitive
   ```
   - Package usage tracking
   - Vulnerability scanning
   - Unused dependency detection

3. **Semantic Search**
   ```bash
   uvmgr search semantic "[description]" --explain
   ```
   - AI-powered understanding
   - Documentation search
   - Similar pattern discovery

4. **File Search**
   ```bash
   uvmgr search files "[pattern]" --type py --size-max 10000
   ```
   - Path matching
   - Content filtering
   - Metadata queries

### Phase 3: Result Synthesis
1. **Deduplication**
   - Remove duplicate matches
   - Merge related results
   - Priority ranking

2. **Context Enhancement**
   - Add surrounding code
   - Include documentation
   - Show relationships

3. **Caching Strategy**
   - Cache frequent queries
   - Incremental updates
   - Smart invalidation

### Phase 4: Performance Analysis
1. **Query Metrics**
   - Execution time per strategy
   - Result relevance scoring
   - Cache hit rates

2. **Optimization Suggestions**
   - Index recommendations
   - Query refinements
   - Caching improvements

## Examples
```bash
# Optimize search for authentication code
/project:search-optimize "authentication middleware"

# Search across all uvmgr components
/project:search-optimize "telemetry" scope=all

# Focused dependency search
/project:search-optimize "security vulnerabilities" scope=deps
```

## Advanced Features
- **Parallel Execution**: Run multiple search strategies concurrently
- **Progressive Results**: Stream results as found
- **Learning Mode**: Improve query patterns over time
- **Export Formats**: JSON, CSV, Markdown reports

## Output
- Optimized query syntax
- Results from all strategies
- Performance metrics
- Caching statistics
- Improvement suggestions