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
const skillEntry = path.join(skillDir, "SKILL.md");
const fixtureBytes = Buffer.from(
  "89504e470d0a1a0a0000000d4948445200000001000000010804000000b51c0c020000000b4944415478da6364f80f00010501012718e3660000000049454e44ae426082",
  "hex",
);
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
  const body = JSON.parse(String(init.body));
  appendFileSync(
    process.env.FIXTURE_LOG,
    JSON.stringify({
      method: init.method,
      url: String(url),
      accept: headers.get("accept"),
      content_type: headers.get("content-type"),
      authorization_present: headers.has("authorization"),
      body,
    }) + "\\n",
  );

  if (process.env.FIXTURE_MODE === "http-error") {
    return new Response(
      JSON.stringify({
        error: {
          message: "fixture rejected " + headers.get("authorization") + " prompt=" + body.prompt,
        },
      }),
      {
        status: 503,
        headers: { "content-type": "application/json" },
      },
    );
  }

  if (process.env.FIXTURE_MODE === "bad-content-type") {
    const transformedPrompt = body.prompt.toUpperCase().replace(/\\s+/g, "-");
    return new Response("ignored", {
      status: 200,
      headers: { "content-type": "application/x-" + transformedPrompt },
    });
  }

  let bytes = Buffer.from("${fixtureBytes.toString("hex")}", "hex");
  if (process.env.FIXTURE_MODE === "non-png") {
    bytes = Buffer.from("not-a-png");
  } else if (process.env.FIXTURE_MODE === "png-no-ihdr") {
    bytes = Buffer.concat([bytes.subarray(0, 8), bytes.subarray(33)]);
  } else if (process.env.FIXTURE_MODE === "png-no-idat") {
    bytes = Buffer.concat([bytes.subarray(0, 33), bytes.subarray(bytes.length - 12)]);
  } else if (process.env.FIXTURE_MODE === "png-no-iend") {
    bytes = bytes.subarray(0, bytes.length - 12);
  } else if (process.env.FIXTURE_MODE === "png-bad-length") {
    bytes = Buffer.from(bytes);
    bytes.writeUInt32BE(bytes.length, 33);
  } else if (process.env.FIXTURE_MODE === "png-bad-crc") {
    bytes = Buffer.from(bytes);
    bytes[bytes.length - 1] ^= 1;
  } else if (process.env.FIXTURE_MODE === "png-trailing") {
    bytes = Buffer.concat([bytes, Buffer.from([0])]);
  }
  const b64 = bytes.toString("base64");
  if (["sse", "sse-multiple", "sse-error-after-completed"].includes(process.env.FIXTURE_MODE)) {
    const completed = JSON.stringify({
      type: "image_generation.completed",
      b64_json: b64,
    });
    const frame = "event: image_generation.completed\\ndata: " + completed + "\\n\\n";
    const suffix = process.env.FIXTURE_MODE === "sse-multiple"
      ? frame
      : process.env.FIXTURE_MODE === "sse-error-after-completed"
        ? "event: error\\ndata: " + JSON.stringify({ error: { message: body.prompt } }) + "\\n\\n"
        : "";
    return new Response(
      ": keepalive\\n\\n" + frame + suffix,
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

function runClient({
  root,
  preload,
  mode,
  args = [],
  prompt = "fixture prompt",
  request = {},
  promptMode = "stdin-json",
  stdinInput,
  withKey = true,
}) {
  const log = path.join(root, `${mode}-${crypto.randomUUID()}.jsonl`);
  const promptArgs = promptMode === "stdin-json"
    ? ["--request-stdin-json"]
    : ["--prompt", prompt];
  const result = spawnSync(
    process.execPath,
    [
      "--import",
      preload,
      targetScript,
      ...promptArgs,
      ...args,
    ],
    {
      cwd: root,
      encoding: "utf8",
      input: stdinInput ?? (promptMode === "stdin-json"
        ? `${JSON.stringify({ prompt, ...request })}\n`
        : undefined),
      env: {
        ...process.env,
        FIXTURE_LOG: log,
        FIXTURE_MODE: mode,
        MTMAI_IMAGE2_KEY: withKey ? fixtureKey : "",
      },
    },
  );
  const requests = existsSync(log)
    ? readFileSync(log, "utf8").trim().split("\n").filter(Boolean).map((line) => JSON.parse(line))
    : [];
  return { result, requests };
}

function assertGenerationRequest(request, prompt = "fixture prompt") {
  assert.deepEqual(request, {
    method: "POST",
    url: "https://yuepa8.com/v1/images/generations",
    accept: "text/event-stream",
    content_type: "application/json",
    authorization_present: true,
    body: {
      model: "gpt-image-2",
      prompt,
      n: 1,
      stream: true,
      partial_images: 1,
      output_format: "png",
    },
  });
}

test("documented normal command keeps the prompt out of shell source", () => {
  const source = readFileSync(skillEntry, "utf8");
  assert.match(source, /--request-stdin-json/);
  assert.doesNotMatch(source, /--prompt\s+"<图片描述>"/);
});

test("stdin JSON transports shell metacharacters as literal prompt data", (t) => {
  const fixture = createFixture(t);
  const prompt = 'literal $(touch should-not-run) `id` "quote"\nsecond line';
  const { result, requests } = runClient({ ...fixture, mode: "json", prompt });

  assert.equal(result.status, 0, result.stderr);
  assert.equal(requests.length, 1);
  assertGenerationRequest(requests[0], prompt);
  assert.equal(existsSync(path.join(fixture.root, "should-not-run")), false);
});

test("stdin JSON rejects a second physical line before dispatch", (t) => {
  const fixture = createFixture(t);
  const { result, requests } = runClient({
    ...fixture,
    mode: "json",
    stdinInput: `${JSON.stringify({ prompt: "fixture prompt" })}\n\n`,
  });

  assert.notEqual(result.status, 0);
  assert.equal(requests.length, 0);
  assert.match(result.stderr, /一行 JSON/);
  assert.equal(existsSync(path.join(fixture.root, "mtm_images")), false);
});

for (const [name, options, expectedError] of [
  ["unknown field", { request: { unexpected: true } }, /未知字段/],
  ["wrong field type", { request: { size: 1 } }, /必须是字符串/],
  ["argv mixing", { args: ["--quality", "high"] }, /不能.*混用/],
  [
    "oversized input",
    { stdinInput: `${JSON.stringify({ prompt: "x".repeat(128 * 1024) })}\n` },
    /超过允许大小/,
  ],
]) {
  test(`stdin JSON rejects ${name} before dispatch`, (t) => {
    const fixture = createFixture(t);
    const { result, requests } = runClient({
      ...fixture,
      mode: "json",
      ...options,
    });

    assert.notEqual(result.status, 0);
    assert.equal(requests.length, 0);
    assert.match(result.stderr, expectedError);
    assert.equal(existsSync(path.join(fixture.root, "mtm_images")), false);
  });
}

for (const mode of ["json", "sse"]) {
  test(`default ${mode} output stays under mtm_images`, (t) => {
    const fixture = createFixture(t);
    const beforeSkillEntries = readdirSync(skillDir).sort();
    const { result, requests } = runClient({ ...fixture, mode });

    assert.equal(result.status, 0, result.stderr);
    assert.equal(requests.length, 1);
    assertGenerationRequest(requests[0]);
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
    request: { output: "custom/result.png" },
  });

  assert.equal(result.status, 0, result.stderr);
  assert.equal(requests.length, 1);
  assertGenerationRequest(requests[0]);
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
  const prompt = "sensitive prompt first line\nsecond line";
  const { result, requests } = runClient({
    ...fixture,
    mode: "http-error",
    prompt,
  });

  assert.notEqual(result.status, 0);
  assert.equal(requests.length, 1);
  assertGenerationRequest(requests[0], prompt);
  assert.match(result.stderr, /客户端没有自动重试/);
  assert.doesNotMatch(result.stderr, new RegExp(fixtureKey));
  assert.doesNotMatch(result.stderr, /Bearer fixture/);
  assert.doesNotMatch(result.stderr, /sensitive prompt first line/);
  assert.doesNotMatch(result.stderr, /second line/);
  assert.equal(existsSync(path.join(fixture.root, "mtm_images")), false);
});

test("unsupported response content type does not echo the untrusted header", (t) => {
  const fixture = createFixture(t);
  const prompt = "Sensitive Prompt First Line\nSecond Line";
  const { result, requests } = runClient({
    ...fixture,
    mode: "bad-content-type",
    prompt,
  });

  assert.notEqual(result.status, 0);
  assert.equal(requests.length, 1);
  assertGenerationRequest(requests[0], prompt);
  assert.doesNotMatch(result.stderr, /sensitive-prompt-first-line-second-line/i);
  assert.doesNotMatch(result.stderr, /application\/x-/i);
  assert.match(result.stderr, /客户端没有自动重试/);
  assert.equal(existsSync(path.join(fixture.root, "mtm_images")), false);
});

test("multiple SSE completed events fail after the single request", (t) => {
  const fixture = createFixture(t);
  const { result, requests } = runClient({ ...fixture, mode: "sse-multiple" });

  assert.notEqual(result.status, 0);
  assert.equal(requests.length, 1);
  assertGenerationRequest(requests[0]);
  assert.match(result.stderr, /多个 completed/);
  assert.match(result.stderr, /客户端没有自动重试/);
  assert.equal(existsSync(path.join(fixture.root, "mtm_images")), false);
});

test("terminal SSE error after completed fails without echoing the prompt", (t) => {
  const fixture = createFixture(t);
  const prompt = "terminal-sensitive-prompt";
  const { result, requests } = runClient({
    ...fixture,
    mode: "sse-error-after-completed",
    prompt,
  });

  assert.notEqual(result.status, 0);
  assert.equal(requests.length, 1);
  assertGenerationRequest(requests[0], prompt);
  assert.match(result.stderr, /terminal error/);
  assert.doesNotMatch(result.stderr, new RegExp(prompt));
  assert.match(result.stderr, /客户端没有自动重试/);
  assert.equal(existsSync(path.join(fixture.root, "mtm_images")), false);
});

for (const mode of [
  "non-png",
  "png-no-ihdr",
  "png-no-idat",
  "png-no-iend",
  "png-bad-length",
  "png-bad-crc",
  "png-trailing",
]) {
  test(`${mode} response bytes fail after the single request`, (t) => {
    const fixture = createFixture(t);
    const { result, requests } = runClient({
      ...fixture,
      mode,
      promptMode: "argv",
    });

    assert.notEqual(result.status, 0);
    assert.equal(requests.length, 1);
    assertGenerationRequest(requests[0]);
    assert.match(result.stderr, /PNG/);
    assert.match(result.stderr, /客户端没有自动重试/);
    assert.equal(existsSync(path.join(fixture.root, "mtm_images")), false);
  });
}
