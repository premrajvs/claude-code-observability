# Splunk Query Guide for Claude Code Observatory

This guide provides example Splunk queries (SPL) for analyzing Claude Code usage telemetry sent via OpenTelemetry.

## Index and Sourcetype

All data is stored in:
- **Index:** `claude_observatory`
- **Sourcetype:** `otel:traces`

## Understanding the Data Structure

The observatory sends three types of spans (OpenInference span kinds):

1. **LLM Spans** - Individual AI interactions with token usage
2. **CHAIN Spans** - Session summaries with aggregated metrics
3. **EVALUATOR Spans** - Quality evaluations and hallucination detections

## Basic Queries

### View All Recent Telemetry

```spl
index=claude_observatory sourcetype="otel:traces"
| head 100
| table _time, name, openinference.span.kind, project.name, session.id
```

### Count Events by Type

```spl
index=claude_observatory sourcetype="otel:traces"
| stats count by openinference.span.kind
```

---

## Token Usage Analysis

### Total Tokens by Project (Last 24 Hours)

```spl
index=claude_observatory sourcetype="otel:traces" openinference.span.kind="LLM"
| eval tokens=tonumber('llm.token_count.total')
| eval project=coalesce('otel.project', 'project.name')
| stats sum(tokens) as total_tokens by project
| sort -total_tokens
```

### Token Usage Trend by Project (Hourly)

```spl
index=claude_observatory sourcetype="otel:traces" openinference.span.kind="LLM"
| eval tokens=tonumber('llm.token_count.total')
| eval project=coalesce('otel.project', 'project.name')
| timechart span=1h sum(tokens) by project
```

### Token Breakdown by Type

```spl
index=claude_observatory sourcetype="otel:traces" openinference.span.kind="LLM"
| eval input_tokens=tonumber('llm.token_count.prompt')
| eval output_tokens=tonumber('llm.token_count.completion')
| eval cache_write=tonumber('llm.token_count.prompt_details.cache_write')
| eval cache_read=tonumber('llm.token_count.prompt_details.cache_read')
| stats sum(input_tokens) as "Input Tokens",
        sum(output_tokens) as "Output Tokens",
        sum(cache_write) as "Cache Write",
        sum(cache_read) as "Cache Read"
```

---

## Cost Analysis

### Total Cost by Project

```spl
index=claude_observatory sourcetype="otel:traces" openinference.span.kind="LLM"
| eval cost=tonumber('llm.cost.total')
| eval project=coalesce('otel.project', 'project.name')
| stats sum(cost) as total_cost by project
| eval total_cost=round(total_cost, 2)
| sort -total_cost
```

### Daily Cost Trend

```spl
index=claude_observatory sourcetype="otel:traces" openinference.span.kind="LLM"
| eval cost=tonumber('llm.cost.total')
| timechart span=1d sum(cost) as daily_cost
| eval daily_cost=round(daily_cost, 2)
```

### Cost by Model

```spl
index=claude_observatory sourcetype="otel:traces" openinference.span.kind="LLM"
| eval cost=tonumber('llm.cost.total')
| eval model=coalesce('otel.model', 'llm.model_name')
| stats sum(cost) as total_cost, count as num_calls by model
| eval avg_cost_per_call=round(total_cost/num_calls, 4)
| eval total_cost=round(total_cost, 2)
| sort -total_cost
```

### Cost Per Session

```spl
index=claude_observatory sourcetype="otel:traces" openinference.span.kind="LLM"
| eval cost=tonumber('llm.cost.total')
| eval session_id=coalesce('otel.session_id', 'session.id')
| eval session_name=coalesce('otel.session_name', 'session.name')
| eval project=coalesce('otel.project', 'project.name')
| stats sum(cost) as session_cost by session_id, session_name, project
| eval session_cost=round(session_cost, 4)
| sort -session_cost
| head 20
```

---

## Session Analysis

### Session Summary Dashboard

```spl
index=claude_observatory sourcetype="otel:traces" openinference.span.kind="CHAIN"
| eval project='project.name'
| eval messages=tonumber('session.message_count')
| eval tokens=tonumber('session.total_tokens')
| eval cost=tonumber('session.total_cost')
| eval quality=tonumber('session.quality_score')
| eval errors=tonumber('session.error_count')
| eval duration=tonumber('session.duration_minutes')
| table _time, project, session.id, session.name, messages, tokens, cost, quality, errors, duration
| sort -_time
```

### Average Session Metrics by Project

