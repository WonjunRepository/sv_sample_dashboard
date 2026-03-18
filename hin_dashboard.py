"""
세븐일레븐 동적 지식 그래프(HIN) 대시보드 v3
내부 원형(dot) / 외부 사각형(square) — 호버 하이라이트 — 임원 보고용
"""

import streamlit as st
import streamlit.components.v1 as components
from pyvis.network import Network
import pandas as pd
import os

# ───────────────────────────────────────────
# 페이지 설정
# ───────────────────────────────────────────
st.set_page_config(
    page_title="세븐일레븐 HIN 대시보드",
    page_icon="🏪",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ───────────────────────────────────────────
# 컬러 팔레트
# ───────────────────────────────────────────
NODE_COLOR_MAP = {
    "상품명":    {"color": "#FFFFFF", "font_color": "#111111"},   # 핵심 상품 — 흰색
    "카테고리":  {"color": "#000080", "font_color": "#FFFFFF"},   # 딥 네이비
    "원재료":    {"color": "#FF00FF", "font_color": "#FFFFFF"},
    "인플루언서": {"color": "#ED1C24", "font_color": "#FFFFFF"},
    "시간":      {"color": "#F58220", "font_color": "#FFFFFF"},
    "IP/브랜드": {"color": "#00A651", "font_color": "#FFFFFF"},
    "후기/특성": {"color": "#00AEEF", "font_color": "#FFFFFF"},
}

# 소스별 형태: 내부=dot / 외부=square / 공통=dot
SOURCE_SHAPE_MAP = {
    "내부": {"shape": "dot",    "borderWidth": 2},
    "외부": {"shape": "square", "borderWidth": 3},
    "공통": {"shape": "dot",    "borderWidth": 4},
}

TYPE_KO = {
    "상품명":    "상품명 (Product Name)",
    "카테고리":  "카테고리 (Category)",
    "원재료":    "원재료 (Ingredient)",
    "인플루언서": "인플루언서 (Influencer)",
    "시간":      "시간 (Time)",
    "IP/브랜드": "IP/브랜드 (IP/Brand)",
    "후기/특성": "후기/특성 (Review)",
}

# 물리 설정 고정값 (UI 슬라이더 제거)
GRAVITY = -2500
SPRING_LEN = 170
NODE_SIZE = 30

# ───────────────────────────────────────────
# 글로벌 CSS
# ───────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@300;400;600;700;900&family=Inter:wght@300;400;600;700&display=swap');

html, body, [class*="css"] { font-family: 'Noto Sans KR', 'Inter', sans-serif; }

[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #0a0a18 0%, #0e0e22 100%);
    border-right: 1px solid rgba(255,255,255,0.06);
}
[data-testid="stSidebar"] * { color: #dde0f0 !important; }

.stApp { background: radial-gradient(ellipse at 20% 10%, #0d0d2e 0%, #060610 55%, #0a0a1c 100%); }

/* ── 헤더 ── */
.db-header {
    background: linear-gradient(130deg, #005730 0%, #007A40 50%, #004D28 100%);
    border-radius: 18px;
    padding: 24px 36px;
    margin-bottom: 20px;
    display: flex; align-items: center; gap: 20px;
    box-shadow: 0 8px 36px rgba(0,120,60,0.4);
    border: 1px solid rgba(255,255,255,0.08);
}
.db-header h1 { color:#fff !important; font-size:1.65rem !important; font-weight:800 !important; margin:0 !important; text-shadow:0 2px 10px rgba(0,0,0,0.5); }
.db-header .sub { color:rgba(255,255,255,0.78); font-size:0.84rem; margin-top:5px; }

/* ── 배지 ── */
.badge { display:inline-block; padding:3px 11px; border-radius:20px; font-size:0.72rem; font-weight:700; margin:0 3px; }
.b-in  { background:rgba(0,166,81,0.2);  color:#00d67a; border:1px solid #00A651; }
.b-out { background:rgba(237,28,36,0.2); color:#FF7070; border:1px solid #ED1C24; }
.b-com { background:rgba(255,215,0,0.2); color:#FFD700; border:1px solid #FFD700; }

/* ── 통계 카드 ── */
.s-card { background:rgba(255,255,255,0.046); border:1px solid rgba(255,255,255,0.09); border-radius:14px; padding:15px 12px; text-align:center; }
.s-num  { font-size:1.9rem; font-weight:800; }
.s-lbl  { font-size:0.72rem; color:rgba(255,255,255,0.56); margin-top:3px; }

/* ── 인사이트 카드 ── */
.ins { border-radius:0 14px 14px 0; padding:13px 17px; margin:10px 0; font-size:0.83rem; line-height:1.72; }

/* ── 형태 범례 ── */
.shape-box { background:rgba(255,255,255,0.04); border-radius:10px; padding:12px 15px; font-size:0.79rem; color:#bbb; }
.shape-box table { width:100%; border-collapse:collapse; }
.shape-box td { padding:5px 6px; }
.shape-box tr:not(:last-child) td { border-bottom:1px solid rgba(255,255,255,0.06); }

hr { border-color:rgba(255,255,255,0.09) !important; }
.block-container { padding-top:1.4rem !important; }
</style>
""", unsafe_allow_html=True)

# ───────────────────────────────────────────
# 데이터
# ───────────────────────────────────────────
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

@st.cache_data
def load_data():
    n = pd.read_csv(os.path.join(BASE_DIR, "network_nodes.csv"))
    e = pd.read_csv(os.path.join(BASE_DIR, "network_edges.csv"))
    return n, e

nodes_df, edges_df = load_data()
all_types = list(NODE_COLOR_MAP.keys())

# ───────────────────────────────────────────
# 사이드바
# ───────────────────────────────────────────
with st.sidebar:
    # ── 타입별 색상 (최상단) ──
    st.markdown("#### 타입별 색상")
    for t, info in NODE_COLOR_MAP.items():
        st.markdown(
            f'<div style="display:flex;align-items:center;gap:8px;margin:4px 0;">'
            f'<div style="width:13px;height:13px;border-radius:3px;background:{info["color"]};flex-shrink:0;border:1px solid rgba(255,255,255,0.3)"></div>'
            f'<span style="color:{info["color"]};font-size:0.8rem;font-weight:600">{t}</span></div>',
            unsafe_allow_html=True,
        )

    st.markdown("---")
    st.markdown("#### 노드 형태 안내")
    st.markdown("""
    <div class="shape-box">
      <table>
        <tr><td>●</td><td><span class="badge b-in">내부</span> 원형 dot</td></tr>
        <tr><td>■</td><td><span class="badge b-out">외부</span> 사각형 square</td></tr>
        <tr><td>⬤</td><td><span class="badge b-com">공통</span> 원형 (굵은 테두리)</td></tr>
      </table>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("## 🔍 데이터 소스 필터")

    show_internal = st.checkbox("● 내부 데이터 (원형)", value=True)
    show_external = st.checkbox("■ 외부 트렌드 (사각형)", value=True)
    show_common   = st.checkbox("⬤ 공통 브릿지 노드", value=True)

    st.markdown("---")
    st.markdown("#### 노드 검색")
    search_term = st.text_input("", placeholder="예: 스포츠, K리그…", label_visibility="collapsed")

    st.markdown("#### 노드 타입 필터")
    selected_types = []
    for t in all_types:
        if st.checkbox(TYPE_KO[t], value=True, key=f"chk_{t}"):
            selected_types.append(t)

    st.markdown("---")
    st.caption("© 2026 경희대학교 캡스톤디자인\n세븐일레븐 산학협력 B팀")

# ───────────────────────────────────────────
# 필터링
# ───────────────────────────────────────────
active_sources = []
if show_internal: active_sources.append("내부")
if show_external: active_sources.append("외부")
if show_common:   active_sources.append("공통")

filtered_nodes = nodes_df[
    nodes_df["type"].isin(selected_types) &
    nodes_df["source"].isin(active_sources)
].copy()

if search_term.strip():
    filtered_nodes = filtered_nodes[
        filtered_nodes["label"].str.contains(search_term.strip(), case=False, na=False)
    ]

visible_labels = set(filtered_nodes["label"].tolist())
filtered_edges = edges_df[
    edges_df["from"].isin(visible_labels) & edges_df["to"].isin(visible_labels)
]

# ───────────────────────────────────────────
# 헤더
# ───────────────────────────────────────────
st.markdown("""
<div class="db-header">
  <span style="font-size:2.6rem">🏪</span>
  <div>
    <h1>세븐일레븐 지식 그래프 기반 트렌드 분석 대시보드 v3</h1>
    <div class="sub">
      <span class="badge b-in">● 내부 원형</span>
      <span class="badge b-out">■ 외부 사각형</span>
      <span class="badge b-com">⬤ 공통 브릿지</span>
      &nbsp;·&nbsp; 호버 하이라이트 활성화 &nbsp;·&nbsp; LLM-RAG 기반 상품 기획 지원 시스템
    </div>
  </div>
</div>
""", unsafe_allow_html=True)

# ───────────────────────────────────────────
# 통계 카드 (5개)
# ───────────────────────────────────────────
n_in  = len(filtered_nodes[filtered_nodes["source"]=="내부"])
n_out = len(filtered_nodes[filtered_nodes["source"]=="외부"])
n_com = len(filtered_nodes[filtered_nodes["source"]=="공통"])
n_hub = len([x for x in ["스포츠"] if x in visible_labels])

cols = st.columns(5)
for col, (num, clr, lbl) in zip(cols, [
    (len(filtered_nodes), "#00d67a", "표시 노드"),
    (len(filtered_edges), "#00AEEF", "표시 엣지"),
    (n_in,                "#00A651", "내부 노드"),
    (n_out,               "#ED1C24", "외부 노드"),
    (n_hub,               "#FFD700", "브릿지 허브"),
]):
    with col:
        st.markdown(f'<div class="s-card"><div class="s-num" style="color:{clr}">{num}</div><div class="s-lbl">{lbl}</div></div>', unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# ───────────────────────────────────────────
# Pyvis 그래프 빌더 (v3)
# ───────────────────────────────────────────
def build_graph(nodes: pd.DataFrame, edges: pd.DataFrame) -> str:
    gravity, spring_len, node_size = GRAVITY, SPRING_LEN, NODE_SIZE

    net = Network(height="720px", width="100%",
                  bgcolor="#08080e", font_color="#ffffff",
                  directed=False, notebook=False)

    net.set_options(f"""
    {{
      "nodes": {{
        "shadow": {{"enabled": true, "size": 16, "x": 3, "y": 4}},
        "font": {{
          "size": 13,
          "face": "Noto Sans KR",
          "strokeWidth": 2,
          "strokeColor": "#000000"
        }}
      }},
      "edges": {{
        "width": 2,
        "smooth": {{"type": "dynamic"}},
        "shadow": {{"enabled": true}},
        "color": {{
          "color": "rgba(170,170,210,0.38)",
          "highlight": "#00d67a",
          "hover": "#FFD700",
          "opacity": 1.0
        }}
      }},
      "physics": {{
        "enabled": true,
        "barnesHut": {{
          "gravitationalConstant": {gravity},
          "springLength": {spring_len},
          "springConstant": 0.035,
          "damping": 0.14,
          "avoidOverlap": 0.75
        }},
        "stabilization": {{"enabled": true, "iterations": 300, "updateInterval": 20}}
      }},
      "interaction": {{
        "hover": true,
        "hoverConnectedEdges": true,
        "selectConnectedEdges": true,
        "dragNodes": true,
        "zoomView": true,
        "tooltipDelay": 100,
        "multiselect": true,
        "navigationButtons": false,
        "keyboard": {{"enabled": true}}
      }}
    }}
    """)

    for _, row in nodes.iterrows():
        ntype   = row["type"]
        label   = row["label"]
        source  = row["source"]
        info    = NODE_COLOR_MAP.get(ntype, {"color": "#555", "font_color": "#fff"})
        sh_info = SOURCE_SHAPE_MAP.get(source, SOURCE_SHAPE_MAP["내부"])

        is_hub = (label == "스포츠")
        size   = node_size * 1.75 if is_hub else node_size

        # 테두리 색 (외부 빨간색 제거 — 모두 타입 자체 색 사용, 허브·공통만 황금)
        if is_hub or source == "공통":
            border_col = "#FFD700"
        else:
            border_col = info["color"]

        border_width = sh_info["borderWidth"] + (2 if is_hub else 0)

        src_icon  = {"내부": "●", "외부": "■", "공통": "⬤"}.get(source, "")
        src_label = {"내부": "내부 데이터", "외부": "외부 트렌드", "공통": "공통(브릿지)"}.get(source, source)

        tooltip = (
            f"<div style='font-family:sans-serif;padding:6px'>"
            f"<b style='color:{info['color']};font-size:14px'>{label}</b><br>"
            f"<span style='color:#bbb;font-size:11px'>타입: {ntype}</span><br>"
            f"<span style='color:#bbb;font-size:11px'>소스: {src_icon} {src_label}</span>"
            + ("<br><span style='color:#FFD700;font-size:11px'>⭐ 핵심 브릿지 허브</span>" if is_hub else "")
            + "</div>"
        )

        net.add_node(
            label, label=label, title=tooltip,
            shape=sh_info["shape"],
            color={
                "background": info["color"],
                "border": border_col,
                "highlight": {"background": info["color"], "border": "#FFD700"},
                "hover":     {"background": info["color"], "border": "#ffffff"},
            },
            font={"color": info["font_color"], "size": 16 if is_hub else 13},
            size=size,
            borderWidth=border_width,
        )

    for _, row in edges.iterrows():
        src, tgt = row["from"], row["to"]
        alpha    = float(row.get("alpha", 1.0))
        is_bridge = ("스포츠" in [src, tgt])

        # K리그/KBO 내부문제 엣지 vs 외부트렌드 엣지 색 구분
        src_info = nodes[nodes["label"] == src]["source"].values
        src_source = src_info[0] if len(src_info) > 0 else "내부"

        if is_bridge:
            edge_color = "rgba(255,215,0,0.95)"
            edge_width = 5.0
            edge_title = "🌉 내·외부 트렌드 브릿지"
        elif src_source == "외부" or (nodes[nodes["label"] == tgt]["source"].values[:1] or [""])[0] == "외부":
            edge_color = "rgba(237,100,100,0.6)"
            edge_width = max(1.5, alpha * 1.6)
            edge_title = f"외부: {src} ↔ {tgt}"
        else:
            edge_color = "rgba(100,210,160,0.5)"
            edge_width = max(1.5, alpha * 1.6)
            edge_title = f"내부: {src} ↔ {tgt}"

        net.add_edge(src, tgt, color=edge_color, width=edge_width, title=edge_title)

    out_path = os.path.join(BASE_DIR, "_hin_graph.html")
    net.save_graph(out_path)
    with open(out_path, "r", encoding="utf-8") as f:
        html = f.read()

    # ── BFS 경로 하이라이트 JS 주입 ──────────────────────────────────
    path_js = """
<script>
(function () {
  /* ── 상태 ── */
  var step1Node = null;          // 첫 번째 클릭 노드 ID
  var pathActive = false;        // 경로 표시 중 여부
  var origNodeColors = {};       // 원본 노드 색상 저장
  var origEdgeColors = {};       // 원본 엣지 색상 저장
  var origEdgeWidths = {};       // 원본 엣지 두께 저장

  /* ── 원본 스타일 스냅샷 ── */
  function snapshot() {
    nodes.get().forEach(function (n) { origNodeColors[n.id] = JSON.parse(JSON.stringify(n.color || {})); });
    edges.get().forEach(function (e) {
      origEdgeColors[e.id] = JSON.parse(JSON.stringify(e.color || {}));
      origEdgeWidths[e.id] = e.width || 2;
    });
  }

  /* ── 인접 리스트 (무방향) ── */
  function buildAdj() {
    var adj = {};
    edges.get().forEach(function (e) {
      if (!adj[e.from]) adj[e.from] = [];
      if (!adj[e.to])   adj[e.to]   = [];
      adj[e.from].push({ node: e.to,   edgeId: e.id });
      adj[e.to].push(  { node: e.from, edgeId: e.id });
    });
    return adj;
  }

  /* ── BFS 최단 경로 ── */
  function bfs(start, end) {
    var adj = buildAdj();
    var visited = {}; visited[start] = true;
    var queue = [{ node: start, nodePath: [start], edgePath: [] }];
    while (queue.length) {
      var cur = queue.shift();
      if (cur.node === end) return cur;
      (adj[cur.node] || []).forEach(function (nb) {
        if (!visited[nb.node]) {
          visited[nb.node] = true;
          queue.push({
            node: nb.node,
            nodePath: cur.nodePath.concat([nb.node]),
            edgePath: cur.edgePath.concat([nb.edgeId])
          });
        }
      });
    }
    return null;
  }

  /* ── 배너 표시 ── */
  function showBanner(html, bg) {
    var b = document.getElementById('__path_banner__');
    if (!b) {
      b = document.createElement('div');
      b.id = '__path_banner__';
      b.style.cssText = [
        'position:fixed','top:18px','left:50%','transform:translateX(-50%)',
        'z-index:99999','padding:10px 26px','border-radius:28px',
        'font-family:\"Noto Sans KR\",sans-serif','font-size:13px','font-weight:700',
        'box-shadow:0 6px 32px rgba(0,0,0,0.6)','max-width:80vw',
        'text-align:center','border:1.5px solid rgba(255,255,255,0.15)',
        'pointer-events:none','line-height:1.6'
      ].join(';');
      document.body.appendChild(b);
    }
    b.style.background = bg;
    b.innerHTML = html;
  }

  function hideBanner() {
    var b = document.getElementById('__path_banner__');
    if (b) b.remove();
  }

  /* ── 전체 초기화 ── */
  function resetAll() {
    nodes.get().forEach(function (n) {
      nodes.update({ id: n.id, color: origNodeColors[n.id] || n.color, opacity: 1.0 });
    });
    edges.get().forEach(function (e) {
      edges.update({ id: e.id, color: origEdgeColors[e.id] || e.color, width: origEdgeWidths[e.id] || 2, opacity: 1.0 });
    });
    step1Node  = null;
    pathActive = false;
    hideBanner();
  }

  /* ── 경로 하이라이트 ── */
  function highlightPath(result) {
    var pathNodeSet = {};
    result.nodePath.forEach(function (id) { pathNodeSet[id] = true; });
    var pathEdgeSet = {};
    result.edgePath.forEach(function (id) { pathEdgeSet[id] = true; });

    // 비경로 노드/엣지 흐리게
    nodes.get().forEach(function (n) {
      if (!pathNodeSet[n.id]) nodes.update({ id: n.id, opacity: 0.15 });
    });
    edges.get().forEach(function (e) {
      if (!pathEdgeSet[e.id]) edges.update({ id: e.id, color: { color: 'rgba(100,100,120,0.18)' }, opacity: 0.15 });
    });

    // 경로 노드 강조
    result.nodePath.forEach(function (id, i) {
      var isEndpoint = (i === 0 || i === result.nodePath.length - 1);
      nodes.update({
        id: id,
        color: { background: isEndpoint ? '#FFD700' : '#00d67a', border: '#ffffff' },
        opacity: 1.0
      });
    });

    // 경로 엣지 강조
    result.edgePath.forEach(function (id) {
      edges.update({ id: id, color: { color: '#FFD700', opacity: 1.0 }, width: 6, opacity: 1.0 });
    });

    // 배너
    var hops = result.nodePath.length - 1;
    var pathStr = result.nodePath.join(' &rarr; ');
    showBanner(
      '✨ 최단 경로 <span style="color:#FFD700">(' + hops + '홉)</span>: ' + pathStr +
      '<br><span style="font-size:11px;color:rgba(255,255,255,0.55)">빈 곳 클릭 시 초기화</span>',
      'linear-gradient(135deg,rgba(10,10,30,0.97),rgba(20,20,55,0.97))'
    );
  }

  /* ── 이벤트 연결 (stabilized 후 실행) ── */
  network.once('stabilized', function () {
    snapshot();

    network.on('click', function (params) {
      /* 빈 공간 클릭 → 초기화 */
      if (!params.nodes || params.nodes.length === 0) {
        resetAll();
        return;
      }

      var clicked = params.nodes[0];

      /* 1단계: 출발 노드 선택 */
      if (!step1Node) {
        if (pathActive) resetAll();
        step1Node = clicked;
        nodes.update({ id: clicked, color: { background: '#FFD700', border: '#FFA500' }, opacity: 1.0 });
        showBanner(
          '🟡 출발 노드: <b>' + clicked + '</b><br>' +
          '<span style="font-size:11px;color:rgba(255,255,255,0.6)">도착 노드를 클릭하세요</span>',
          'rgba(20,16,50,0.95)'
        );
        return;
      }

      /* 같은 노드 재클릭 → 초기화 */
      if (clicked === step1Node) { resetAll(); return; }

      /* 2단계: 도착 노드 선택 → BFS */
      var result = bfs(step1Node, clicked);
      pathActive = true;

      if (result) {
        highlightPath(result);
      } else {
        showBanner(
          '❌ <b>' + step1Node + '</b> → <b>' + clicked + '</b> 직접 경로 없음',
          'rgba(160,20,20,0.95)'
        );
        setTimeout(resetAll, 2200);
      }
      step1Node = null;
    });
  });
})();
</script>
</body>
"""
    # </body> 직전에 주입
    html = html.replace("</body>", path_js)
    return html

# ───────────────────────────────────────────
# 레이아웃
# ───────────────────────────────────────────
left_col, right_col = st.columns([3, 1])

with left_col:
    st.markdown("### 📊 이기종 정보 네트워크 (HIN)")

    tip_html = """
    <div style="background:rgba(255,255,255,0.04);border-radius:10px;padding:10px 16px;
                font-size:0.8rem;color:#aac;margin-bottom:10px;border:1px solid rgba(255,255,255,0.07)">
        💡 <b>노드 클릭 드래그</b>로 자유롭게 이동 &nbsp;·&nbsp;
        <b>마우스 호버</b> 시 연결 노드·엣지 하이라이트 &nbsp;·&nbsp;
        <span style="color:#FFD700"><b>노드 두 번 클릭</b></span>으로 <b>두 노드 간 최단 경로 강조</b> (빈 곳 클릭 시 초기화)
    </div>
    """
    st.markdown(tip_html, unsafe_allow_html=True)

    if not active_sources:
        st.warning("⚠️ 사이드바에서 데이터 소스를 하나 이상 선택하세요.")
    elif filtered_nodes.empty:
        st.warning("선택 조건에 맞는 노드가 없습니다.")
    else:
        graph_html = build_graph(filtered_nodes, filtered_edges)
        components.html(graph_html, height=740, scrolling=False)

with right_col:
    st.markdown("### 💡 핵심 인사이트")

    # K리그 내부 문제
    st.markdown("""
    <div class="ins" style="background:linear-gradient(135deg,rgba(0,166,81,0.13),rgba(0,80,40,0.06));
         border-left:4px solid #00A651; color:#b8f5d8;">
        <b style="color:#00d67a">● K리그 (내부 데이터)</b><br>
        <span style="color:#FF9090">관중 점유율 정체</span>·<span style="color:#FF9090">팬덤 고령화</span> 문제가 노출됨.<br>
        새로운 소비층 유입을 위한 외부 트렌드 접목이 필요한 상황.
    </div>
    """, unsafe_allow_html=True)

    # KBO 외부 트렌드
    st.markdown("""
    <div class="ins" style="background:linear-gradient(135deg,rgba(237,28,36,0.12),rgba(160,0,0,0.06));
         border-left:4px solid #ED1C24; color:#ffc8c8;">
        <b style="color:#FF7070">■ KBO (외부 트렌드)</b><br>
        <span style="color:#FFD700">MZ세대 유입 급증</span>·<span style="color:#FFD700">역대급 관중 동원</span>으로 스포츠 소비 생태계가 확장 중.<br>
        이 트렌드가 세븐일레븐 상품(크보빵)과 직결됨.
    </div>
    """, unsafe_allow_html=True)

    # 스포츠 브릿지
    st.markdown("""
    <div class="ins" style="background:linear-gradient(135deg,rgba(255,215,0,0.12),rgba(200,150,0,0.06));
         border-left:4px solid #FFD700; color:#fff8d0;">
        <b style="color:#FFD700">⬤ '스포츠' 브릿지 허브</b><br>
        황금 엣지(──)가 두 영역을 연결합니다.<br>
        KBO의 성장 트렌드 →<b>스포츠</b>→ K리그IP 경로가<br>
        슛!비타민워터 상품 기획의 근거가 됩니다.
    </div>
    """, unsafe_allow_html=True)

    # 호버 가이드
    st.markdown("""
    <div class="ins" style="background:rgba(255,255,255,0.04);border-left:4px solid #8899cc; color:#ccd;">
        <b>🖱️ 인터랙션 가이드</b><br>
        · <b>호버</b>: 연결 노드·엣지만 밝게 표시<br>
        · <b>클릭</b>: 연결 엣지 선택 강조<br>
        · <b>드래그</b>: 노드 위치 자유 변경<br>
        · <b>스크롤</b>: 줌 인/아웃
    </div>
    """, unsafe_allow_html=True)



# ───────────────────────────────────────────
# 하단 데이터 테이블
# ───────────────────────────────────────────
st.markdown("---")
with st.expander("📄 원본 데이터 (노드·엣지)", expanded=False):
    t1, t2 = st.tabs(["노드 목록", "엣지 목록"])
    with t1:
        st.dataframe(filtered_nodes.reset_index(drop=True), use_container_width=True)
    with t2:
        st.dataframe(filtered_edges.reset_index(drop=True), use_container_width=True)

st.markdown("""
<p style='text-align:center;color:rgba(255,255,255,0.25);font-size:0.73rem;margin-top:14px;'>
경희대학교 산학협력 캡스톤디자인 2026 · 세븐일레븐 B팀 · LLM-RAG 기반 상품 기획 지원 시스템
</p>
""", unsafe_allow_html=True)
