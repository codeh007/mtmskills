#!/usr/bin/env node

import { randomUUID } from "node:crypto";
import { link, lstat, mkdir, rm, writeFile } from "node:fs/promises";
import path from "node:path";

const ENDPOINT = "https://yuepa8.com/v1/images/generations";
const MODEL = "gpt-image-2";
const REQUEST_STDIN_FLAG = "--request-stdin-json";
const MAX_REQUEST_STDIN_BYTES = 128 * 1024;
const REQUEST_TIMEOUT_MS = 15 * 60 * 1000;
const SUPPORTED_SIZES = new Set(["auto", "1024x1024", "1536x1024", "1024x1536"]);
const SUPPORTED_QUALITIES = new Set(["auto", "low", "medium", "high"]);
const POST_DISPATCH_NOTICE = "本次上游请求可能已经产生结果或费用；客户端没有自动重试。";

class ClientError extends Error {
  constructor(message, { afterDispatch = false, cause } = {}) {
    super(message, cause ? { cause } : undefined);
    this.name = "ClientError";
    this.afterDispatch = afterDispatch;
  }
}

function assertRuntime() {
  const major = Number.parseInt(process.versions.node.split(".", 1)[0], 10);
  if (!Number.isInteger(major) || major < 18 || typeof fetch !== "function") {
    throw new ClientError("需要 Node.js 18 或更高版本，且运行时必须提供原生 fetch。");
  }
}

function parseArgs(argv) {
  if (argv.includes(REQUEST_STDIN_FLAG)) {
    if (argv.length !== 1 || argv[0] !== REQUEST_STDIN_FLAG) {
      throw new ClientError(`${REQUEST_STDIN_FLAG} 不能重复或与其他命令行参数混用。`);
    }
    return { readRequestFromStdin: true };
  }

  const values = {};
  const known = new Set(["--prompt", "--output", "--size", "--quality"]);

  for (let index = 0; index < argv.length; index += 1) {
    const flag = argv[index];
    if (!known.has(flag)) {
      throw new ClientError(`不支持的参数：${flag}`);
    }
    if (Object.hasOwn(values, flag)) {
      throw new ClientError(`参数不能重复：${flag}`);
    }
    const value = argv[index + 1];
    if (value === undefined) {
      throw new ClientError(`参数缺少值：${flag}`);
    }
    values[flag] = value;
    index += 1;
  }

  return {
    readRequestFromStdin: false,
    options: normalizeRequestInput({
      prompt: values["--prompt"],
      output: values["--output"],
      size: values["--size"],
      quality: values["--quality"],
    }),
  };
}

function normalizeRequestInput(input) {
  const prompt = typeof input.prompt === "string" ? input.prompt.trim() : "";
  if (!prompt) {
    throw new ClientError("请提供非空的 --prompt 图片描述。");
  }

  const size = input.size;
  if (size !== undefined && typeof size !== "string") {
    throw new ClientError("--size 必须是字符串。");
  }
  if (size && !SUPPORTED_SIZES.has(size)) {
    throw new ClientError(`不支持的 --size：${size}`);
  }

  const quality = input.quality;
  if (quality !== undefined && typeof quality !== "string") {
    throw new ClientError("--quality 必须是字符串。");
  }
  if (quality && !SUPPORTED_QUALITIES.has(quality)) {
    throw new ClientError(`不支持的 --quality：${quality}`);
  }

  if (input.output !== undefined && (typeof input.output !== "string" || !input.output.trim())) {
    throw new ClientError("--output 必须是非空字符串。");
  }
  const output = input.output
    ? path.resolve(input.output)
    : path.resolve(
        "mtm_images",
        `mtm-image2-${new Date().toISOString().replace(/[-:.TZ]/g, "")}-${randomUUID().slice(0, 8)}.png`,
      );

  return { prompt, output, size, quality };
}

async function readRequestFromStdinJson() {
  const line = await readSingleStdinLine();
  let payload;
  try {
    payload = JSON.parse(line);
  } catch (error) {
    throw new ClientError("stdin 请求不是有效的单行 JSON。", { cause: error });
  }

  if (!payload || typeof payload !== "object" || Array.isArray(payload)) {
    throw new ClientError("stdin 请求必须是 JSON object。");
  }
  const allowed = new Set(["prompt", "output", "size", "quality"]);
  const unknown = Object.keys(payload).find((key) => !allowed.has(key));
  if (unknown) {
    throw new ClientError(`stdin 请求包含未知字段：${unknown}`);
  }
  return normalizeRequestInput(payload);
}

