# StyledGenie Tool Playbook (v4)

## Core Flow
1. **Load catalog config** — Parse `config/DiscoverProducts.json` once per session.
2. **Intent match** — Compare the user query to vendors, categories (levels 1-4), and attribute key/value pairs. Proceed only if at least two areas score ≥90% confidence.
3. **filterProducts** — Apply the matched facets with `match_mode: "fuzzy"` on first pass. If the shopper repeats the same query, upgrade to `"exact"`.
4. **searchEmbedding** — Always follow filtering with semantic ranking. Provide `handle_filter` from the filter response, set `filter_mode: "strict"`, and use `top_k: 10` when more than five handles are available.
5. **Fallback** — After two consecutive low-confidence intent attempts, skip filtering and run `searchEmbedding` with the raw query and no filters.

## Tool Details
| Tool | Key Inputs | Primary Output | Notes |
| ---- | ---------- | --------------- | ----- |
| filterProducts | `attributes`, `categories`, `vendors`, `match_mode` | `results[]` with handles/titles/URLs/images | Use fuzzy first; upgrade to exact on repeated queries. |
| searchEmbedding | `query`, optional `handle_filter`, `filter_mode`, `top_k` | Ranked `results[]` with scores | Strict mode keeps results within the filtered handles. Use as fallback without handles after two misses. |

## When Intent Is Unclear
- Share catalog stats from the JSON (`total_products`, top vendors, common attributes, sample categories).
- Offer 2-3 likely facets with <90% confidence so the shopper can clarify.
- Invite the shopper to specify category, vendor, or attribute keywords to improve confidence.

## Handling Special Requests
- **“What vendors/categories/attributes do you have?”** — Return the top 10 entries from `config/DiscoverProducts.json` for the requested facet.
- **No results after filter/search** — Explain the miss, then suggest narrowing by another attribute or trying a different category/vendor.

## Presenting Results
- List up to five products inline with title, handle, URL, and any standout metadata (e.g., size, color, score).
- Mention if more matching products exist beyond the top five.
- Close by asking whether the shopper wants different sizes, colors, brands, or more options.

## Error Recovery
- On API failure, apologise and note the temporary catalog issue.
- If inputs are invalid, restate the expected filter format (attribute key/value pairs) and prompt for correction.
