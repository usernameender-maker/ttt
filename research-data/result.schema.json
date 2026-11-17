{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "title": "TVE-1 result log schema",
  "type": "object",
  "required": [
    "scenario",
    "seed",
    "backend",
    "timestamp_utc",
    "mean_ms",
    "gflops_per_sec",
    "validation_passed"
  ],
  "properties": {
    "scenario": { "type": "string" },
    "seed": { "type": "integer" },
    "backend": { "type": "string" },
    "timestamp_utc": { "type": "string" },
    "mean_ms": { "type": "number" },
    "gflops_per_sec": { "type": "number" },
    "validation_passed": { "type": "boolean" },
    "max_abs_error": { "type": ["number", "null"] },
    "thread_environment": { "type": "object" }
  },
  "additionalProperties": true
}
