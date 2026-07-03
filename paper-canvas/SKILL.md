---
name: paper-canvas
description: >
  Transforms academic paper/talk metadata into a beautiful, interactive, single-file HTML
  visualization page. Left-side tab nav, right-side panels with custom animation demos + deep-dive
  explanations, plus a "related companies" tab. Output is **fully self-contained, zero network
  dependencies** — works offline / behind GFW / on airplanes.
---

# Paper Canvas Skill

**约束：无外部依赖。** 所有样式内联 `<style>`，所有 JS 原生（vanilla JS + Canvas API）。
禁止任何 `<script src="...">`、`<link href="...">`、CDN、外链字体/图片。
系统字体栈 + emoji 图标 + inline SVG/data URI 没问题。

**L3 动画靠原生 Canvas + CSS，不内联第三方库。** vendor/ 目录下的 d3/katex/anime 文件已废弃，
不要再读取或内联它们。（之前 socket 断连就是因为内联 d3 280KB + katex 277KB 导致输出超量。）
如需公式渲染，手写 Unicode 数学符号或简化的 HTML 排版即可。

## Step 1 — Extract structured metadata

| Field | Example |
|-------|---------|
| `title` / `subtitle` | "Photonics for AI, AI for Photonics…" |
| `authors` | "Odile Liboiron-Ladouceur" |
| `institution` / `venue_short` / `venue_full` / `date` / `session_id` | "McGill University" / "OFC" / "OFC, LA" / "2026-03-16" / "M1G.6" |
| `content_summary` | full abstract |

If anything is missing, ask once.

## Step 2 — Decompose into modules

3–4 technical topics → each gets a nav tab (emoji + title + subtitle), an animation demo, and a deep-dive explanation. Plus a final **"Related Companies"** tab (always last).

## Step 2.5 — Design tokens

Pick one theme for `:root`:

```
A (Aurora) — optics/physics default: bg #0b0f1a→#131a2b, accent #8b5cf6+#06b6d4+#ec4899, radial-gradient mesh
B (Vercel) — AI/infra: bg #08090a→#0f1011, accent #5e6ad2+#00d4ff+#ff0080, conic-gradient + noise texture
```

**Visual effects (≥4)**:
1. Glassmorphism — `backdrop-filter: blur(20px) saturate(180%)`
2. Gradient mesh bg — `body::before` with gradient + floating keyframes
3. Noise — `body::after` SVG feTurbulence data URI (opacity 0.04)
4. Micro-interactions — card hover translateY(-2px), button active scale(0.97), panel enter cubic-bezier
5. Magnetic cursor — button mousemove follows cursor ×0.2
6. Scroll-triggered — IntersectionObserver + opacity/translateY transition
7. Mono fonts for all numbers/formulas — `--font-mono: ui-monospace, "SF Mono", Consolas`

## Step 3 — Design animations (vanilla JS + Canvas API, no libraries)

### 教学红线

目标读者：研究生通识水平（学过线代/概率，无领域背景）。每个动画必须满足：

1. **解决具体困惑** — 动画上方写 `❓ 你可能会问：……`
2. **有真实数字** — 小向量/矩阵（2-4维）走一遍计算，数值直接印在画面上
3. **分步骤可单步** — 3-6步，「下一步 ▶」「重置 ↺」按钮，每步配中文旁白
4. **对比 with/without** — 至少一个动画展示"不用某机制会怎样"
5. **直觉类比** — 抽象概念先用日常类比铺垫

### 动画模式

| 模式 | 场景 | 关键 |
|------|------|------|
| 数字逐步计算 | softmax/点积/归一化 | 中间结果数值 + 每步旁白 |
| 对比双视图 | with vs without | 左右并排同时跑 |
| 状态机分步 | 多阶段流程 | 步骤指示器 1/N |
| 热力图/权重表 | 注意力分布 | 格子内标数值 |
| 滑块互动 | 超参敏感性 | 拖动实时更新 |

