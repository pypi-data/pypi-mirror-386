#!/usr/bin/env node
/**
 * npx wrapper for the Python-based LOBBY CLI
 * Tries in order:
 *  1) existing `lobby` binary on PATH
 *  2) python3 -m lobby.cli
 *  3) python -m lobby.cli
 *  4) pipx run lobby-ai (ephemeral install)
 *  5) uvx lobby-ai
 */

const { spawnSync } = require('child_process');
const fs = require('fs');
const path = require('path');

function isWin() { return process.platform === 'win32'; }

function which(cmd) {
  const PATH = process.env.PATH || '';
  const split = PATH.split(isWin() ? ';' : ':');
  const exts = isWin() ? (process.env.PATHEXT || '.EXE;.CMD;.BAT').split(';') : [''];
  for (const dir of split) {
    const base = path.join(dir, cmd);
    for (const ext of exts) {
      const candidate = base + ext;
      try { fs.accessSync(candidate, fs.constants.X_OK); return candidate; } catch {}
    }
  }
  return null;
}

function tryRun(cmd, args) {
  const res = spawnSync(cmd, args, { stdio: 'inherit' });
  return res.status === 0;
}

const args = process.argv.slice(2);

// Allow users to force a specific python
const preferredPython = process.env.LOBBY_NODE_WRAPPER_PYTHON;
if (preferredPython && which(preferredPython)) {
  if (tryRun(preferredPython, ['-m', 'lobby.cli', ...args])) process.exit(0);
}

// 1) existing binary
if (which('lobby')) {
  if (tryRun('lobby', args)) process.exit(0);
}
if (which('lobby.exe')) {
  if (tryRun('lobby.exe', args)) process.exit(0);
}

// 2) python3 -m lobby.cli
if (which('python3')) {
  if (tryRun('python3', ['-m', 'lobby.cli', ...args])) process.exit(0);
}

// 3) python -m lobby.cli
if (which('python')) {
  if (tryRun('python', ['-m', 'lobby.cli', ...args])) process.exit(0);
}

// 4) pipx run lobby-ai
if (which('pipx')) {
  if (tryRun('pipx', ['run', 'lobby-ai', ...args])) process.exit(0);
}

// 5) uvx lobby-ai
if (which('uvx')) {
  if (tryRun('uvx', ['lobby-ai', ...args])) process.exit(0);
}

console.error('\n❌ Could not find a working LOBBY installation.');
console.error('Install one of the following and re-run this command:');
console.error('  pipx install lobby-ai');
console.error("  pip install --user lobby-ai    # then ensure your user's bin is on PATH");
console.error('  uvx lobby-ai --help');
console.error('\nTip: set LOBBY_NODE_WRAPPER_PYTHON to force a specific python, e.g.:');
console.error('  LOBBY_NODE_WRAPPER_PYTHON=python3 npx lobby-ai --help');
process.exit(1);
