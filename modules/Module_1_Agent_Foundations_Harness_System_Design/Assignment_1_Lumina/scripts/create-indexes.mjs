#!/usr/bin/env node
/**
 * Create every index LUMINA needs, from scripts/indexes.json. PROVIDED — safe to re-run.
 *
 * MONGO-ONLY CONVENIENCE, not a gate. It is a helper for the taught MERN path; nothing in
 * the grader calls it. If you built on another store, create its indexes however that store
 * expects and make /health name it.
 *
 *   node scripts/create-indexes.mjs            # apply
 *   node scripts/create-indexes.mjs --status   # just show what exists
 *
 * A plain mongod (docker compose up mongo) has no Atlas Search: the three search indexes
 * will fail and this script says so and keeps going, because the regular and TTL indexes
 * still apply. Run with VECTOR_BACKEND=mongo-cosine-scan in that case, and make /health
 * say which backend is live so a grader knows what they are looking at.
 */
import { readFileSync } from 'node:fs';
import { dirname, join, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';
import { config } from 'dotenv';
import { MongoClient } from 'mongodb';

const HERE = dirname(fileURLToPath(import.meta.url));
config({ path: resolve(HERE, '..', '.env') });

const spec = JSON.parse(readFileSync(join(HERE, 'indexes.json'), 'utf8'));
const uri = process.env.MONGODB_URI;
const dbName = process.env.MONGODB_DB ?? 'lumina';
const statusOnly = process.argv.includes('--status');

if (!uri) {
  console.error('MONGODB_URI is not set. Copy .env.example to .env and fill it in.');
  process.exit(2);
}

const client = new MongoClient(uri, { serverSelectionTimeoutMS: 8000 });
let warnings = 0;

try {
  await client.connect();
  const db = client.db(dbName);
  console.log(`lumina indexes → ${dbName}\n`);

  if (statusOnly) {
    for (const name of Object.keys(spec.collections)) {
      const existing = await db.collection(name).indexes().catch(() => []);
      console.log(`${name}: ${existing.map((i) => i.name).join(', ') || '(none)'}`);
    }
    for (const si of spec.searchIndexes) {
      const list = await db.collection(si.collection).listSearchIndexes().toArray().catch(() => null);
      const found = list?.find((i) => i.name === si.name);
      console.log(
        `${si.collection}/${si.name}: ${found ? `${found.status ?? 'present'}${found.queryable ? ' (queryable)' : ''}` : 'MISSING'}`
      );
    }
    process.exit(0);
  }

  // ---- regular + TTL indexes -------------------------------------------------
  for (const [name, cfg] of Object.entries(spec.collections)) {
    // createCollection first so an index on an unseen collection does not race the app.
    await db.createCollection(name).catch(() => {});
    for (const idx of cfg.indexes ?? []) {
      const options = { ...(idx.options ?? {}) };
      const label = options.name ?? Object.entries(idx.keys).map(([k, v]) => `${k}_${v}`).join('_');
      try {
        await db.collection(name).createIndex(idx.keys, options);
        console.log(`  ✓ ${name}.${label}${options.expireAfterSeconds !== undefined ? ' (TTL)' : ''}`);
      } catch (err) {
        warnings++;
        console.log(`  ! ${name}.${label} — ${err.message}`);
      }
    }
  }

  // ---- Atlas Search / Vector Search indexes ---------------------------------
  console.log('');
  for (const si of spec.searchIndexes) {
    const coll = db.collection(si.collection);
    await db.createCollection(si.collection).catch(() => {});
    try {
      const existing = await coll.listSearchIndexes().toArray();
      if (existing.some((i) => i.name === si.name)) {
        await coll.updateSearchIndex(si.name, si.definition);
        console.log(`  ✓ ${si.collection}/${si.name} (${si.type}) updated`);
      } else {
        await coll.createSearchIndex({ name: si.name, type: si.type, definition: si.definition });
        console.log(`  ✓ ${si.collection}/${si.name} (${si.type}) created — building, usually < 1 min`);
      }
    } catch (err) {
      warnings++;
      console.log(`  ! ${si.collection}/${si.name} — ${err.message}`);
      console.log('    (no Atlas Search on this cluster? run with VECTOR_BACKEND=mongo-cosine-scan)');
    }
  }

  console.log(
    warnings
      ? `\ndone with ${warnings} warning(s). A search index reports "building" for a while; ` +
          'it is not queryable until listSearchIndexes says queryable: true.'
      : '\ndone. Search indexes build asynchronously — check with --status before you trust a recall number.'
  );
} finally {
  await client.close();
}
