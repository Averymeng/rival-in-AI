// 前端逻辑：拉取历史报告列表；提交研究目标 → 调用后端闭环。
const statusEl = document.getElementById("status");
const listEl = document.getElementById("report-list");
const form = document.getElementById("goal-form");
const input = document.getElementById("goal-input");

function fmtDate(ts) {
  const d = new Date(ts * 1000);
  return d.getFullYear() + "-" + (d.getMonth() + 1) + "-" + d.getDate();
}

async function loadReports() {
  try {
    const res = await fetch("/api/reports");
    const data = await res.json();
    const reports = data.reports || [];
    if (!reports.length) {
      listEl.innerHTML = '<div class="empty">还没有报告，提交一个研究目标试试。</div>';
      return;
    }
    listEl.innerHTML = reports
      .map(
        (r) =>
          `<a class="card" href="/report/${encodeURIComponent(r.file)}">
             <h3>${r.name}</h3>
             <div class="meta">${r.intent ? "「" + r.intent + "」 " : ""}更新于 ${fmtDate(r.updated)}</div>
           </a>`
      )
      .join("");
  } catch (e) {
    listEl.innerHTML = '<div class="empty">加载失败：' + e.message + "</div>";
  }
}

form.addEventListener("submit", async (e) => {
  e.preventDefault();
  const goal = input.value.trim();
  if (!goal) {
    statusEl.textContent = "请输入研究目标";
    return;
  }
  statusEl.textContent = "正在实时检索并生成报告（通常需要 30–90 秒）…";
  input.disabled = true;
  try {
    const res = await fetch("/api/research", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ goal }),
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || "生成失败");
    statusEl.textContent = "报告已生成：" + data.title;
    window.location.href = data.url;
  } catch (e) {
    statusEl.textContent = "生成失败：" + e.message;
    input.disabled = false;
  }
});

loadReports();