### Canvas 模板（直接用，选 1-2 个）

**粒子系统** — 光子传播/数据流:
```js
const c = document.getElementById('cv'), ctx = c.getContext('2d');
const N = 80, ps = Array.from({length:N}, () => ({x:Math.random()*c.width, y:Math.random()*c.height, vx:(Math.random()-.5)*1.5, vy:(Math.random()-.5)*1.5, r:Math.random()*2+1, hue:250+Math.random()*60}));
function loop() {
  ctx.fillStyle = 'rgba(11,15,26,.15)'; ctx.fillRect(0,0,c.width,c.height);
  for (let i=0;i<N;i++) for (let j=i+1;j<N;j++){const d=Math.hypot(ps[i].x-ps[j].x,ps[i].y-ps[j].y);if(d<80){ctx.strokeStyle=`hsla(260,80%,70%,${1-d/80})`;ctx.lineWidth=.5;ctx.beginPath();ctx.moveTo(ps[i].x,ps[i].y);ctx.lineTo(ps[j].x,ps[j].y);ctx.stroke();}}
  ps.forEach(p => { p.x+=p.vx; p.y+=p.vy; if(p.x<0||p.x>c.width)p.vx*=-1; if(p.y<0||p.y>c.height)p.vy*=-1; ctx.fillStyle=`hsl(${p.hue},80%,70%)`; ctx.beginPath(); ctx.arc(p.x,p.y,p.r,0,Math.PI*2); ctx.fill(); });
  requestAnimationFrame(loop);
} loop();
```

**力导向图** — 知识图谱/注意力图:
```js
// 斥力 O(n²) + 边弹簧力 + 速度阻尼 0.85
for (let i=0;i<N;i++) for (let j=i+1;j<N;j++) { const dx=n[j].x-n[i].x, dy=n[j].y-n[i].y, d=Math.hypot(dx,dy)+.01, f=800/(d*d); n[i].vx-=f*dx/d; n[i].vy-=f*dy/d; n[j].vx+=f*dx/d; n[j].vy+=f*dy/d; }
edges.forEach(e => { const a=n[e.a], b=n[e.b]; const dx=b.x-a.x, dy=b.y-a.y, d=Math.hypot(dx,dy)+.01, f=(d-100)*.02; a.vx+=f*dx/d; a.vy+=f*dy/d; b.vx-=f*dx/d; b.vy-=f*dy/d; });
n.forEach(x => { x.vx*=.85; x.vy*=.85; x.x+=x.vx; x.y+=x.vy; });
```

**波形** — 光波/信号/傅里叶:
```js
let t=0; function loop() { ctx.clearRect(0,0,c.width,c.height); ctx.strokeStyle='#8b5cf6'; ctx.lineWidth=2; ctx.beginPath(); for (let x=0;x<c.width;x++){const y=c.height/2+Math.sin(x*.02+t)*40+Math.sin(x*.05+t*1.7)*20;x===0?ctx.moveTo(x,y):ctx.lineTo(x,y);} ctx.stroke(); t+=.04; requestAnimationFrame(loop); } loop();
```

**3D 伪透视** — 张量/立方体:
```js
const verts=[[-1,-1,-1],[1,-1,-1],[1,1,-1],[-1,1,-1],[-1,-1,1],[1,-1,1],[1,1,1],[-1,1,1]], edges=[[0,1],[1,2],[2,3],[3,0],[4,5],[5,6],[6,7],[7,4],[0,4],[1,5],[2,6],[3,7]]; let a=0;
function proj(v){let[x,y,z]=v;[x,z]=[x*Math.cos(a)-z*Math.sin(a),x*Math.sin(a)+z*Math.cos(a)];[y,z]=[y*Math.cos(a*.7)-z*Math.sin(a*.7),y*Math.sin(a*.7)+z*Math.cos(a*.7)];const f=200/(4+z);return[c.width/2+x*f,c.height/2+y*f];}
function loop(){ctx.clearRect(0,0,c.width,c.height);ctx.strokeStyle='#06b6d4';ctx.lineWidth=2;edges.forEach(([i,j])=>{const[x1,y1]=proj(verts[i]),[x2,y2]=proj(verts[j]);ctx.beginPath();ctx.moveTo(x1,y1);ctx.lineTo(x2,y2);ctx.stroke();});a+=.01;requestAnimationFrame(loop);} loop();
```