async function readSingleStdinLine() {
  const chunks = [];
  let totalBytes = 0;
  try {
    for await (const chunk of process.stdin) {
      const bytes = Buffer.isBuffer(chunk) ? chunk : Buffer.from(chunk);
      totalBytes += bytes.length;
      if (totalBytes > MAX_REQUEST_STDIN_BYTES) {
        throw new ClientError("stdin 请求超过允许大小。");
      }
      chunks.push(bytes);
    }
  } catch (error) {
    if (error instanceof ClientError) throw error;
    throw new ClientError("无法读取 stdin JSON 请求。", { cause: error });
  }

  if (totalBytes === 0) {
    throw new ClientError("stdin 没有提供 JSON 请求。");
  }

  const input = Buffer.concat(chunks, totalBytes).toString("utf8");
  const line = input.endsWith("\r\n")
    ? input.slice(0, -2)
    : input.endsWith("\n")
      ? input.slice(0, -1)
      : input;
  if (!line || line.includes("\n") || line.includes("\r")) {
    throw new ClientError("stdin 只能包含一行 JSON 请求。");
  }
  return line;
}

async function pathExists(filePath) {
  try {
    await lstat(filePath);
    return true;
  } catch (error) {
    if (error?.code === "ENOENT") return false;
    throw new ClientError("无法检查输出路径。", { cause: error });
  }
}

function readDedicatedKey() {
  const key = process.env.MTMAI_IMAGE2_KEY?.trim();
  if (!key) {
    throw new ClientError(
      "缺少专用环境变量 MTMAI_IMAGE2_KEY；请按 references/install.md 完成配置并重启 Codex/IDE。",
    );
  }
  return key;
}

function buildPayload(options) {
  const payload = {
    model: MODEL,
    prompt: options.prompt,
    n: 1,
    stream: true,
    partial_images: 1,
    output_format: "png",
  };
  if (options.size) payload.size = options.size;
  if (options.quality) payload.quality = options.quality;
  return payload;
}

function redact(value, secrets = []) {
  let text = String(value ?? "");
  for (const secret of secrets) {
    if (secret) text = text.split(secret).join("[REDACTED]");
  }
  text = text.replace(/(Bearer\s+)[A-Za-z0-9._~+/=-]{8,}/gi, "$1[REDACTED]");
  text = text.replace(/sk-[A-Za-z0-9_.-]{8,}/g, "sk-[REDACTED]");
  return text.slice(0, 600);
}

async function readResponseText(response) {
  try {
    return await response.text();
  } catch (error) {
    throw new ClientError("读取响应时连接中断。", { afterDispatch: true, cause: error });
  }
}

function parseJson(text, context) {
  try {
    return JSON.parse(text);
  } catch (error) {
    throw new ClientError(`${context}不是有效 JSON。`, { afterDispatch: true, cause: error });
  }
}

function extractJsonBase64(payload) {
  if (!payload || typeof payload !== "object" || !Array.isArray(payload.data) || payload.data.length !== 1) {
    throw new ClientError("JSON 响应必须且只能包含一个 data[0].b64_json。", { afterDispatch: true });
  }
  const value = payload.data[0]?.b64_json;
  if (typeof value !== "string" || !value) {
    throw new ClientError("JSON 响应没有有效的 data[0].b64_json；不会下载 URL fallback。", {
      afterDispatch: true,
    });
  }
  return value;
}

class SseParser {
  constructor() {
    this.buffer = "";
    this.eventName = "";
    this.dataLines = [];
    this.completedBase64 = undefined;
  }

  push(text) {
    this.buffer += text;
    let newlineIndex;
    while ((newlineIndex = this.buffer.indexOf("\n")) !== -1) {
      let line = this.buffer.slice(0, newlineIndex);
      this.buffer = this.buffer.slice(newlineIndex + 1);
      if (line.endsWith("\r")) line = line.slice(0, -1);
      this.#line(line);
    }
  }

  finish() {
    if (this.buffer) {
      const line = this.buffer.endsWith("\r") ? this.buffer.slice(0, -1) : this.buffer;
      this.buffer = "";
      this.#line(line);
    }
    this.#dispatch();
    if (!this.completedBase64) {
      throw new ClientError("SSE 已结束，但没有收到 image_generation.completed。", { afterDispatch: true });
    }
    return this.completedBase64;
  }

  #line(line) {
    if (line === "") {
      this.#dispatch();
      return;
    }
    if (line.startsWith(":")) return;

