#!/usr/bin/env node
const fs = require('fs');

/**
 * Simple wrapper to integrate Deepnest engine.
 * Reads JSON from stdin:
 *   { pieces: [ { polygon: [ [x,y], ... ] }, ... ], width, height, spacing, rotations }
 * Writes to stdout JSON:
 *   { placements: [ { polygon: [ [x,y],... ], x, y, rotationAngle }, ... ] }
 *
 * TODO: replace stub logic with actual deepnest API calls
 */
(async function main() {
  try {
    const input = JSON.parse(await new Promise((res, rej) => {
      let data = '';
      process.stdin.setEncoding('utf8');
      process.stdin.on('data', chunk => data += chunk);
      process.stdin.on('end', () => res(data));
      process.stdin.on('error', err => rej(err));
    }));
    const { pieces = [], width, height, spacing, rotations } = input;
    // Invoke Deepnest engine via its headless CLI (requires prior `npm install && npm run build` in deepnest/)
    const { spawnSync } = require('child_process');
    const deepnestDir = require('path').resolve(__dirname, '..', '..', 'deepnest');
    // Electron-based headless entrypoint must be implemented in deepnest to accept JSON via stdin and output placements
    // Invoke local Electron binary in headless mode
    const electronBin = require('path').join(deepnestDir, 'node_modules', '.bin', 'electron');
    const proc = spawnSync(
      electronBin, ['.', '--headless'],
      { cwd: deepnestDir, input: JSON.stringify(input), encoding: 'utf8' }
    );
    if (proc.error) throw proc.error;
    if (proc.status !== 0) {
      console.error(proc.stderr);
      process.exit(proc.status);
    }
    let result;
    try {
      result = JSON.parse(proc.stdout);
    } catch (e) {
      throw new Error(`Invalid JSON from Deepnest engine: ${e.message}`);
    }
    process.stdout.write(JSON.stringify({ placements: result.placements || [] }));
  } catch (err) {
    console.error(err && err.stack || err);
    process.exit(1);
  }
})();
