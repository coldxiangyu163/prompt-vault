const fs = require('fs');
const crypto = require('crypto');

// Load existing prompts
const existingPrompts = JSON.parse(fs.readFileSync('data/prompts.json', 'utf8'));

// New prompts from scraping
const newPrompts = [
  STATE_CIVITAI_PROMPTS_PLACEHOLDER,
  STATE_SD_PROMPTS_PLACEHOLDER,
  STATE_FLUX_PROMPTS_PLACEHOLDER,
  STATE_MJ_PROMPTS_PLACEHOLDER
].flat();

console.log('Existing prompts:', existingPrompts.length);
console.log('New scraped prompts:', newPrompts.length);

// Deduplication logic
const existingHashes = new Set();
const existingUrls = new Set();

existingPrompts.forEach(p => {
  if (p.content) {
    const hash = crypto.createHash('md5').update(p.content.substring(0, 100)).digest('hex').substring(0, 12);
    existingHashes.add(hash);
  }
  if (p.images && p.images[0]) {
    existingUrls.add(p.images[0]);
  }
});

// Filter duplicates
const uniqueNew = newPrompts.filter(p => {
  const hash = crypto.createHash('md5').update(p.content.substring(0, 100)).digest('hex').substring(0, 12);
  const isDuplicateHash = existingHashes.has(hash);
  const isDuplicateUrl = p.images && p.images[0] && existingUrls.has(p.images[0]);
  return !isDuplicateHash && !isDuplicateUrl;
});

console.log('After deduplication:', uniqueNew.length);

// Infer tags and style
function inferTags(content) {
  const tags = [];
  const lower = content.toLowerCase();
  if (lower.includes('portrait') || lower.includes('face') || lower.includes('人像')) tags.push('portrait');
  if (lower.includes('landscape') || lower.includes('scenery') || lower.includes('风景')) tags.push('landscape');
  if (lower.includes('anime') || lower.includes('动漫')) tags.push('anime');
  if (lower.includes('3d') || lower.includes('render')) tags.push('3D');
  if (lower.includes('fantasy') || lower.includes('魔幻')) tags.push('fantasy');
  if (lower.includes('realistic') || lower.includes('photo')) tags.push('photorealistic');
  if (lower.includes('abstract') || lower.includes('抽象')) tags.push('abstract');
  if (lower.includes('minimalist') || lower.includes('极简')) tags.push('minimalist');
  if (lower.includes('cyberpunk') || lower.includes('赛博')) tags.push('cyberpunk');
  return tags.length > 0 ? tags : ['general'];
}

function inferStyle(content) {
  const lower = content.toLowerCase();
  if (lower.includes('anime') || lower.includes('动漫')) return 'anime';
  if (lower.includes('realistic') || lower.includes('photo')) return 'photorealistic';
  if (lower.includes('3d') || lower.includes('render')) return '3D';
  if (lower.includes('oil painting') || lower.includes('watercolor')) return 'painting';
  if (lower.includes('sketch') || lower.includes('line art')) return 'sketch';
  return 'digital-art';
}

// Add metadata
const timestamp = new Date().toISOString();
const enrichedNew = uniqueNew.map((p, idx) => ({
  id: `scrape_${Date.now()}_${idx}`,
  content: p.content,
  negativePrompt: p.negativePrompt || '',
  tool: p.tool,
  images: p.images,
  tags: inferTags(p.content),
  style: inferStyle(p.content),
  source: p.source,
  created_at: timestamp.split('T')[0],
  collected_at: timestamp
}));

// Merge and save
const merged = [...existingPrompts, ...enrichedNew];
fs.writeFileSync('data/prompts.json', JSON.stringify(merged, null, 2));

console.log('Final total:', merged.length);
console.log('New prompts added:', enrichedNew.length);