    const colon = line.indexOf(":");
    const field = colon === -1 ? line : line.slice(0, colon);
    let value = colon === -1 ? "" : line.slice(colon + 1);
    if (value.startsWith(" ")) value = value.slice(1);
    if (field === "event") this.eventName = value;
    if (field === "data") this.dataLines.push(value);
  }

  #dispatch() {
    if (this.dataLines.length === 0) {
      this.eventName = "";
      return;
    }

    const eventName = this.eventName;
    const data = this.dataLines.join("\n");
    this.eventName = "";
    this.dataLines = [];
    if (data === "[DONE]") return;

    const payload = parseJson(data, "SSE data");
    const type = typeof payload?.type === "string" ? payload.type : eventName;
    if (eventName === "error" || type === "error" || type.endsWith(".error") || payload?.error) {
      throw new ClientError("SSE 返回 terminal error。", { afterDispatch: true });
    }

    if (type === "image_generation.completed") {
      if (this.completedBase64 !== undefined) {
        throw new ClientError("SSE 返回了多个 completed 图片。", { afterDispatch: true });
      }
      if (typeof payload?.b64_json !== "string" || !payload.b64_json) {
        throw new ClientError("image_generation.completed 缺少 b64_json。", { afterDispatch: true });
      }
      this.completedBase64 = payload.b64_json;
    }
  }
}

async function parseEventStream(response) {
  if (!response.body) {
    throw new ClientError("event-stream 响应没有可读取的 body。", { afterDispatch: true });
  }

  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  const parser = new SseParser();
  let mode;
  let prefix = "";
  let rawJson = "";

  try {
    while (true) {
      const { value, done } = await reader.read();
      if (done) break;
      const text = decoder.decode(value, { stream: true });

      if (!mode) {
        prefix += text;
        const first = prefix.match(/\S/);
        if (!first) continue;
        mode = first[0] === "{" ? "json" : "sse";
        if (mode === "json") rawJson = prefix;
        else parser.push(prefix);
        prefix = "";
        continue;
      }

      if (mode === "json") rawJson += text;
      else parser.push(text);
    }

    const tail = decoder.decode();
    if (!mode) {
      prefix += tail;
      const first = prefix.match(/\S/);
      if (!first) throw new ClientError("event-stream 响应为空。", { afterDispatch: true });
      mode = first[0] === "{" ? "json" : "sse";
      if (mode === "json") rawJson = prefix;
      else parser.push(prefix);
    } else if (mode === "json") rawJson += tail;
    else parser.push(tail);

    if (mode === "json") {
      return {
        base64: extractJsonBase64(parseJson(rawJson, "event-stream JSON fallback")),
        responseMode: "json-event-stream-fallback",
      };
    }
    return { base64: parser.finish(), responseMode: "sse" };
  } catch (error) {
    try {
      await reader.cancel();
    } catch {
      // 原始错误更有诊断价值。
    }
    if (error instanceof ClientError) throw error;
    throw new ClientError("读取 SSE 时连接中断。", { afterDispatch: true, cause: error });
  }
}

async function parseSuccessfulResponse(response) {
  const contentType = response.headers.get("content-type")?.toLowerCase() ?? "";
  if (contentType.includes("application/json")) {
    const payload = parseJson(await readResponseText(response), "JSON 响应");
    return { base64: extractJsonBase64(payload), responseMode: "json" };
  }
  if (contentType.includes("text/event-stream")) {
    return parseEventStream(response);
  }
  throw new ClientError("Images API 返回不支持的响应类型。", { afterDispatch: true });
}

function decodeBase64(value) {
  const pattern = /^(?:[A-Za-z0-9+/]{4})*(?:[A-Za-z0-9+/]{2}==|[A-Za-z0-9+/]{3}=)?$/;
  if (typeof value !== "string" || value.length === 0 || value.length % 4 !== 0 || !pattern.test(value)) {
    throw new ClientError("最终图片的 b64_json 不是有效 base64。", { afterDispatch: true });
  }
  const bytes = Buffer.from(value, "base64");
  if (bytes.length === 0) {
    throw new ClientError("最终图片解码后为空。", { afterDispatch: true });
  }
  validatePng(bytes);
  return bytes;
}

const PNG_SIGNATURE = Buffer.from([0x89, 0x50, 0x4e, 0x47, 0x0d, 0x0a, 0x1a, 0x0a]);
const CRC32_TABLE = Uint32Array.from({ length: 256 }, (_, value) => {
  let crc = value;
  for (let bit = 0; bit < 8; bit += 1) {
    crc = (crc >>> 1) ^ ((crc & 1) ? 0xedb88320 : 0);
  }
  return crc >>> 0;
});