```spl
index=claude_observatory sourcetype="otel:traces" openinference.span.kind="CHAIN"
| eval project='project.name'
| eval messages=tonumber('session.message_count')
| eval tokens=tonumber('session.total_tokens')
| eval cost=tonumber('session.total_cost')
| eval quality=tonumber('session.quality_score')
| eval duration=tonumber('session.duration_minutes')
| stats avg(messages) as avg_messages,
        avg(tokens) as avg_tokens,
        avg(cost) as avg_cost,
        avg(quality) as avg_quality,
        avg(duration) as avg_duration,
        count as num_sessions
  by project
| eval avg_cost=round(avg_cost, 4)
| eval avg_quality=round(avg_quality, 2)
| eval avg_duration=round(avg_duration, 1)
```

### Long-Running Sessions

```spl
index=claude_observatory sourcetype="otel:traces" openinference.span.kind="CHAIN"
| eval duration=tonumber('session.duration_minutes')
| where duration > 30
| eval project='project.name'
| eval cost=tonumber('session.total_cost')
| table _time, project, session.name, duration, cost, session.message_count
| sort -duration
```

---

## Hallucination & Quality Analysis

### Hallucination Events by Category

```spl
index=claude_observatory sourcetype="otel:traces" openinference.span.kind="EVALUATOR"
| eval category='evaluation.category'
| eval confidence=tonumber('evaluation.confidence')
| stats count as event_count, avg(confidence) as avg_confidence by category
| eval avg_confidence=round(avg_confidence*100, 1) . "%"
| sort -event_count
```

### Hallucinations by Project

```spl
index=claude_observatory sourcetype="otel:traces" openinference.span.kind="EVALUATOR"
| eval project='project.name'
| eval category='evaluation.category'
| stats count by project, category
| sort -count
```

### Projects with High Error Rates

```spl
index=claude_observatory sourcetype="otel:traces" openinference.span.kind="CHAIN"
| eval project='project.name'
| eval errors=tonumber('session.error_count')
| eval messages=tonumber('session.message_count')
| eval error_rate=errors/messages
| where error_rate > 0.2
| table project, session.name, messages, errors, error_rate
| sort -error_rate
```

### Quality Score Trend

```spl
index=claude_observatory sourcetype="otel:traces" openinference.span.kind="CHAIN"
| eval quality=tonumber('session.quality_score')
| timechart span=1d avg(quality) as avg_quality
| eval avg_quality=round(avg_quality, 2)
```

---

## Drill-Down Queries

### Project → Sessions → Conversations

**Step 1: View Projects**
```spl
index=claude_observatory sourcetype="otel:traces" openinference.span.kind="LLM"
| eval project=coalesce('otel.project', 'project.name')
| stats count as interactions,
        sum(tonumber('llm.token_count.total')) as total_tokens,
        sum(tonumber('llm.cost.total')) as total_cost
  by project
| sort -total_cost
```

**Step 2: View Sessions for a Project** (replace `YOUR_PROJECT` with actual project name)
```spl
index=claude_observatory sourcetype="otel:traces" openinference.span.kind="LLM" project.name="YOUR_PROJECT"
| eval session_id=coalesce('otel.session_id', 'session.id')
| eval session_name=coalesce('otel.session_name', 'session.name')
| stats count as interactions,
        sum(tonumber('llm.token_count.total')) as total_tokens,
        sum(tonumber('llm.cost.total')) as total_cost
  by session_id, session_name
| sort -total_cost
```

**Step 3: View Conversations in a Session** (replace `YOUR_SESSION_ID`)
```spl
index=claude_observatory sourcetype="otel:traces" openinference.span.kind="LLM" session.id="YOUR_SESSION_ID"
| eval tokens=tonumber('llm.token_count.total')
| eval cost=tonumber('llm.cost.total')
| eval message_index=tonumber('message.index')
| table _time, message_index, llm.model_name, tokens, cost
| sort +message_index
```

---

## Real-Time Monitoring

### Live Token Usage (Last 5 Minutes)

```spl
index=claude_observatory sourcetype="otel:traces" openinference.span.kind="LLM" earliest=-5m
| eval project=coalesce('otel.project', 'project.name')
| eval tokens=tonumber('llm.token_count.total')
| stats sum(tokens) as total_tokens by project
| sort -total_tokens
```

### Active Sessions (Last Hour)

