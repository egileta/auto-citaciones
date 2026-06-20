import { writeFileSync } from 'node:fs';

const key = process.env.INDEXNOW_KEY;
if (!key) {
  console.log('INDEXNOW_KEY not set, skipping key file generation.');
  process.exit(0);
}

if (!/^[A-Za-z0-9-]{8,128}$/.test(key)) {
  console.error('INDEXNOW_KEY has invalid format; refusing to write key file.');
  process.exit(1);
}

writeFileSync(`dist/${key}.txt`, key);
console.log(`Wrote dist/${key}.txt`);
