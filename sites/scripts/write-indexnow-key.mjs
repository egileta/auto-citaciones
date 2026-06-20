import { writeFileSync } from 'node:fs';

const key = process.env.INDEXNOW_KEY;
if (!key) {
  console.log('INDEXNOW_KEY not set, skipping key file generation.');
  process.exit(0);
}

writeFileSync(`dist/${key}.txt`, key);
console.log(`Wrote dist/${key}.txt`);
