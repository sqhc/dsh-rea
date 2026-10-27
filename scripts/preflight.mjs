#!/usr/bin/env node
/**
 * Dependency-free preflight for the dsh-rea DeepSeek Harness bundle.
 *
 * Checks the Node.js version, verifies that the npm/npx cache directory is
 * writable, then performs one MCP initialize + tools/list handshake against the
 * official rea-agents package over stdio. Printing the tool count and catalog
 * size makes the Harness-side token cost predictable, and the run warms the
 * npx cache so the first Harness launch does not time out.
 *
 * Usage:
 *   node scripts/preflight.mjs
 *
 * Environment:
 *   DSH_REA_NPM_CACHE             cache directory
 *                                 (default <profile>/cache/dsh-rea/npm, then
 *                                 $DSH_HOME/cache/dsh-rea/npm)
 *   DSH_REA_PREFLIGHT_TIMEOUT_MS  total handshake timeout (default 240000)
 */

import { spawn } from "node:child_process";
import { mkdir, rm, writeFile } from "node:fs/promises";
import { homedir } from "node:os";
import { join } from "node:path";

const REA_VERSION = "6.8.0";
const TIMEOUT_MS = Number(process.env.DSH_REA_PREFLIGHT_TIMEOUT_MS ?? 240_000);

const nodeVersion = process.versions.node;
const [major, minor] = nodeVersion.split(".").map(Number);
const nodeSupported =
  (major === 22 && minor >= 23) || (major === 24 && minor >= 22) || major >= 26;

console.log(`node ${nodeVersion}: ${nodeSupported ? "supported" : "NOT in REA's supported range"}`);
if (!nodeSupported) {
  console.log("  REA 6.8.0+ supports Node 22.x (>=22.23), 24.x (>=24.22), or 26+.");
  console.log("  Node 23.x and 25.x are NOT supported.");
  console.log("  Continuing anyway; some REA tools may fail on this runtime.");
}

const profileDir = process.env.DSH_PROFILE_DIR;
const dshHome = process.env.DSH_HOME ?? join(homedir(), ".dsh");
const cacheDir =
  process.env.DSH_REA_NPM_CACHE ?? join(profileDir ?? dshHome, "cache", "dsh-rea", "npm");

async function checkCache() {
  try {
    await mkdir(cacheDir, { recursive: true });
    const probe = join(cacheDir, `.dsh-rea-write-test-${process.pid}`);
    await writeFile(probe, "ok");
    await rm(probe, { force: true });
  } catch (error) {
    console.error(`FAIL npm cache ${cacheDir} is not writable: ${error.message}`);
    console.error("  Set DSH_REA_NPM_CACHE to a writable directory and retry.");
    process.exit(1);
  }
  console.log(`npm cache ${cacheDir}: writable`);
}

await checkCache();

const child = spawn(
  process.platform === "win32" ? "npx.cmd" : "npx",
  ["-y", `rea-agents@${REA_VERSION}`, "mcp"],
  {
    env: {
      ...process.env,
      NPM_CONFIG_CACHE: cacheDir,
      REA_MCP_INPUT_SCHEMA_PROFILE: "compact",
      REA_MCP_OUTPUT_SCHEMA_PROFILE: "off",
    },
    stdio: ["pipe", "pipe", "pipe"],
    shell: process.platform === "win32",
  },
);

let stdoutBuffer = "";
let stderrTail = "";
let initialized = false;
let settled = false;

const timer = setTimeout(() => {
  finish(false, `handshake timed out after ${TIMEOUT_MS} ms`);
}, TIMEOUT_MS);

function cleanup() {
  clearTimeout(timer);
  try {
    child.stdin.end();
  } catch {
    // The child may already be gone.
  }
  if (!child.killed) child.kill("SIGTERM");
}

function finish(ok, message) {
  if (settled) return;
  settled = true;
  cleanup();
  if (!ok) {
    console.error(`FAIL ${message}`);
    if (stderrTail.trim() !== "") {
      console.error("--- child stderr (tail) ---");
      console.error(stderrTail.trim().slice(-4000));
    }
    process.exitCode = 1;
  }
}

function send(message) {
  if (settled) return;
  try {
    child.stdin.write(`${JSON.stringify(message)}\n`);
  } catch (error) {
    finish(false, `could not write to the MCP server: ${error.message}`);
  }
}

function handleMessage(message) {
  if (message.id === 1) {
    if (message.error !== undefined) {
      finish(false, `initialize failed: ${JSON.stringify(message.error)}`);
      return;
    }
    initialized = true;
    send({ jsonrpc: "2.0", method: "notifications/initialized" });
    send({ jsonrpc: "2.0", id: 2, method: "tools/list", params: {} });
    return;
  }
  if (message.id === 2) {
    if (message.error !== undefined) {
      finish(false, `tools/list failed: ${JSON.stringify(message.error)}`);
      return;
    }
    const tools = message.result?.tools ?? [];
    const bytes = Buffer.byteLength(JSON.stringify(tools), "utf8");
    const largest = [...tools]
      .sort((a, b) => JSON.stringify(b).length - JSON.stringify(a).length)
      .slice(0, 3)
      .map((tool) => `${tool.name} (${JSON.stringify(tool).length} B)`);
    console.log(`REA ${REA_VERSION}: handshake ok`);
    console.log(`  tools: ${tools.length}`);
    console.log(`  catalog: ${(bytes / 1024).toFixed(1)} KiB (~${Math.round(bytes / 4000)}k tokens)`);
    console.log(`  largest schemas: ${largest.join(", ")}`);
    console.log("OK");
    finish(true);
  }
}

child.stdout.setEncoding("utf8");
child.stdout.on("data", (chunk) => {
  stdoutBuffer += chunk;
  let newline = stdoutBuffer.indexOf("\n");
  while (newline !== -1) {
    const line = stdoutBuffer.slice(0, newline).trim();
    stdoutBuffer = stdoutBuffer.slice(newline + 1);
    if (line !== "") {
      try {
        handleMessage(JSON.parse(line));
      } catch {
        // Non-JSON output belongs to the child's own logging.
      }
    }
    newline = stdoutBuffer.indexOf("\n");
  }
});

child.stderr.setEncoding("utf8");
child.stderr.on("data", (chunk) => {
  stderrTail = (stderrTail + chunk).slice(-16_000);
});

child.on("error", (error) => {
  finish(false, `could not start npx: ${error.message}`);
});

child.on("exit", (code, signal) => {
  if (settled) return;
  finish(
    false,
    initialized
      ? `MCP server exited before tools/list (code ${code}, signal ${signal})`
      : `MCP server exited before initialize (code ${code}, signal ${signal})`,
  );
});

send({
  jsonrpc: "2.0",
  id: 1,
  method: "initialize",
  params: {
    protocolVersion: "2025-06-18",
    capabilities: {},
    clientInfo: { name: "dsh-rea-preflight", version: "0.1.0" },
  },
});
