"use strict";
const el = id => document.getElementById(id);
const input = el("text"), form = el("analysis"), button = el("submit");
const words = {
  tr: {online:"Çevrimiçi", model:"Model bilgisi", how:"Nasıl çalışır?", limits:"Sınırlamalar", privacy:"Gizlilik", contact:"İletişim", hero:"İnsan mı,<br><em>yapay zekâ mı?</em>", intro:"Türkçe veya İngilizce metnini analiz et ve modelin yazarlık tahminini gör.", editor:"Metin girişi", example:"Örnek metin", trExample:"Türkçe örnek", enExample:"İngilizce örnek", placeholder:"Metnini buraya yaz veya yapıştır…", upload:"Dosya yükle", clear:"Temizle", submit:"Metni analiz et", analyzing:"Analiz ediliyor…", result:"Analiz sonucu", score:"AI skoru / 100", waiting:"Metin bekleniyor", threshold:"Karar eşiği", inspected:"İncelenen metin", caveat:"Skor bir model tahminidir. Tek başına yazarlık kanıtı olarak kullanılmamalıdır.", privacyFoot:"Metin analiz için Hugging Face'e gönderilir.", lang:"EN", langLabel:"Switch to English", min:"En az {n} sözcük", count:"{n} sözcük", chars:"{n} / {max} karakter", fileTitle:"TXT, Markdown, PDF, Word, Excel veya PowerPoint yükle", drop:"veya dosyayı buraya bırak", copy:"Sonucu kopyala", copied:"Kopyalandı", modelIntro:", Türkçe ve İngilizce metinler için insan veya yapay zekâ tahmini üretir.", howText:"Metin nasıl incelenir?", howBody:"En az {n} sözcük gerekir. Model metnin tamamını sırayla, en çok 50 sözcüklük parçalar halinde inceler. Son parça kısa olsa da hesaba katılır. Her parçanın sonuçtaki ağırlığı sözcük sayısıyla orantılıdır.", scoreTitle:"Skor nasıl okunur?", scoreBody:"AI skoru karar eşiğine ulaştığında model “Yapay zekâ” etiketini seçer. Skor, yazarın AI kullanmış olma olasılığı olarak yorumlanmamalıdır.", styleTitle:"Üslup skoru nasıl destekler?", styleBody:"Üslup modeli cümle yapısını, sözcük çeşitliliğini ve tekrarı inceler.", errorsTitle:"Nerede yanılabilir?", errorsBody:"Model İngilizce akademik yazıları AI olarak işaretleyebilir. Günlük dilde ise bazı insan yorumlarını yanlış işaretleyebilir ve bazı AI yorumlarını kaçırabilir. Başarı, metnin türüne ve seçilen model sürümüne göre değişir.", human:"İnsan", ai:"Yapay zekâ", busy:"Model metni inceliyor…", failed:"Analiz tamamlanamadı", unavailable:"Sunucuya ulaşılamadı. Biraz sonra tekrar dene.", readFile:"Dosya okunuyor…", unsupported:"Bu dosya biçimi şu anda desteklenmiyor. TXT veya Markdown dosyası deneyebilirsin.", invalidFile:"TXT, Markdown, PDF, Word (.docx), Excel (.xlsx, .xls) veya PowerPoint (.pptx) dosyası seç.", tooLarge:"En fazla 100.000 karakter yüklenebilir.", tooBig:"Belge dosyaları en fazla {n} MB olabilir.", badEncoding:"Dosyayı UTF-8 olarak kaydedip yeniden dene.", cannotRead:"Belge okunamadı.", modelError:"Model ayarları okunamadı. Sayfayı yenileyip tekrar dene.", modelUnavailable:"Bu sürümde genel skoru ana model belirler.", stylePart:"Üslup modeli cümle yapısını, sözcük çeşitliliğini ve tekrarı inceler. Üslup skorunun genel skordaki ağırlığı %{n}. Yeterli sözcük bulunmadığında ana skor kullanılır.", pieces:"{n} parça · {w} sözcük", close:"Kapat", analyzingError:"Analiz tamamlanamadı."},
  en: {online:"Online", model:"About the model", how:"How it works", limits:"Limitations", privacy:"Privacy", contact:"Contact", hero:"Human,<br><em>or AI?</em>", intro:"Analyze text in Turkish or English and see the model’s authorship estimate.", editor:"Your text", example:"Sample text", trExample:"Turkish sample", enExample:"English sample", placeholder:"Type or paste your text here…", upload:"Upload file", clear:"Clear", submit:"Analyze text", analyzing:"Analyzing…", result:"Analysis result", score:"AI score / 100", waiting:"Waiting for text", threshold:"Decision threshold", inspected:"Text analyzed", caveat:"This score is a model estimate. It should not be used as proof of authorship on its own.", privacyFoot:"Text is sent to Hugging Face for analysis.", lang:"TR", langLabel:"Türkçeye geç", min:"At least {n} words", count:"{n} words", chars:"{n} / {max} characters", fileTitle:"Upload TXT, Markdown, PDF, Word, Excel, or PowerPoint", drop:"or drop a file here", copy:"Copy result", copied:"Copied", modelIntro:" estimates whether Turkish and English text was written by a person or AI.", howText:"How is the text analyzed?", howBody:"At least {n} words are required. The model processes the full text in order, in chunks of up to 50 words. A short final chunk is included. Each chunk is weighted by its word count.", scoreTitle:"What does the score mean?", scoreBody:"When the AI score reaches the decision threshold, the model labels the text “AI”. The score should not be read as the probability that the author used AI.", styleTitle:"How does style contribute?", styleBody:"The style model examines sentence structure, vocabulary variety, and repetition.", errorsTitle:"Where can it be wrong?", errorsBody:"The model may flag English academic writing as AI. It may also misclassify some informal human writing or miss some AI-written comments. Accuracy varies by text type and model version.", human:"Human", ai:"AI", busy:"The model is analyzing your text…", failed:"Analysis failed", unavailable:"Could not reach the server. Please try again shortly.", readFile:"Reading file…", unsupported:"This file type is not supported right now. Try a TXT or Markdown file.", invalidFile:"Choose a TXT, Markdown, PDF, Word (.docx), Excel (.xlsx, .xls), or PowerPoint (.pptx) file.", tooLarge:"Files can contain up to 100,000 characters.", tooBig:"Documents can be up to {n} MB.", badEncoding:"Save the file as UTF-8 and try again.", cannotRead:"Could not read the document.", modelError:"Could not load model settings. Refresh the page and try again.", modelUnavailable:"This version uses the main model for the overall score.", stylePart:"The style model examines sentence structure, vocabulary variety, and repetition. It contributes %{n} to the overall score. The main model is used when there are not enough words.", pieces:"{n} chunks · {w} words", close:"Close", analyzingError:"Analysis failed."}
};
const savedLanguage = localStorage.getItem("detector-language");
let lang = location.pathname==="/en"?"en":savedLanguage === "tr" || savedLanguage === "en" ? savedLanguage : (navigator.language || "en").toLowerCase().startsWith("tr") ? "tr" : "en";
const t = (key, values = {}) => Object.entries(values).reduce((s,[k,v])=>s.replaceAll("{"+k+"}",String(v)), words[lang][key] || words.tr[key] || key);
function language() {
  document.documentElement.lang = lang;
  document.title = lang === "en" ? "AI Text Detector · Analysis" : "Metin Dedektörü · Analiz";
  const description=document.querySelector('meta[name="description"]');if(description)description.content=lang==="en"?"Free AI text detector for English and Turkish. Analyze writing patterns in text of 50 words or more. Results are estimates, not proof.":"Türkçe ve İngilizce metinleri analiz ederek yapay zekâ yazımı tahmini alın. Ücretsiz çevrimiçi AI metin dedektörü; sonuçlar yalnızca tahmindir.";
  const canonical=document.querySelector('link[rel="canonical"]');if(canonical)canonical.href=`https://ai-text-detector-eng-tr.vercel.app${lang==="en"?"/en":"/"}`;
  const ogTitle=document.querySelector('meta[property="og:title"]');if(ogTitle)ogTitle.content=lang==="en"?"Free AI Text Detector for Turkish and English":"Türkçe ve İngilizce AI Metin Dedektörü";
  const ogDescription=document.querySelector('meta[property="og:description"]');if(ogDescription)ogDescription.content=description?.content||"";
  const ogUrl=document.querySelector('meta[property="og:url"]');if(ogUrl)ogUrl.content=`https://ai-text-detector-eng-tr.vercel.app${lang==="en"?"/en":"/"}`;
  const set=(id,value)=>{const node=el(id);if(node)node.textContent=value;};
  set("online-label",t("online"));set("model-link-label",t("model"));set("examples-label",t("example"));set("upload-label",t("upload"));set("clear-label",t("clear"));set("submit-label",busy?t("analyzing"):t("submit"));set("output-heading",t("result"));set("hero-heading","");el("hero-heading").innerHTML=t("hero");
  el("hero-heading").nextElementSibling.textContent=t("intro");el("text").placeholder=t("placeholder");el("text-label").textContent=lang==="en"?"Text to analyze":"Analiz edilecek metin";
  el("seo-copy").setAttribute("aria-label",lang==="en"?"About the tool":"Araç hakkında");
  el("seo-copy").innerHTML=lang==="en"
    ? '<h2>Free AI text detector for Turkish and English</h2><p>Analyze Turkish and English writing for patterns associated with AI-generated text. The tool accepts text with at least 50 words and reports a model score as an estimate.</p><p>AI detection is not conclusive. Do not use a score alone as proof of authorship. Learn <a href="/en/how-it-works">how the detector works</a> and read its <a href="/en/limitations">limitations</a>.</p>'
    : '<h2>Türkçe ve İngilizce AI metin dedektörü</h2><p>Metin Dedektörü, Türkçe ve İngilizce yazılardaki yapay zekâ üretimine benzer örüntüleri inceler. En az 50 sözcük içeren metinleri analiz eder ve model skorunu tahmin olarak sunar.</p><p>AI yazım tespiti kesin sonuç vermez. Skoru tek başına yazarlık kanıtı olarak kullanma; aracın <a href="/nasil-calisir">nasıl çalıştığını</a> ve <a href="/sinirlamalar">sınırlamalarını</a> incele.</p>';
  el("sample-menu").querySelector('[data-example="tr"]').textContent=t("trExample");el("sample-menu").querySelector('[data-example="en"]').textContent=t("enExample");
  el("file").previousElementSibling.title=t("fileTitle");set("drop-hint",t("drop"));set("copy-result",t("copy"));el("copy-result").setAttribute("aria-label",t("copy"));
  const paths={"/nasil-calisir":"/en/how-it-works","/sinirlamalar":"/en/limitations","/gizlilik":"/en/privacy","/iletisim":"/en/contact"};
  const headings=document.querySelectorAll(".site-nav a,.footer-nav a");for(const a of headings){const tr=a.dataset.trHref||a.getAttribute("href");a.dataset.trHref=tr;const key={"/nasil-calisir":"how","/sinirlamalar":"limits","/gizlilik":"privacy","/iletisim":"contact"}[tr];if(key){a.textContent=t(key);a.href=lang==="en"?paths[tr]:tr;}}
  el("language-toggle").dataset.current=lang;el("language-toggle").setAttribute("aria-label","Language / Dil");
  for(const option of el("language-toggle").querySelectorAll("[data-lang-option]"))option.dataset.active=String(option.dataset.langOption===lang);
  el("score").nextElementSibling.textContent=t("score");el("verdict").querySelector("span").textContent=el("score").textContent==="—"?t("waiting"):el("verdict").dataset.state==="ai"?t("ai"):t("human");
  const detailLabels=el("threshold").parentElement.parentElement.querySelectorAll("span");detailLabels[0].textContent=t("threshold");detailLabels[1].textContent=t("inspected");el("caveat").querySelector("p").textContent=t("caveat");document.querySelector("footer > span").lastChild.textContent=t("privacyFoot");
  for(const [i,a] of [...document.querySelectorAll(".site-nav a")].entries()) {a.setAttribute("aria-label",a.textContent);}
  for(const [selector,value] of [[".heading h2",t("editor")]]) document.querySelector(selector).textContent=value;
  const info=el("info");info.querySelector(".dialog-head h2").textContent=t("model");el("close-info").setAttribute("aria-label",t("close"));
  const paras=info.querySelectorAll("p"), hs=info.querySelectorAll("h3");
  hs[0].textContent=t("howText");hs[1].textContent=t("scoreTitle");hs[2].textContent=t("styleTitle");hs[3].textContent=t("errorsTitle");
  paras[0].textContent=(el("info-model").textContent|| (lang==="en"?"Local detector":"Yerel dedektör"))+t("modelIntro");paras[1].textContent=t("howBody",{n:settings?.min_words||50});paras[2].textContent=t("scoreBody");
  if(typeof settings?.style_weight==="number")paras[3].textContent=settings.style_weight?t("stylePart",{n:number(settings.style_weight*100)}):t("modelUnavailable");else paras[3].textContent=t("styleBody");paras[4].textContent=t("errorsBody");
  sync();
}
el("language-toggle").onclick=()=>{const next=lang==="tr"?"en":"tr";localStorage.setItem("detector-language",next);location.href=next==="en"?"/en":"/";};
let settings = null, busy = false, loadedFile = 0, lastResult = null;
const samples = {
  tr: "Geçen hafta işe giderken her sabah önünden geçtiğim parkta kısa bir yürüyüş yapmaya karar verdim. Normalde otobüse yetişmek için hızlı adımlarla yürürdüm. Bu kez biraz erken çıktığım için banklardan birine oturdum ve çevremde olup bitenleri izledim. Birkaç dakika sonra aynı yolu kullanan insanların çoğunun da benim gibi acele ettiğini fark ettim. Ertesi sabah yanımda bir kitap götürdüm ve otobüs gelene kadar birkaç sayfa okudum.",
  en: "I took a different route to the station yesterday because the main road was closed. There was a small bakery on the corner that I had never noticed before. I stopped for a loaf of bread and ended up talking to the owner about the neighborhood. By the time I reached the platform, I had missed my usual train, but I had also found somewhere I would like to visit again."
};
const number = value => new Intl.NumberFormat(lang==="en"?"en-US":"tr-TR", {maximumFractionDigits: 1}).format(value);
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
  el("counter").textContent = t("count",{n:number(words)});
  el("char-counter").textContent=t("chars",{n:number(input.value.length),max:number(settings?.max_chars??100000)});
  el("char-counter").classList.toggle("over-limit",input.value.length>(settings?.max_chars??100000)*.95);
  button.disabled = busy || !settings || words < settings.min_words;
  el("clear").disabled = busy || !input.value;
  el("upload").disabled = busy;
  el("examples").disabled = busy;
  input.readOnly = busy;
  el("submit-label").textContent = busy ? t("analyzing") : t("submit");
}
function resetResult() {
  el("score").textContent = "—"; el("pieces").textContent = "—";
  verdict(t("waiting")); drawDial(); message(); sync(); el("copy-result").disabled=true;lastResult=null;
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
    throw new Error(t("invalidFile"));
  }
  if (!["txt", "md", "markdown"].includes(extension)) {
    const restartMessage = t("unsupported");
    if (settings && !settings.document_extensions?.includes("." + extension)) throw new Error(restartMessage);
    const maxBytes = settings?.max_document_bytes ?? 20 * 1024 * 1024;
    if (file.size > maxBytes) throw new Error(t("tooBig",{n:Math.floor(maxBytes / 1024 / 1024)}));
    const response = await fetch("/api/extract/" + extension, {method: "POST", body: file});
    if (response.status === 404) throw new Error(restartMessage);
    const data = await response.json();
    if (!response.ok) throw new Error(data.error || data.detail || t("cannotRead"));
    return data.text;
  }
  if (file.size > limit * 4 + 3) throw new Error(t("tooLarge"));
  const bytes = await file.arrayBuffer();
  try {
    return new TextDecoder("utf-8", {fatal: true}).decode(bytes);
  } catch {
    throw new Error(t("badEncoding"));
  }
}
el("file").onchange = async () => {
  const file=el("file").files[0]; el("file").value="";
  if(!file || busy) return;
  const seq=++loadedFile;
  message(t("readFile"));
  button.disabled=true;
  try {
    const limit=settings?.max_chars ?? input.maxLength;
    const text=await readUpload(file, limit);
    if(text.length>limit) throw new Error(t("tooLarge"));
    if(seq!==loadedFile || busy) return;
    input.value=text; resetResult(); input.focus();
  } catch(err) {
    if(seq===loadedFile) {
      message(err instanceof TypeError ? "Sunucuya ulaşılamadı. Biraz sonra tekrar dene." : err.message);
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
    const response=await fetch("/api/analyze",{method:"POST",headers:{"Content-Type":"application/json","Accept-Language":lang},body:JSON.stringify({text:input.value})});
    const data=await response.json();
    if(!response.ok) throw new Error(data.error || data.detail || "Analiz tamamlanamadı.");
    lastResult=data;el("copy-result").disabled=false;
    el("score").textContent=number(data.ai_score*100);
    el("pieces").textContent=t("pieces",{n:number(data.windows),w:number(data.word_count)});
    el("threshold").textContent=number(data.threshold*100)+" / 100";
    verdict(data.label==="AI" ? t("ai") : t("human"), data.label==="AI" ? "ai" : "human");
    drawDial(data.ai_score);
    if(matchMedia("(max-width:800px)").matches) el("output").scrollIntoView({block:"nearest"});
  } catch(err) {
    el("score").textContent="—"; verdict(t("failed"));
    message(err instanceof TypeError ? t("unavailable") : err.message);
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
    const name=settings.name;
    el("output-heading").textContent="Analiz sonucu";
    if (typeof settings.style_weight === "number") {
    el("info-style").textContent=settings.style_weight > 0
        ? t("stylePart",{n:number(settings.style_weight*100)}) : t("modelUnavailable");
    }
    el("hero-model").textContent=name;el("hero-model").hidden=false;el("info-model").textContent=name;
    el("minimum").textContent=t("min",{n:number(settings.min_words)});input.maxLength=settings.max_chars;
    el("threshold").textContent=number(settings.threshold*100)+" / 100";
    drawDial();sync();
  } catch {message(t("modelError"));}
  language();
})();

