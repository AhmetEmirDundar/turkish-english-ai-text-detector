"use strict";
const el = id => document.getElementById(id);
const input = el("text"), form = el("analysis"), button = el("submit");
let settings = null, busy = false, loadedFile = 0;
const samples = {
  tr: "Geçen hafta işe giderken her sabah önünden geçtiğim parkta kısa bir yürüyüş yapmaya karar verdim. Normalde otobüse yetişmek için hızlı adımlarla yürürdüm. Bu kez biraz erken çıktığım için banklardan birine oturdum ve çevremde olup bitenleri izledim. Birkaç dakika sonra aynı yolu kullanan insanların çoğunun da benim gibi acele ettiğini fark ettim. Ertesi sabah yanımda bir kitap götürdüm ve otobüs gelene kadar birkaç sayfa okudum.",
  en: "I took a different route to the station yesterday because the main road was closed. There was a small bakery on the corner that I had never noticed before. I stopped for a loaf of bread and ended up talking to the owner about the neighborhood. By the time I reached the platform, I had missed my usual train, but I had also found somewhere I would like to visit again."
};
const number = value => new Intl.NumberFormat("tr-TR", {maximumFractionDigits: 1}).format(value);
function message(text = "") {
  el("message").textContent = text;
  el("message").hidden = !text;
}
function verdict(text, state = "") {
  el("verdict").querySelector("span").textContent = text;
  el("verdict").dataset.state = state;
}
function drawDial(score = null) {
  const dial = el("dial"), svgNS = "http://www.w3.org/2000/svg";
  dial.replaceChildren();
  function point(value, radius) {
    const angle = Math.PI * (1 - value);
    return [120 + radius * Math.cos(angle), 115 - radius * Math.sin(angle)];
  }
  function line(value, inner, outer, color, width) {
    const item = document.createElementNS(svgNS, "line");
    const [x1, y1] = point(value, inner), [x2, y2] = point(value, outer);
    for (const [attr, val] of Object.entries({x1,y1,x2,y2,stroke:color,"stroke-width":width,"stroke-linecap":"round"})) item.setAttribute(attr,val);
    dial.append(item);
  }
  for (let i=0;i<43;i++) {
    const value = i/42;
    line(value,87,102,score !== null && value <= score ? "#7858d9" : "#dfdbe9",3.4);
  }
  if (settings) line(settings.threshold,105,111,"#51465f",2);
  for (const [x,label] of [[18,"0"],[222,"100"]]) {
    const t=document.createElementNS(svgNS,"text");
    t.setAttribute("x",x); t.setAttribute("y",131); t.setAttribute("text-anchor","middle");
    t.setAttribute("font-size","10"); t.setAttribute("fill","#746e80"); t.textContent=label;
    dial.append(t);
  }
}
function sync() {
  const words = input.value.trim() ? input.value.trim().split(/\s+/u).length : 0;
  el("counter").textContent = number(words) + " sözcük";
  button.disabled = busy || !settings || words < settings.min_words;
  el("clear").disabled = busy || !input.value;
  el("upload").disabled = busy;
  el("examples").disabled = busy;
  input.readOnly = busy;
  button.querySelector("span").textContent = busy ? "Analiz ediliyor…" : "Metni analiz et";
}
function resetResult() {
  el("score").textContent = "—"; el("pieces").textContent = "—";
  verdict("Metin bekleniyor"); drawDial(); message(); sync();
}
function closeMenu() {el("sample-menu").hidden=true;el("examples").setAttribute("aria-expanded","false");}
el("examples").onclick = () => {
  const opened=el("sample-menu").hidden;
  el("sample-menu").hidden=!opened; el("examples").setAttribute("aria-expanded",String(opened));
  if(opened) el("sample-menu").querySelector("button").focus();
};
document.addEventListener("click", e => {if(!e.target.closest(".example-wrap")) closeMenu();});
document.addEventListener("keydown", e => {
  if(e.key==="Escape" && !el("sample-menu").hidden) {closeMenu();el("examples").focus();}
});
el("sample-menu").onclick = e => {
  const option=e.target.closest("[data-example]");
  if(!option || busy) return;
  loadedFile++;input.value=samples[option.dataset.example];closeMenu();resetResult();input.focus();
};
input.oninput = () => {loadedFile++;resetResult();};
el("clear").onclick = () => {loadedFile++; input.value=""; resetResult(); input.focus();};
el("upload").onclick = () => el("file").click();
async function readUpload(file, limit) {
  const extension = file.name.split(".").pop().toLowerCase();
  if (!file.name.includes(".") || !el("file").accept.split(",").includes("." + extension)) {
    throw new Error("TXT, Markdown, PDF, Word (.docx), Excel (.xlsx, .xls) veya PowerPoint (.pptx) dosyası seç.");
  }
  if (!["txt", "md", "markdown"].includes(extension)) {
    const restartMessage = "Açık sunucu bu dosya biçimini desteklemiyor. Eski sunucuyu kapat, güncel app.py dosyasını çalıştır ve sayfayı yenile.";
    if (settings && !settings.document_extensions?.includes("." + extension)) throw new Error(restartMessage);
    if (file.size > 20 * 1024 * 1024) throw new Error("Belge dosyaları en fazla 20 MB olabilir.");
    const response = await fetch("/api/extract/" + extension, {method: "POST", body: file});
    if (response.status === 404) throw new Error(restartMessage);
    const data = await response.json();
    if (!response.ok) throw new Error(data.error);
    return data.text;
  }
  if (file.size > limit * 4 + 3) throw new Error("En fazla 100.000 karakter yüklenebilir.");
  const bytes = await file.arrayBuffer();
  try {
    return new TextDecoder("utf-8", {fatal: true}).decode(bytes);
  } catch {
    throw new Error("Dosyayı UTF-8 olarak kaydedip yeniden dene.");
  }
}
el("file").onchange = async () => {
  const file=el("file").files[0]; el("file").value="";
  if(!file || busy) return;
  const seq=++loadedFile;
  message("Dosya okunuyor…");
  button.disabled=true;
  try {
    const limit=settings?.max_chars ?? input.maxLength;
    const text=await readUpload(file, limit);
    if(text.length>limit) throw new Error("En fazla 100.000 karakter yüklenebilir.");
    if(seq!==loadedFile || busy) return;
    input.value=text; resetResult(); input.focus();
  } catch(err) {
    if(seq===loadedFile) {
      message(err instanceof TypeError ? "Yerel sunucuya ulaşılamadı. Sunucuyu kontrol edip tekrar dene." : err.message);
      sync();
    }
  }
};
form.onsubmit = async e => {
  e.preventDefault();
  if(button.disabled) return;
  loadedFile++;busy=true;closeMenu();message();sync();
  el("output").setAttribute("aria-busy","true");
  el("score").textContent="…"; el("pieces").textContent="—";drawDial();
  verdict("Model metni inceliyor…","busy");
  try {
    const response=await fetch("/api/analyze",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({text:input.value})});
    const data=await response.json();
    if(!response.ok) throw new Error(data.error);
    el("score").textContent=number(data.ai_score*100);
    el("pieces").textContent=number(data.windows)+" parça · "+number(data.word_count)+" sözcük";
    el("threshold").textContent=number(data.threshold*100)+" / 100";
    verdict(data.label==="AI" ? "Yapay zekâ" : "İnsan", data.label==="AI" ? "ai" : "human");
    drawDial(data.ai_score);
    if(matchMedia("(max-width:800px)").matches) el("output").scrollIntoView({block:"nearest"});
  } catch(err) {
    el("score").textContent="—"; verdict("Analiz tamamlanamadı");
    message(err instanceof TypeError ? "Yerel sunucuya ulaşılamadı. Sunucuyu başlatıp tekrar dene." : err.message);
  } finally {busy=false;el("output").removeAttribute("aria-busy");sync();}
};
const dialog=el("info");
el("open-info").onclick=()=>dialog.showModal();
el("close-info").onclick=()=>dialog.close();
dialog.addEventListener("click",e=>{if(e.target===dialog && (e.offsetX<0 || e.offsetX>dialog.clientWidth || e.offsetY<0 || e.offsetY>dialog.clientHeight)) dialog.close();});

