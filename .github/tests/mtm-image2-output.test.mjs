import assert from "node:assert/strict";
import { spawnSync } from "node:child_process";
import {
  existsSync,
  mkdtempSync,
  readFileSync,
  readdirSync,
  rmSync,
  writeFileSync,
} from "node:fs";
import os from "node:os";
import path from "node:path";
import test from "node:test";
import { fileURLToPath } from "node:url";

const repoRoot = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "../..");
const targetScript = path.join(
  repoRoot,
  "skills/mtmskills/mtm-image2/scripts/generate.mjs",
);
const skillDir = path.dirname(path.dirname(targetScript));
const fixtureBytes = Buffer.from("fixture-image");
const fixtureKey = "fixture-sensitive-token-123";

function createFixture(t) {
  const root = mkdtempSync(path.join(os.tmpdir(), "mtm-image2-output-"));
  const preload = path.join(root, "preload.mjs");
  t.after(() => rmSync(root, { recursive: true, force: true }));
  writeFileSync(
    preload,
    `
import { appendFileSync } from "node:fs";

globalThis.fetch = async (url, init = {}) => {
  const headers = new Headers(init.headers);
  appendFileSync(
    process.env.FIXTURE_LOG,
    JSON.stringify({
      method: init.method,
      url: String(url),
      authorization_present: headers.has("authorization"),
    }) + "\\n",
  );

  if (process.env.FIXTURE_MODE === "http-error") {
    return new Response(
      JSON.stringify({
        error: {
          message: "fixture rejected " + headers.get("authorization"),
        },
      }),
      {
        status: 503,
        headers: { "content-type": "application/json" },
      },
    );
  }

  const b64 = Buffer.from("fixture-image").toString("base64");
  if (process.env.FIXTURE_MODE === "sse") {
    const completed = JSON.stringify({
      type: "image_generation.completed",
      b64_json: b64,
    });
    return new Response(
      ": keepalive\\n\\nevent: image_generation.completed\\ndata: " +
        completed +
        "\\n\\n",
      {
        status: 200,
        headers: { "content-type": "text/event-stream" },
      },
    );
  }

  return new Response(JSON.stringify({ data: [{ b64_json: b64 }] }), {
    status: 200,
    headers: { "content-type": "application/json" },
  });
};
`,
  );
  return { root, preload };
}

function runClient({ root, preload, mode, args = [], withKey = true }) {
  const log = path.join(root, `${mode}-${crypto.randomUUID()}.jsonl`);
  const result = spawnSync(
    process.execPath,
    [
      "--import",
      preload,
      targetScript,
      "--prompt",
      "fixture prompt",
      ...args,
    ],
    {
      cwd: root,
      encoding: "utf8",
      env: {
        ...process.env,
        FIXTURE_LOG: log,
        FIXTURE_MODE: mode,
        MTMAI_IMAGE2_KEY: withKey ? fixtureKey : "",
      },
    },
  );
  const requests = existsSync(log)
    ? readFileSync(log, "utf8").trim().split("\n").filter(Boolean)
    : [];
  return { result, requests };
}

for (const mode of ["json", "sse"]) {
  test(`default ${mode} output stays under mtm_images`, (t) => {
    const fixture = createFixture(t);
    const beforeSkillEntries = readdirSync(skillDir).sort();
    const { result, requests } = runClient({ ...fixture, mode });

    assert.equal(result.status, 0, result.stderr);
    assert.equal(requests.length, 1);
    const output = JSON.parse(result.stdout);
    assert.equal(path.dirname(output.output), path.join(fixture.root, "mtm_images"));
    assert.deepEqual(readFileSync(output.output), fixtureBytes);
    assert.equal(
      readdirSync(fixture.root).some((entry) => entry.endsWith(".png")),
      false,
    );
    assert.deepEqual(readdirSync(skillDir).sort(), beforeSkillEntries);
  });
}

test("explicit output remains relative to workdir", (t) => {
  const fixture = createFixture(t);
  const { result, requests } = runClient({
    ...fixture,
    mode: "json",
    args: ["--output", "custom/result.png"],
  });

  assert.equal(result.status, 0, result.stderr);
  assert.equal(requests.length, 1);
  const output = JSON.parse(result.stdout);
  assert.equal(output.output, path.join(fixture.root, "custom/result.png"));
  assert.deepEqual(readFileSync(output.output), fixtureBytes);
  assert.equal(existsSync(path.join(fixture.root, "mtm_images")), false);
});

test("missing key fails before dispatch", (t) => {
  const fixture = createFixture(t);
  const { result, requests } = runClient({
    ...fixture,
    mode: "json",
    withKey: false,
  });

  assert.notEqual(result.status, 0);
  assert.equal(requests.length, 0);
  assert.equal(existsSync(path.join(fixture.root, "mtm_images")), false);
});

test("post-dispatch error is single-request and secret-safe", (t) => {
  const fixture = createFixture(t);
  const { result, requests } = runClient({
    ...fixture,
    mode: "http-error",
  });

  assert.notEqual(result.status, 0);
  assert.equal(requests.length, 1);
  assert.match(result.stderr, /客户端没有自动重试/);
  assert.doesNotMatch(result.stderr, new RegExp(fixtureKey));
  assert.doesNotMatch(result.stderr, /Bearer fixture/);
  assert.equal(existsSync(path.join(fixture.root, "mtm_images")), false);
});