if(!savedLanguage&&location.pathname!=="/en"){
  fetch("/api/locale").then(r=>r.ok?r.json():null).then(data=>{
    if(data?.language==="tr"||data?.language==="en"){lang=data.language;language();if(lang==="en")history.replaceState(null,"","/en");}
  }).catch(()=>{});
}

el("copy-result").onclick=async()=>{
  if(!lastResult)return;
  const report=`${t("result")}\n${t("score")}: ${number(lastResult.ai_score*100)}\n${t("threshold")}: ${number(lastResult.threshold*100)} / 100\n${t("inspected")}: ${t("pieces",{n:number(lastResult.windows),w:number(lastResult.word_count)})}\n${t("human")} / ${t("ai")}: ${lastResult.label==="AI"?t("ai"):t("human")}`;
  try{await navigator.clipboard.writeText(report);const b=el("copy-result");b.textContent=t("copied");setTimeout(()=>{if(lastResult)b.textContent=t("copy");},1600);}catch{message(lang==="en"?"Clipboard access is unavailable in this browser.":"Bu tarayıcı panoya erişime izin vermiyor.");}
};

const surface=document.querySelector(".writing-surface");
for(const event of ["dragenter","dragover"])surface.addEventListener(event,e=>{e.preventDefault();if(!busy)surface.classList.add("dragging");});
for(const event of ["dragleave","drop"])surface.addEventListener(event,e=>{e.preventDefault();surface.classList.remove("dragging");});
surface.addEventListener("drop",e=>{if(busy)return;const file=e.dataTransfer.files[0];if(file){const transfer=new DataTransfer();transfer.items.add(file);el("file").files=transfer.files;el("file").dispatchEvent(new Event("change"));}});
