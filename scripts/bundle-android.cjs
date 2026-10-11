const fs = require('node:fs');
const path = require('node:path');
const { spawnSync } = require('node:child_process');
const output = path.resolve('build/bundle');
fs.mkdirSync(output, { recursive: true });
const result = spawnSync(
  process.execPath,
  [
    path.resolve('node_modules/react-native/cli.js'),
    'bundle',
    '--platform',
    'android',
    '--dev',
    'false',
    '--entry-file',
    'index.js',
    '--bundle-output',
    path.join(output, 'index.android.bundle'),
    '--assets-dest',
    path.join(output, 'assets'),
    '--max-workers',
    '2',
  ],
  { stdio: 'inherit' },
);
if (result.error) {
  throw result.error;
}
process.exit(result.status ?? 1);
