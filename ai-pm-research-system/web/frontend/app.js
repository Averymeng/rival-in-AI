// 前端逻辑：拉取历史报告列表；提交目标（P1+ 接入研究闭环）。
const statusEl = document.getElementById("status");
const listEl = document.getElementById("report-list");
const form = document.getElementById("goal-form");
const input = document.getElementById("goal-input");

function fmtDate(ts){
  const d = new Date(ts*1000);
  return d.getFullYear()+"-"+(d.getMonth()+1)+"-"+d.getDate();
}

async function loadReports(){
  try{
    const res = await fetch("/api/reports");
    const data = await res.json();
    const reports = data.reports || [];
    if(!reports.length){
      listEl.innerHTML = '<div class="empty">还没有报告，提交一个研究目标试试。</div>';
      return;
    }
    listEl.innerHTML = reports.map(r =>
      `<a class="card" href="/report/${encodeURIComponent(r.file)}">
         <h3>${r.name}</h3>
         <div class="meta">更新于 ${fmtDate(r.updated)}</div>
       </a>`).join("");
  }catch(e){
    listEl.innerHTML = '<div class="empty">加载失败：'+e.message+'</div>';
  }
}

form.addEventListener("submit", async (e)=>{
  e.preventDefault();
  const goal = input.value.trim();
  if(!goal){ statusEl.textContent = "请输入研究目标"; return; }
  statusEl.textContent = "此阶段暂未接入实时生成（P1 开放）；请在本地运行后端研究流水线。";
});

loadReports();
