#!/usr/bin/env node
/**
 * PromptVault Auto Scraper
 * Uses Playwriter MCP to scrape Civitai + PromptHero via Arc browser
 * Run: node auto_scraper.js
 */

const fs = require('fs');
const path = require('path');
const crypto = require('crypto');
const { execSync } = require('child_process');

const DATA_FILE = path.join(__dirname, '../data/prompts.json');
const LOG_FILE = path.join(__dirname, 'output/scrape_log.json');

// Ensure output dir
const outputDir = path.join(__dirname, 'output');
if (!fs.existsSync(outputDir)) fs.mkdirSync(outputDir, { recursive: true });

function log(msg) {
  const ts = new Date().toISOString();
  console.log(`[${ts}] ${msg}`);
}

function contentHash(text) {
  const normalized = text.toLowerCase().replace(/\s+/g, ' ').trim();
  return crypto.createHash('md5').update(normalized).digest('hex').slice(0, 12);
}

function inferTags(prompt) {
  const p = prompt.toLowerCase();
  const tagMap = {
    portrait: ['portrait','face','headshot','woman','man','girl','boy'],
    landscape: ['landscape','scenery','mountain','ocean','forest','nature'],
    anime: ['anime','manga','waifu','chibi'],
    photorealistic: ['photorealistic','photo','realistic','raw photo','dslr'],
    fantasy: ['fantasy','dragon','magic','wizard','elf','sword'],
    'sci-fi': ['sci-fi','cyberpunk','futuristic','robot','mech','space'],
    architecture: ['architecture','building','interior','room','house'],
    character: ['character','oc','costume','armor'],
    cinematic: ['cinematic','film','movie','dramatic lighting'],
  };
  const tags = [];
  for (const [tag, kws] of Object.entries(tagMap)) {
    if (kws.some(k => p.includes(k))) tags.push(tag);
  }
  return tags.length ? tags : ['general'];
}

function inferStyle(prompt) {
  const p = prompt.toLowerCase();
  const styles = [
    ['anime', ['anime','manga','waifu']],
    ['photorealistic', ['photorealistic','raw photo','dslr','realistic']],
    ['digital-art', ['digital art','digital painting','illustration']],
    ['3d-render', ['3d render','blender','octane','unreal engine']],
    ['cinematic', ['cinematic','film still','movie']],
    ['concept-art', ['concept art','environment design']],
  ];
  for (const [style, kws] of styles) {
    if (kws.some(k => p.includes(k))) return style;
  }
  return 'mixed';
}

async function main() {
  log('🚀 Starting PromptVault auto-scraper...');
  
  // This script is meant to be called by nanobot with Playwriter context
  // The actual scraping logic is in the Playwriter execution
  log('⚠️  This script should be triggered by nanobot cron with Playwriter context');
  log('📝 Use: nanobot "run PromptVault scraper"');
  
  process.exit(0);
}

main().catch(err => {
  log(`❌ Error: ${err.message}`);
  process.exit(1);
});
