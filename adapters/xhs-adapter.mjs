// xhs-adapter — 包一层本地 xiaohongshu-mcp（:18060），对上 smart-search 私域搜索契约。
// 只检索。登录走上游二维码页（GET /login），cookies 由上游服务保存。
// 密钥不经过命令行：XHS_ADAPTER_TOKEN 只来自环境变量。
import { createServer } from "node:http";
import { spawn } from "node:child_process";

const UPSTREAM = process.env.XHS_UPSTREAM ?? "http://127.0.0.1:18060";
const PORT = Number(process.env.XHS_ADAPTER_PORT ?? 18061);
const TOKEN = process.env.XHS_ADAPTER_TOKEN ?? "local-xhs";

function mcpJson(c) {
	return JSON.stringify(c).replace(/[\u0080-\uffff]/g, (ch) =>
		"\\u" + ch.charCodeAt(0).toString(16).padStart(4, "0"),
	);
}

function send(res, status, body, type = "application/json; charset=utf-8") {
	res.writeHead(status, { "Content-Type": type, "Cache-Control": "no-store" });
	res.end(typeof body === "string" ? body : mcpJson(body));
}

async function upstreamJson(path, options = {}) {
	const response = await fetch(UPSTREAM + path, {
		...options,
		headers: { Accept: "application/json", ...(options.headers ?? {}) },
	});
	const text = await response.text();
	let data;
	try {
		data = JSON.parse(text);
	} catch {
		throw new Error(`upstream ${response.status} non-JSON`);
	}
	if (!response.ok) {
		const error = new Error(data?.error || data?.message || `upstream ${response.status}`);
		error.status = response.status;
		throw error;
	}
	return data;
}

async function loginStatus(timeoutMs = 2500) {
	try {
		const payload = await upstreamJson("/api/v1/login/status", { signal: AbortSignal.timeout(timeoutMs) });
		return payload?.data ?? { is_logged_in: false };
	} catch {
		return { is_logged_in: false, unreachable: true };
	}
}

function normalizeFeed(feed) {
	const card = feed?.noteCard ?? {};
	const nickname = card.user?.nickname ?? card.user?.nickName ?? "";
	const interact = card.interactInfo ?? {};
	const url = `https://www.xiaohongshu.com/explore/${feed.id}?xsec_token=${feed.xsecToken ?? ""}&xsec_source=pc_search`;
	const counts = [
		interact.likedCount ? `赞${interact.likedCount}` : "",
		interact.collectedCount ? `藏${interact.collectedCount}` : "",
		interact.commentCount ? `评${interact.commentCount}` : "",
	]
		.filter(Boolean)
		.join(" ");
	return {
		title: String(card.displayTitle ?? "").trim(),
		url,
		snippet: counts,
		source: "xiaohongshu",
		published_date: "",
		author: String(nickname).trim(),
		id: String(feed.id ?? ""),
	};
}

const searchCache = new Map();
const CACHE_TTL_MS = 60_000;

async function handleSearch(body) {
	const query = String(body?.query ?? "").trim();
	const count = Math.min(Number(body?.count ?? 8) || 8, 30);
	if (!query) return { ok: false, error: { code: "upstream", message: "query is empty" } };
	const cached = searchCache.get(query);
	if (cached && Date.now() - cached.at < CACHE_TTL_MS) {
		const results = cached.results.slice(0, count);
		if (results.length) return { ok: true, results };
	}
	try {
		const payload = await upstreamJson(
			`/api/v1/feeds/search?keyword=${encodeURIComponent(query)}`,
		);
		const feeds = payload?.data?.feeds ?? [];
		const results = feeds.slice(0, count).map(normalizeFeed).filter((item) => item.title || item.url);
		if (!results.length) return { ok: false, error: { code: "empty", message: "no results" } };
		searchCache.set(query, { at: Date.now(), results });
		return { ok: true, results };
	} catch (error) {
		const status = error.status ?? 0;
		const code = status === 401 || status === 403 ? "auth_required" : status === 429 ? "rate_limited" : "upstream";
		return { ok: false, error: { code, message: String(error.message).slice(0, 300) } };
	}
}

