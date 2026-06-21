## Semantic Duplicate Function Discovery

Use this workflow when a refactor round needs to find functions that do the same job with different names or implementations. It is discovery input for `gomtm-refactor`, not automatic permission to consolidate code.

## When To Use

- LLM or multi-author code has accumulated repeated helpers, validators, formatters, path logic, or API shaping code.
- `jscpd` or syntax-level duplicate checks have already handled copy/paste duplication, but semantic overlap is still suspected.
- A broad refactor round needs an inventory before choosing a safe duplicate-implementation batch.

Avoid this workflow for a tiny local edit where direct source reading is faster and clearer.

## Workflow

Run commands from the skill directory unless the paths are made absolute.

1. Extract a function catalog:

   ```bash
   scripts/duplicate-functions/extract-functions.sh <repo>/src -o catalog.json
   ```

2. Categorize the catalog with `references/semantic-duplicate-functions-categorize-prompt.md`. Use a low-cost model for classification, save the full JSON array to `categorized.json`, and verify the entry count still matches `catalog.json`.

3. Split categories:

   ```bash
   scripts/duplicate-functions/prepare-category-analysis.sh categorized.json categories
   ```

4. Analyze each category with at least 3 functions using `references/semantic-duplicate-functions-find-prompt.md`. Save each result to `duplicates/<category>.json`.

5. Generate the report:

   ```bash
   scripts/duplicate-functions/generate-report.sh duplicates duplicates-report.md
   ```

6. Treat the report as a candidate inventory. Before changing source code, confirm real consumers, ownership boundaries, behavior differences, and the smallest trustworthy verification path.

## High-Risk Duplicate Areas

- `utils/`, `helpers/`, `lib/`
- validation and type guards
- error creation, wrapping, and formatting
- path parsing, joining, and normalization
- string/date formatting
- API response shaping
- provider/tool implementations with repeated request mapping

## Consolidation Rules

- Consolidate only when input-output semantics and edge cases are understood.
- Prefer the implementation with clearer ownership, better tests, and fewer special cases.
- Keep behavior-focused verification around the surviving path before deleting the duplicate.
- If two functions differ in null handling, error shape, authorization, side effects, or logging semantics, mark the finding as `INVESTIGATE` and keep it out of the current batch.
- Do not consolidate test helpers by default; repeated test setup can be clearer than a shared fixture that hides behavior.

## Common Failures

- Running duplicate detection on the whole repo without categorization, producing noisy comparisons.
- Treating LOW or MEDIUM confidence LLM findings as proof.
- Inventing a new generic helper when one direct canonical owner would be simpler.
- Deleting a duplicate before updating all real call sites and rerunning focused verification.