// A static signal surface, independent of the user's text and the model score.
function drawSignal() {
  const canvas=el("signal"), {width:w,height:h}=canvas.getBoundingClientRect();
  const ratio=Math.min(devicePixelRatio||1,2), ctx=canvas.getContext("2d");
  if(!ctx || !w) return;
  canvas.width=Math.round(w*ratio);canvas.height=Math.round(h*ratio);ctx.scale(ratio,ratio);
  const compact=w<580, center=w*(compact?.96:.76), span=w*(compact?.49:.28);
  const mesh=ctx.createLinearGradient(center-span,0,center+span,0);
  mesh.addColorStop(0,"rgba(154,121,234,.08)");mesh.addColorStop(.32,"rgba(189,158,255,.87)");
  mesh.addColorStop(.68,"rgba(223,193,255,.99)");mesh.addColorStop(1,"rgba(161,121,239,.36)");
  ctx.globalAlpha=compact?.59:1;
  ctx.fillStyle="rgba(190,164,228,.18)";
  for(let x=w*.47;x<w;x+=14) for(let y=10;y<h;y+=14) ctx.fillRect(x,y,1,1);
  function coord(u,v) {
    const envelope=Math.exp(-u*u*1.7);
    const wave=Math.sin(u*4.65+v*1.7)*envelope*(.62+.3*Math.cos(v*2.6));
    return [center+span*(u+.18*v),h*(.56+.18*v-.095*u-.55*wave)];
  }
  ctx.strokeStyle=mesh;ctx.lineWidth=.95;
  for(let j=0;j<=64;j++) {
    const v=j/32-1;ctx.beginPath();
    for(let i=0;i<=140;i++) {const [x,y]=coord(i/70-1,v);i?ctx.lineTo(x,y):ctx.moveTo(x,y);}
    ctx.stroke();
  }
  ctx.globalAlpha*=.27;ctx.lineWidth=.65;
  for(let i=0;i<=58;i++) {
    const u=i/29-1;ctx.beginPath();
    for(let j=0;j<=60;j++) {const [x,y]=coord(u,j/30-1);j?ctx.lineTo(x,y):ctx.moveTo(x,y);}
    ctx.stroke();
  }
}
new ResizeObserver(drawSignal).observe(el("signal"));
drawDial();sync();
(async()=>{
  try {
    const res=await fetch("/api/model"); if(!res.ok) throw new Error();
    settings=await res.json();
    const name=settings.name+" · "+settings.version;
    el("hero-model").textContent=name;el("hero-model").hidden=false;el("info-model").textContent=name;
    el("minimum").textContent="En az "+settings.min_words+" sözcük";input.maxLength=settings.max_chars;
    el("threshold").textContent=number(settings.threshold*100)+" / 100";
    drawDial();sync();
  } catch {message("Model ayarları okunamadı. Yerel sunucuyu kontrol edip sayfayı yenile.");}
})();