```spl
index=claude_observatory sourcetype="otel:traces" openinference.span.kind="LLM" earliest=-1h
| eval session_id=coalesce('otel.session_id', 'session.id')
| eval session_name=coalesce('otel.session_name', 'session.name')
| eval project=coalesce('otel.project', 'project.name')
| stats latest(_time) as last_activity,
        count as interactions
  by session_id, session_name, project
| eval last_activity=strftime(last_activity, "%H:%M:%S")
| sort -interactions
```

---

## Advanced Analytics

### Token Efficiency (Cache Hit Rate)

```spl
index=claude_observatory sourcetype="otel:traces" openinference.span.kind="LLM"
| eval cache_read=tonumber('llm.token_count.prompt_details.cache_read')
| eval cache_write=tonumber('llm.token_count.prompt_details.cache_write')
| eval total_prompt=tonumber('llm.token_count.prompt')
| eval project=coalesce('otel.project', 'project.name')
| stats sum(cache_read) as total_cache_read,
        sum(cache_write) as total_cache_write,
        sum(total_prompt) as total_prompt_tokens
  by project
| eval cache_hit_rate=round((total_cache_read/(total_prompt_tokens+total_cache_read))*100, 1)
| table project, total_cache_read, total_cache_write, cache_hit_rate
| sort -cache_hit_rate
```

### Peak Usage Hours

```spl
index=claude_observatory sourcetype="otel:traces" openinference.span.kind="LLM"
| eval hour=strftime(_time, "%H")
| eval tokens=tonumber('llm.token_count.total')
| chart sum(tokens) as total_tokens by hour
| sort +hour
```

### Model Distribution

```spl
index=claude_observatory sourcetype="otel:traces" openinference.span.kind="LLM"
| eval model=coalesce('otel.model', 'llm.model_name')
| stats count as usage_count by model
| sort -usage_count
```

---

## Alerting Use Cases

### High Cost Alert (>$1 per session)

```spl
index=claude_observatory sourcetype="otel:traces" openinference.span.kind="CHAIN"
| eval cost=tonumber('session.total_cost')
| where cost > 1.0
| eval project='project.name'
| table _time, project, session.name, cost
| sort -cost
```

### Low Quality Score Alert (<0.7)

```spl
index=claude_observatory sourcetype="otel:traces" openinference.span.kind="CHAIN"
| eval quality=tonumber('session.quality_score')
| where quality < 0.7
| eval project='project.name'
| table _time, project, session.name, quality, session.error_count
| sort +quality
```

### High Error Rate Alert (>3 errors per session)

```spl
index=claude_observatory sourcetype="otel:traces" openinference.span.kind="CHAIN"
| eval errors=tonumber('session.error_count')
| where errors > 3
| eval project='project.name'
| table _time, project, session.name, errors, session.message_count
| sort -errors
```

---

## Dashboard Recommendations

### Executive Dashboard
- Daily cost trend (line chart)
- Total tokens by project (bar chart)
- Top 5 most expensive sessions (table)
- Average quality score (single value)

### Operations Dashboard
- Active sessions (real-time table)
- Token usage per hour (timechart)
- Cache hit rate by project (bar chart)
- Error events by category (pie chart)

### Quality Dashboard
- Hallucination events by category (bar chart)
- Quality score trend (line chart)
- Projects with high error rates (table)
- Average session quality by project (bar chart)

---

## Tips for Better Queries

1. **Use field aliases** for frequently used fields:
   ```spl
   | eval project=coalesce('otel.project', 'project.name')
   ```

2. **Convert to numbers** before aggregation:
   ```spl
   | eval tokens=tonumber('llm.token_count.total')
   ```

3. **Round cost values** for readability:
   ```spl
   | eval cost=round(cost, 2)
   ```

4. **Filter by time range** for better performance:
   ```spl
   earliest=-24h latest=now
   ```

5. **Use stats over transaction** for better performance with large datasets.

---

## Troubleshooting

### No Data Showing Up?

1. Check index and sourcetype:
   ```spl
   | metadata type=sourcetypes index=claude_observatory
   ```

2. Verify HEC token is working:
   ```spl
   index=_internal source=*splunkd.log* HEC
   ```

3. Check OTel Collector logs for connection issues.

### Field Names Not Matching?

Use this to discover available fields:
```spl
index=claude_observatory sourcetype="otel:traces"
| head 1
| transpose
```

---

## Next Steps

1. Create scheduled searches for daily/weekly reports
2. Set up alerts for cost/quality thresholds
3. Build dashboards for different stakeholders
4. Export data for long-term trend analysis