function validatePng(bytes) {
  if (bytes.length < 33 || !bytes.subarray(0, PNG_SIGNATURE.length).equals(PNG_SIGNATURE)) {
    throw new ClientError("最终图片不是有效 PNG。", { afterDispatch: true });
  }

  let offset = PNG_SIGNATURE.length;
  let sawHeader = false;
  let sawImageData = false;
  while (offset < bytes.length) {
    if (bytes.length - offset < 12) {
      throw new ClientError("最终 PNG chunk 不完整。", { afterDispatch: true });
    }
    const length = bytes.readUInt32BE(offset);
    const typeOffset = offset + 4;
    const dataOffset = typeOffset + 4;
    const crcOffset = dataOffset + length;
    const nextOffset = crcOffset + 4;
    if (nextOffset > bytes.length) {
      throw new ClientError("最终 PNG chunk 长度无效。", { afterDispatch: true });
    }

    const type = bytes.toString("ascii", typeOffset, dataOffset);
    if (!sawHeader) {
      if (type !== "IHDR" || length !== 13) {
        throw new ClientError("最终 PNG 缺少有效 IHDR。", { afterDispatch: true });
      }
      if (bytes.readUInt32BE(dataOffset) === 0 || bytes.readUInt32BE(dataOffset + 4) === 0) {
        throw new ClientError("最终 PNG 尺寸无效。", { afterDispatch: true });
      }
      sawHeader = true;
    } else if (type === "IHDR") {
      throw new ClientError("最终 PNG 包含重复 IHDR。", { afterDispatch: true });
    }

    const expectedCrc = bytes.readUInt32BE(crcOffset);
    const actualCrc = crc32(bytes.subarray(typeOffset, crcOffset));
    if (actualCrc !== expectedCrc) {
      throw new ClientError("最终 PNG chunk 校验失败。", { afterDispatch: true });
    }

    if (type === "IDAT") sawImageData = true;
    if (type === "IEND") {
      if (length !== 0 || !sawImageData || nextOffset !== bytes.length) {
        throw new ClientError("最终 PNG 结束结构无效。", { afterDispatch: true });
      }
      return;
    }
    offset = nextOffset;
  }

  throw new ClientError("最终 PNG 缺少 IEND。", { afterDispatch: true });
}

function crc32(bytes) {
  let crc = 0xffffffff;
  for (const byte of bytes) {
    crc = CRC32_TABLE[(crc ^ byte) & 0xff] ^ (crc >>> 8);
  }
  return (crc ^ 0xffffffff) >>> 0;
}

async function atomicWrite(output, bytes) {
  const directory = path.dirname(output);
  const temporary = path.join(directory, `.${path.basename(output)}.${process.pid}.${randomUUID()}.tmp`);
  try {
    await mkdir(directory, { recursive: true });
    await writeFile(temporary, bytes, { flag: "wx", mode: 0o600 });
    await link(temporary, output);
    await rm(temporary);
  } catch (error) {
    await rm(temporary, { force: true }).catch(() => {});
    if (error instanceof ClientError) throw error;
    if (error?.code === "EEXIST") {
      throw new ClientError("写入前输出路径已出现，拒绝覆盖。", { afterDispatch: true, cause: error });
    }
    throw new ClientError("无法原子写入最终图片。", { afterDispatch: true, cause: error });
  }
}

async function dispatch(payload, key) {
  let response;
  try {
    response = await fetch(ENDPOINT, {
      method: "POST",
      headers: {
        Accept: "text/event-stream",
        Authorization: `Bearer ${key}`,
        "Content-Type": "application/json",
      },
      body: JSON.stringify(payload),
      signal: AbortSignal.timeout(REQUEST_TIMEOUT_MS),
    });
  } catch (error) {
    throw new ClientError("Images API 请求失败或超时。", { afterDispatch: true, cause: error });
  }

  if (!response.ok) {
    await response.body?.cancel().catch(() => {});
    throw new ClientError(`Images API 返回 HTTP ${response.status}。`, { afterDispatch: true });
  }
  return parseSuccessfulResponse(response);
}

async function main() {
  assertRuntime();
  const parsed = parseArgs(process.argv.slice(2));
  const options = parsed.readRequestFromStdin
    ? await readRequestFromStdinJson()
    : parsed.options;
  promptForRedaction = options.prompt;
  if (await pathExists(options.output)) {
    throw new ClientError("--output 指向已存在的路径，拒绝覆盖。");
  }
  const key = readDedicatedKey();
  const result = await dispatch(buildPayload(options), key);
  const bytes = decodeBase64(result.base64);
  await atomicWrite(options.output, bytes);
  process.stdout.write(`${JSON.stringify({ ok: true, output: options.output, response_mode: result.responseMode })}\n`);
}

let keyForRedaction = "";
let promptForRedaction = "";
try {
  keyForRedaction = process.env.MTMAI_IMAGE2_KEY?.trim() ?? "";
  await main();
} catch (error) {
  const afterDispatch = error instanceof ClientError && error.afterDispatch;
  const message = redact(error instanceof Error ? error.message : error, [keyForRedaction, promptForRedaction]);
  process.stderr.write(`错误：${message}${afterDispatch ? ` ${POST_DISPATCH_NOTICE}` : ""}\n`);
  process.exitCode = 1;
}
