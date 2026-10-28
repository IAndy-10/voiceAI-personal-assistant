// Fails if the built client contains anything that looks like a provider API key,
// or any API key value from server/.env. Prints file and variable names, never values.
import { existsSync, readdirSync, readFileSync, statSync } from "node:fs";
import { join } from "node:path";
import { fileURLToPath } from "node:url";

const DIST = fileURLToPath(new URL("../dist/", import.meta.url));
const ENV = fileURLToPath(new URL("../../server/.env", import.meta.url));

const PATTERNS = {
  anthropic: /sk-ant-[A-Za-z0-9_-]{20,}/,
  openai: /sk-(?!ant-)(proj-)?[A-Za-z0-9_-]{32,}/,
  google: /AIza[0-9A-Za-z_-]{35}/,
};

function files(dir) {
  return readdirSync(dir).flatMap((name) => {
    const path = join(dir, name);
    return statSync(path).isDirectory() ? files(path) : [path];
  });
}

function envSecrets() {
  if (!existsSync(ENV)) return {};
  const secrets = {};
  for (const line of readFileSync(ENV, "utf8").split("\n")) {
    const match = line.match(/^\s*([A-Z0-9_]*_KEY)\s*=\s*["']?([^"'\s#]+)/);
    if (match && match[2].length >= 8) secrets[match[1]] = match[2];
  }
  return secrets;
}

if (!existsSync(DIST)) {
  console.error("client/dist/ not found. Run `npm run build` first.");
  process.exit(1);
}

const secrets = envSecrets();
const findings = [];
for (const file of files(DIST)) {
  const content = readFileSync(file, "utf8");
  for (const [name, pattern] of Object.entries(PATTERNS)) {
    if (pattern.test(content)) findings.push(`${file}: looks like a ${name} API key`);
  }
  for (const [name, value] of Object.entries(secrets)) {
    if (content.includes(value)) findings.push(`${file}: contains the value of ${name}`);
  }
}

if (findings.length > 0) {
  console.error(findings.join("\n"));
  process.exit(1);
}
console.log(`No API keys found in dist/ (checked ${Object.keys(secrets).length} .env keys).`);
