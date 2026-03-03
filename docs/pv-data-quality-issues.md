# PromptVault Data Quality Issues

**Generated**: 2026-03-04 05:11 CST

This document records specific data quality issues found during the quality check.

---

## 1. Duplicate Entries (Removed)

**Total Duplicates Removed**: 84

### Sample Duplicates
| Original ID | Duplicate ID | Issue |
|-------------|--------------|-------|
| civitai-123026336 | civitai-123026363 | Exact duplicate (same prompt + images) |
| civitai-123026336 | civitai-123026366 | Exact duplicate (same prompt + images) |
| civitai-123029711 | civitai-123029713 | Exact duplicate (same prompt + images) |
| 20260301_civ_228 | 58e9b6aeaba1 | Duplicate from different scrape runs |
| 20260301_civ_236 | f51fea0f7c31 | Duplicate from different scrape runs |

**Root Cause**: Civitai API returns same images with different IDs, scraper doesn't detect cross-run duplicates effectively.

---

## 2. Missing/Null IDs

**Total Affected**: 162 prompts (7.9%)

### Sample Cases
- `null` (1 entry) - ID field is literally null
- Multiple entries with `id: null` in JSON

**Impact**: Critical - prevents effective deduplication and tracking

**Recommendation**: Fix scraper to always generate unique IDs (timestamp + hash)

---

## 3. Empty Prompts

**Total Affected**: 95 prompts (4.6%)

### Sample Cases
| ID | Tool | Issue |
|----|------|-------|
| 42e48d7a80c1 | Unknown | Completely empty prompt |
| 20260304_civ_newest_123068342 | Stable Diffusion | Empty prompt |

**Root Cause**: Scraper fails to extract prompt text from certain page structures

**Recommendation**: Add validation to skip entries with empty prompts

---

## 4. Missing Images

**Total Affected**: 135 prompts (6.6%)

### Sample Cases
| ID | Tool | Prompt Preview |
|----|------|----------------|
| civitai-123029468 | Stable Diffusion | "1girl, japanese clothes, kimono..." |
| ph-3ac90abf045c | Stable Diffusion | "an image of a person with flowing..." |

**Root Cause**: Image URL extraction fails for certain sources (especially PromptHero)

**Recommendation**: Improve image URL parsing, add fallback strategies

---

## 5. Unknown Tool Classification

**Total Affected**: 96 prompts (4.7%, down from 157)

### Sample Unknown Prompts
| ID | Source | Prompt Preview | Likely Tool |
|----|--------|----------------|-------------|
| 58e9b6aeaba1 | civitai | "zidiusArt, black cat is looking..." | Stable Diffusion |
| f51fea0f7c31 | civitai | "Epic foreground-to-background..." | Stable Diffusion |
| 004e0f2ce5fb | civitai | "an infographic on how to pick..." | Stable Diffusion |
| 666880354572 | civitai | "remove the two little holes..." | Unknown (editing prompt) |

**Fixed**: 23 prompts reclassified using pattern matching
**Remaining**: 96 prompts (edge cases, new tools, or editing prompts)

**Recommendation**: 
- Add more inference patterns
- Consider manual review for top 20 Unknown prompts
- Accept 4-5% Unknown as normal

---

## 6. Quality Issues from Random Sample (50 prompts)

### Issues Found: 16/50 (32%)

| Index | ID | Problems | Tool | Prompt Preview |
|-------|----|---------|----|----------------|
| 2 | 42e48d7a80c1 | truncated/too_short, unknown_tool | Unknown | "" |
| 3 | null | missing_id | Stable Diffusion | "The palette is dominated by dark tones..." |
| 4 | civitai-123029468 | no_images | Stable Diffusion | "1girl, japanese clothes, kimono..." |
| 7 | ph-3ac90abf045c | no_images | Stable Diffusion | "an image of a person with flowing..." |
| 18 | 20260304_civ_newest_123068342 | truncated/too_short | Stable Diffusion | "" |
| 22 | 53d7d529a62d | unknown_tool | Unknown | "ANIRLEQ, blurry, chromatic aberration..." |
| 23 | null | missing_id | Stable Diffusion | "masterpiece, best quality, 1girl..." |
| 26 | d54ce021c34a | unknown_tool | Unknown | "The Scooby gang as paranormal..." |
| 33 | civitai_122133697 | unknown_tool | Unknown | "<lora:reij-detaILer:0.74>..." |
| 34 | ad2968f79d2e | unknown_tool | Unknown | "Ultra-cinematic dark-fantasy..." |

---

## 7. Scraper Performance Issues

### High Deduplication Rates
Some scrape runs had extremely high dedup rates:
- 97.8% dedup (only 2 new prompts from 90+ scraped)
- 97.2% dedup (only 2 new prompts)
- 95.5% dedup (only 3 new prompts)

**Root Cause**: Scraping same content repeatedly without time-based filtering

**Recommendation**: 
- Add `since` parameter to only scrape images from last 6 hours
- Rotate between different sorting strategies
- Reduce scraping frequency when dedup rate > 90%

---

## 8. Data Integrity Issues

### Inconsistent Date Formats
- `collected_at`: "2026-02-27T16:04:00"
- `createdAt`: "2026-03-04T02:44:43.949825"
- `created_at`: "2026-02-27"

**Recommendation**: Standardize to ISO 8601 format with timezone

### Inconsistent Field Names
- `source_url` vs `source`
- `collected_at` vs `createdAt`
- `negativePrompt` vs `negative_prompt`

**Recommendation**: Standardize field naming convention

---

## 9. Action Items

### Critical (Fix Immediately)
- [ ] Fix null ID generation in scraper
- [ ] Add validation to skip empty prompts
- [ ] Improve image URL extraction

### High Priority
- [ ] Implement time-based filtering (last 6 hours)
- [ ] Add scraper rotation strategy
- [ ] Standardize date formats

### Medium Priority
- [ ] Review top 20 Unknown tool prompts manually
- [ ] Add more tool inference patterns
- [ ] Standardize field naming

### Low Priority
- [ ] Add data validation tests
- [ ] Implement quality scoring
- [ ] Add metadata enrichment

---

**Status**: 84 duplicates removed, 23 Unknown tools fixed, quality report generated