const LOGIN_PAGE = `<!doctype html><html lang="zh"><head><meta charset="utf-8">
<title>小红书登录</title><style>body{font-family:system-ui;background:#111;color:#eee;text-align:center;padding:2rem}
img{background:#fff;padding:12px;border-radius:12px}</style></head><body>
<h2>小红书登录</h2><p>用小红书 App 扫下面的二维码。</p>
<div id="qr">加载中…</div><p id="status"></p>
<script>
async function refresh(){
  try{
    const qr=await fetch('/qr').then(r=>r.json());
    const img=qr?.data?.qr_code_base64 || qr?.data?.image_base64 || qr?.data?.base64 || qr?.data?.qrCodeBase64 || '';
    document.getElementById('qr').innerHTML = img
      ? '<img src="data:image/png;base64,'+img+'" width="280">'
      : '二维码获取失败：'+JSON.stringify(qr).slice(0,120);
  }catch(e){document.getElementById('qr').textContent='二维码获取失败：'+e;}
  try{
    const st=await fetch('/login/status').then(r=>r.json());
    const d=st?.data ?? {};
    document.getElementById('status').textContent = d.is_logged_in
      ? '已登录：'+(d.username||'')+'，可以回到 smart-search 继续搜索。'
      : '未登录';
  }catch(e){document.getElementById('status').textContent='状态获取失败';}
}
refresh(); setInterval(refresh, 5000);
</script></body></html>`;

const server = createServer(async (req, res) => {
	const url = new URL(req.url, `http://127.0.0.1:${PORT}`);
	if (url.pathname === "/health") {
		const login = await loginStatus(2000);
		return send(res, 200, { ok: true, service: "xhs-adapter", upstream: UPSTREAM, login });
	}
	if (url.pathname === "/login" && req.method === "GET") {
		return send(res, 200, LOGIN_PAGE, "text/html; charset=utf-8");
	}
	if (url.pathname === "/login/open" && req.method === "POST") {
		if (process.platform === "win32") {
			spawn("cmd", ["/c", "start", "", `http://127.0.0.1:${PORT}/login`], { detached: true, windowsHide: false, stdio: "ignore" }).unref();
		}
		return send(res, 200, { ok: true, login_url: `http://127.0.0.1:${PORT}/login` });
	}
	if (url.pathname === "/qr") {
		try {
			const payload = await upstreamJson("/api/v1/login/qrcode");
			return send(res, 200, payload);
		} catch (error) {
			return send(res, 502, { error: String(error.message) });
		}
	}
	if (url.pathname === "/login/status") {
		const payload = await upstreamJson("/api/v1/login/status").catch((error) => ({ error: String(error.message) }));
		return send(res, 200, payload);
	}
	if (url.pathname === "/search" && req.method === "POST") {
		let body = "";
		req.on("data", (chunk) => {
			body += chunk;
			if (body.length > 100_000) req.destroy();
		});
		req.on("end", async () => {
			const auth = req.headers.authorization ?? "";
			if (auth !== `Bearer ${TOKEN}`) {
				return send(res, 401, { error: { code: "auth_required", message: "bad bearer token" } });
			}
			let parsed = {};
			try {
				parsed = JSON.parse(body || "{}");
			} catch {
				return send(res, 400, { error: { code: "upstream", message: "invalid JSON body" } });
			}
			return send(res, 200, await handleSearch(parsed));
		});
		return;
	}
	send(res, 404, { error: { code: "upstream", message: "not found" } });
});

server.listen(PORT, "127.0.0.1", () => {
	console.log(`xhs-adapter listening on http://127.0.0.1:${PORT} (upstream ${UPSTREAM})`);
});