**规范**: IIFE 包裹每个 canvas，高 DPI `ctx.scale(devicePixelRatio)`，暗色背景用 `rgba(bg,.1)` 拖尾而非 clearRect。

每个动画下方必须配「👉 看到了什么」小结（2-3句），把动画现象翻译成论文概念。

## Step 4 — HTML structure

```html
<header class="header"> ← 深色底，标题左，作者卡片右
  <h1>title</h1><div class="subtitle">subtitle · venue · date</div>
  <div class="author-card"><div class="name">authors</div><div class="inst">institution</div></div>
</header>

<main>
  <nav class="tabs">  ← 竖排按钮，active 白底+左边框+scale(1.02)
    每个 tab: <button class="tab" data-tab="xxx"><span class="icon">📖</span><div><div class="ttl">标题</div><div class="sub">副标题</div></div></button>
    最后: <div class="tip">💡 操作提示...</div>
  </nav>

  <section class="content">
    <div class="panel" data-panel="intro">  ← 仅 intro 用 2-column .intro-grid
      左: 论文背景/动机, 右: 核心贡献
    </div>
    <!-- 每个 module 一个 panel -->
    <div class="panel" data-panel="module1">
      <div class="card"> ← demo: h2 + .demo-area(动画区) + .btn(触发)
      <div class="card"> ← deep-dive: h2「核心技术解析」+ 2段 + .highlight 框
    </div>
    <div class="panel" data-panel="companies">  ← 3-column .co-grid
      每列: .co-col.c1(紫)/.c2(蓝)/.c3(绿), 内含 2-4 个 .co-card(公司名+理由)
    </div>
  </section>
</main>

<script>
// Tab 切换
document.querySelectorAll('.tab').forEach(btn => {
  btn.addEventListener('click', () => {
    const id = btn.dataset.tab;
    document.querySelectorAll('.tab').forEach(t => t.classList.toggle('active', t === btn));
    document.querySelectorAll('.panel').forEach(p => p.classList.toggle('active', p.dataset.panel === id));
  });
});
// 各模块动画触发函数
</script>
```

**CSS 要点**: `.panel { display:none; } .panel.active { display:flex; }` + fadeIn keyframes.
Intro grid `grid-template-columns: 1fr 1fr`, companies grid `repeat(3,1fr)`.
响应式 `@media (max-width:900px)` 切单列。

不要加下载按钮——文件本身就是离线版本。

## Step 5 — Save file

命名: `{YYYYMMDD}_{VENUE_SHORT}_{SESSION_ID}_{FirstWords}.html`
保存到: `D:\大模型论文\`

## 自检清单

- [ ] 选了一套主题 token，实现了 ≥4 个视觉效果
- [ ] 数值/公式用了 mono 字体
- [ ] ≥2 个 tab 用了 Canvas 动画，有可见数字 label
- [ ] 每个动画有「下一步」「重置」+ «看到了什么» 小结
- [ ] 每个动画上方有 `❓` 引子
- [ ] 至少一个 with/without 对比
- [ ] 核心概念第一次出现配了白话类比
- [ ] 无任何 CDN/外链/import/require/JSX/p5/three
- [ ] 所有 tab 和 panel 的 data- 属性匹配

## 内容规范

全部中文解释。Deep-dive 每段 150-250 字。公司选真实企业。3 模块 + intro + 公司 = 5 tabs。
