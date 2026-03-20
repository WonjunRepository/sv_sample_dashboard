"""
세븐일레븐 동적 지식 그래프(HIN) 대시보드 v4
고정 레이아웃 · 그룹 하이라이트 · 점선 엣지 · 호버 효과 — 임원 보고용
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
    "상품명":    {"color": "#444444", "font_color": "#FFFFFF"},   # 다크 그레이 (요청)
    "카테고리":  {"color": "#000080", "font_color": "#FFFFFF"},   # 딥 네이비
    "원재료":    {"color": "#FF00FF", "font_color": "#FFFFFF"},
    "인플루언서": {"color": "#ED1C24", "font_color": "#FFFFFF"},
    "시간":      {"color": "#F58220", "font_color": "#FFFFFF"},
    "IP/브랜드": {"color": "#00A651", "font_color": "#FFFFFF"},
    "후기/특성": {"color": "#00AEEF", "font_color": "#FFFFFF"},
}

# 소스별 형태: 내부=dot / 외부=square / 공통=dot (굵은 테두리)
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

# 노드 좌표 고정 레이아웃 (x: 내부=-250~-450, 외부=+250~+450, 공통=0)
# '슛!비타민워터'는 정중앙(0, 0) 고정
FIXED_POSITIONS = {
    # 중심 상품 노드
    "슛!비타민워터":      {"x":   0,   "y":   0},
    # 내부 노드 (좌측 클러스터)
    "음료수":            {"x": -220,  "y": -120},
    "비타민B":           {"x": -260,  "y":  40},
    "레몬향":            {"x": -220,  "y":  170},
    "K리그":             {"x": -400,  "y": -60},
    "상큼":              {"x": -170,  "y": -220},
    "관중 정체":   {"x": -500,  "y":  100},
    "팬덤 고령화":        {"x": -500,  "y": -160},
    # 외부 노드 (우측 클러스터)
    "크보빵":            {"x":  300,  "y":  0},
    "빵":                {"x":  420,  "y":  140},
    "KBO":               {"x":  420,  "y": -80},
    "여름 시즌":          {"x":  260,  "y":  200},
    "MZ 세대 유입":   {"x":  560,  "y": -180},
    "역대급 관중":   {"x":  560,  "y":  80},
    # 공통 브릿지 (중간)
    "스포츠":            {"x":   0,   "y": -280},
}

# ───────────────────────────────────────────
# 글로벌 CSS
# ───────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@300;400;600;700;900&family=Inter:wght@300;400;600;700&display=swap');

html, body, [class*="css"] { font-family: 'Noto Sans KR', 'Inter', sans-serif; }

[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #f8f9fa 0%, #e9ecef 100%);
    border-right: 1px solid rgba(0,0,0,0.06);
}
[data-testid="stSidebar"] * { color: #222222 !important; }

.stApp { background: radial-gradient(ellipse at 20% 10%, #ffffff 0%, #f4f6f9 55%, #e9ecef 100%); }

/* ── 헤더 ── */
.db-header {
    background: linear-gradient(130deg, #005730 0%, #007A40 50%, #004D28 100%);
    border-radius: 18px;
    padding: 24px 36px;
    margin-bottom: 20px;
    display: flex; align-items: center; gap: 20px;
    box-shadow: 0 8px 30px rgba(0,0,0,0.1);
    border: 1px solid rgba(0,0,0,0.08);
}
.db-header h1 { color:#fff !important; font-size:1.65rem !important; font-weight:800 !important; margin:0 !important; text-shadow:0 2px 5px rgba(0,0,0,0.3); }
.db-header .sub { color:rgba(255,255,255,0.9); font-size:0.84rem; margin-top:5px; }

/* ── 배지 ── */
.badge { display:inline-block; padding:3px 11px; border-radius:20px; font-size:0.72rem; font-weight:700; margin:0 3px; }
.b-in  { background:rgba(0,166,81,0.1);  color:#008A43; border:1px solid #00A651; }
.b-out { background:rgba(237,28,36,0.1); color:#D11820; border:1px solid #ED1C24; }
.b-com { background:rgba(255,165,0,0.15); color:#E65C00; border:1px solid #FF8C00; }

/* ── 통계 카드 ── */
.s-card { background:#ffffff; border:1px solid rgba(0,0,0,0.08); border-radius:14px; padding:15px 12px; text-align:center; box-shadow:0 2px 8px rgba(0,0,0,0.04); }
.s-num  { font-size:1.9rem; font-weight:800; }
.s-lbl  { font-size:0.75rem; color:#666666; margin-top:3px; font-weight:600; }

/* ── 인사이트 카드 ── */
.ins { border-radius:0 14px 14px 0; padding:13px 17px; margin:10px 0; font-size:0.85rem; line-height:1.72; }

/* ── 형태 범례 ── */
.shape-box { background:#ffffff; border:1px solid rgba(0,0,0,0.06); border-radius:10px; padding:12px 15px; font-size:0.8rem; color:#444; box-shadow:0 2px 5px rgba(0,0,0,0.02); }
.shape-box table { width:100%; border-collapse:collapse; }
.shape-box td { padding:5px 6px; }
.shape-box tr:not(:last-child) td { border-bottom:1px solid rgba(0,0,0,0.04); }

/* ── 하이라이트 모드 라디오 ── */
.stRadio > div { gap: 8px !important; }
.stRadio label { cursor: pointer; }

hr { border-color:rgba(0,0,0,0.08) !important; }
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

    # ── 핵심: 하이라이트 모드 라디오 버튼 ──
    st.markdown("## 🔆 그룹 하이라이트 모드")
    highlight_mode = st.radio(
        label="보기 모드 선택",
        options=["전체 보기", "내부 강조", "외부 강조"],
        index=0,
        label_visibility="collapsed",
    )

    st.markdown("""
    <div style="font-size:0.76rem;color:#445577;margin-top:6px;padding:8px 10px;
                background:rgba(0,0,0,0.04);border-radius:8px;line-height:1.7">
        · <b>전체 보기</b>: 모든 노드 선명<br>
        · <b>내부 강조</b>: 내부+공통 강조, 외부 흐림<br>
        · <b>외부 강조</b>: 외부+공통 강조, 내부 흐림
    </div>
    """, unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("#### 노드 검색")
    search_term = st.text_input("", placeholder="예: 스포츠, K리그…", label_visibility="collapsed")

    st.markdown("---")
    st.caption("© 2026 경희대학교 캡스톤디자인\n세븐일레븐 산학협력 B팀")

# ───────────────────────────────────────────
# 헤더
# ───────────────────────────────────────────
st.markdown("""
<div class="db-header">
  <span style="font-size:2.6rem">🏪</span>
  <div>
    <h1>세븐일레븐 지식 그래프 기반 트렌드 분석 대시보드 v4</h1>
    <div class="sub">
      <span class="badge b-in">● 내부 원형</span>
      <span class="badge b-out">■ 외부 사각형</span>
      <span class="badge b-com">⬤ 공통 브릿지</span>
      &nbsp;·&nbsp; 고정 레이아웃 &nbsp;·&nbsp; 그룹 하이라이트 &nbsp;·&nbsp; 호버 하이라이트 활성화
    </div>
  </div>
</div>
""", unsafe_allow_html=True)

# ───────────────────────────────────────────
# 통계 카드 (5개)
# ───────────────────────────────────────────
n_in  = len(nodes_df[nodes_df["source"]=="내부"])
n_out = len(nodes_df[nodes_df["source"]=="외부"])
n_com = len(nodes_df[nodes_df["source"]=="공통"])
n_hub = len([x for x in ["스포츠"] if x in set(nodes_df["label"].tolist())])

cols = st.columns(5)
for col, (num, clr, lbl) in zip(cols, [
    (len(nodes_df), "#00d67a", "전체 노드"),
    (len(edges_df), "#00AEEF", "전체 엣지"),
    (n_in,          "#00A651", "내부 노드"),
    (n_out,         "#ED1C24", "외부 노드"),
    (n_hub,         "#FFD700", "브릿지 허브"),
]):
    with col:
        st.markdown(f'<div class="s-card"><div class="s-num" style="color:{clr}">{num}</div><div class="s-lbl">{lbl}</div></div>', unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# ───────────────────────────────────────────
# Pyvis 그래프 빌더 v4
# ───────────────────────────────────────────
def build_graph(nodes: pd.DataFrame, edges: pd.DataFrame, mode: str, search: str) -> str:
    """
    mode: "전체 보기" | "내부 강조" | "외부 강조"
    고정 레이아웃: stabilization 후 physics 비활성화
    점선: 외부 트렌드 엣지
    """
    net = Network(height="720px", width="100%",
                  bgcolor="#ffffff", font_color="#222222",
                  directed=False, notebook=False)

    # ── 물리 엔진: stabilization 후 완전 비활성화 ──
    net.set_options("""
    {
      "nodes": {
        "shadow": {"enabled": true, "size": 16, "x": 3, "y": 4},
        "font": {
          "size": 16,
          "face": "Noto Sans KR",
          "bold": false,
          "strokeWidth": 3,
          "strokeColor": "#ffffff"
        }
      },
      "edges": {
        "width": 2,
        "smooth": {"type": "curvedCW", "roundness": 0.1},
        "shadow": {"enabled": true}
      },
      "physics": {
        "enabled": false
      },
      "interaction": {
        "hover": true,
        "hoverConnectedEdges": true,
        "selectConnectedEdges": true,
        "dragNodes": true,
        "zoomView": true,
        "tooltipDelay": 100,
        "multiselect": false,
        "navigationButtons": false,
        "keyboard": {"enabled": true}
      }
    }
    """)

    # ── 하이라이트 모드에 따른 opacity 결정 함수 ──
    def get_opacity(source: str) -> float:
        """모드에 따라 노드 opacity 반환"""
        if mode == "전체 보기":
            return 1.0
        elif mode == "내부 강조":
            # 내부 + 공통(스포츠) = 선명, 외부 = 흐림
            return 1.0 if source in ("내부", "공통") else 0.18
        else:  # 외부 강조
            # 외부 + 공통(스포츠) = 선명, 내부 = 흐림
            return 1.0 if source in ("외부", "공통") else 0.15

    def dimmed_color(color_hex: str) -> str:
        """흐림 처리 시 옅은 회색 계열로 변환"""
        return "#ebebeb"

    # ── 노드 추가 ──
    for _, row in nodes.iterrows():
        ntype   = row["type"]
        label   = row["label"]
        source  = row["source"]
        info    = NODE_COLOR_MAP.get(ntype, {"color": "#555", "font_color": "#fff"})
        sh_info = SOURCE_SHAPE_MAP.get(source, SOURCE_SHAPE_MAP["내부"])

        is_hub   = (label == "스포츠")
        is_center = (label == "슛!비타민워터")
        size     = 42 if is_center else (38 if is_hub else 28)

        opacity = get_opacity(source)
        is_dim  = (opacity < 0.5)

        # 검색 하이라이트
        is_searched = search.strip() and search.strip().lower() in label.lower()

        if is_hub or source == "공통":
            border_col = "#FF9900" if not is_dim else "#d0d0d0"
        elif is_center:
            border_col = "#888888"
        else:
            border_col = info["color"] if not is_dim else "#cccccc"

        node_bg    = (dimmed_color(info["color"]) if is_dim else info["color"])
        node_font  = "#aaaaaa" if is_dim else info["font_color"]
        border_width = sh_info["borderWidth"] + (2 if is_hub else 0) + (3 if is_center else 0)

        src_icon  = {"내부": "●", "외부": "■", "공통": "⬤"}.get(source, "")
        src_label = {"내부": "내부 데이터", "외부": "외부 트렌드", "공통": "공통(브릿지)"}.get(source, source)

        tooltip = (
            f"<div style='font-family:sans-serif;padding:6px;background:#ffffff;border-radius:4px'>"
            f"<b style='color:{info['color']};font-size:14px'>{label}</b><br>"
            f"<span style='color:#666666;font-size:11px'>타입: {ntype}</span><br>"
            f"<span style='color:#666666;font-size:11px'>소스: {src_icon} {src_label}</span>"
            + ("<br><span style='color:#FF8C00;font-size:11px'>⭐ 핵심 브릿지 허브</span>" if is_hub else "")
            + ("<br><span style='color:#888888;font-size:11px'>📍 중심 상품 노드</span>" if is_center else "")
            + "</div>"
        )

        # 고정 좌표 가져오기
        pos = FIXED_POSITIONS.get(label, {"x": 0, "y": 0})

        # 검색된 노드는 강제 하이라이트
        if is_searched:
            node_bg    = "#FFD700"
            node_font  = "#000000"
            border_col = "#FF8C00"

        net.add_node(
            label, label=label, title=tooltip,
            shape=sh_info["shape"],
            color={
                "background": node_bg,
                "border":     border_col,
                "highlight":  {"background": info["color"], "border": "#FFD700"},
                "hover":      {"background": info["color"], "border": "#ffffff"},
            },
            font={"color": node_font, "size": 22 if is_center else (20 if is_hub else 16),
                  "strokeWidth": 3, "strokeColor": "#ffffff", "bold": False,
                  "vadjust": 6},
            size=size,
            borderWidth=border_width,
            opacity=opacity,
            x=pos["x"], y=pos["y"],
            physics=False,  # 개별 노드 물리 비활성화
        )

    # ── 엣지 추가 ──
    for _, row in edges.iterrows():
        src  = row["from"]
        tgt  = row["to"]
        alpha = float(row.get("alpha", 1.0))
        edge_type = row.get("edge_type", "내부") if "edge_type" in row else "내부"

        is_bridge = ("스포츠" in [src, tgt])

        # 엣지 연결된 노드의 source 확인
        src_source_arr = nodes[nodes["label"] == src]["source"].values
        tgt_source_arr = nodes[nodes["label"] == tgt]["source"].values
        src_source = src_source_arr[0] if len(src_source_arr) > 0 else "내부"
        tgt_source = tgt_source_arr[0] if len(tgt_source_arr) > 0 else "내부"

        # 양 끝 노드 중 하나라도 강조 대상이면 엣지 선명
        src_opacity = get_opacity(src_source)
        tgt_opacity = get_opacity(tgt_source)
        edge_opacity = max(src_opacity, tgt_opacity)
        is_edge_dim = (edge_opacity < 0.5)

        # 점선 여부: 외부 트렌드 엣지 (외부→외부, 외부→공통) = 점선
        is_dashed = (edge_type == "외부") or (src_source == "외부") or (tgt_source == "외부")
        # 브릿지 엣지 (K리그/KBO ↔ 스포츠)는 내부/외부 혼재, 엣지 타입으로 분기
        if is_bridge:
            # K리그-스포츠: 내부 실선, KBO-스포츠: 외부 점선
            non_sports = src if tgt == "스포츠" else tgt
            non_sports_src = nodes[nodes["label"] == non_sports]["source"].values
            ns = non_sports_src[0] if len(non_sports_src) > 0 else "내부"
            is_dashed = (ns == "외부")

        if is_bridge:
            edge_color = "rgba(255,140,0,0.8)" if not is_edge_dim else "rgba(255,140,0,0.15)"
            edge_width = 5.0 if not is_edge_dim else 2.0
            edge_title = "🌉 내·외부 트렌드 브릿지"
        elif src_source == "외부" or tgt_source == "외부":
            edge_color = ("rgba(237,28,36,0.6)" if not is_edge_dim else "rgba(237,28,36,0.15)")
            edge_width = max(1.5, alpha * 2.0) if not is_edge_dim else 1.2
            edge_title = f"외부: {src} ↔ {tgt}"
        else:
            edge_color = ("rgba(0,166,81,0.6)" if not is_edge_dim else "rgba(0,166,81,0.15)")
            edge_width = max(1.5, alpha * 2.0) if not is_edge_dim else 1.2
            edge_title = f"내부: {src} ↔ {tgt}"

        net.add_edge(
            src, tgt,
            color=edge_color,
            width=edge_width,
            title=edge_title,
            dashes=is_dashed,
        )

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
        'box-shadow:0 6px 20px rgba(0,0,0,0.1)','max-width:80vw',
        'text-align:center','border:1px solid rgba(0,0,0,0.08)',
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
      if (!pathEdgeSet[e.id]) edges.update({ id: e.id, color: { color: 'rgba(0,0,0,0.08)' }, opacity: 0.15 });
    });

    // 경로 노드 강조
    result.nodePath.forEach(function (id, i) {
      var isEndpoint = (i === 0 || i === result.nodePath.length - 1);
      nodes.update({
        id: id,
        color: { background: isEndpoint ? '#FF4500' : '#41B883', border: '#ffffff' },
        opacity: 1.0
      });
    });

    // 경로 엣지 강조
    result.edgePath.forEach(function (id) {
      edges.update({ id: id, color: { color: '#FF4500', opacity: 1.0 }, width: 6, opacity: 1.0 });
    });

    // 배너
    var hops = result.nodePath.length - 1;
    var pathStr = result.nodePath.join(' &rarr; ');
    showBanner(
      '✨ 최단 경로 <span style="color:#FF4500">(' + hops + '홉)</span>: ' + pathStr +
      '<br><span style="font-size:11px;color:#555555">빈 곳 클릭 시 초기화</span>',
      'rgba(255,255,255,0.95)'
    );
  }

  /* ── 이벤트 연결 ── */
  // 물리 엔진(physics)이 비활성화되어 있으므로 stabilized 이벤트가 발생하지 않습니다.
  // 대신 약간의 지연 후 바로 스냅샷을 찍고 이벤트를 바인딩합니다.
  setTimeout(function () {
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
        nodes.update({ id: clicked, color: { background: '#FF4500', border: '#D03000' }, opacity: 1.0 });
        showBanner(
          '🟡 출발 노드: <b><span style="color:#222">' + clicked + '</span></b><br>' +
          '<span style="font-size:11px;color:#555555">도착 노드를 클릭하세요</span>',
          'rgba(255,255,255,0.95)'
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
          '❌ <b><span style="color:#222">' + step1Node + '</span></b> → <b><span style="color:#222">' + clicked + '</span></b> 직접 경로 없음',
          'rgba(255,240,240,0.95)'
        );
        setTimeout(resetAll, 2200);
      }
      step1Node = null;
    });
  }, 500);
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
    st.markdown("### 📊 이기종 정보 네트워크 (HIN) — 고정 레이아웃")

    # 현재 모드 표시 배지
    mode_badge = {
        "전체 보기": '<span class="badge b-com">⬤ 전체 보기</span>',
        "내부 강조": '<span class="badge b-in">● 내부 강조</span>',
        "외부 강조": '<span class="badge b-out">■ 외부 강조</span>',
    }
    tip_html = f"""
    <div style="background:rgba(255,255,255,0.04);border-radius:10px;padding:10px 16px;
                font-size:0.8rem;color:#aac;margin-bottom:10px;border:1px solid rgba(255,255,255,0.07)">
        현재 모드: {mode_badge.get(highlight_mode, '')} &nbsp;·&nbsp;
        좌측 <span style="color:#00d67a"><b>내부 클러스터</b></span> &nbsp;|&nbsp;
        우측 <span style="color:#FF7070"><b>외부 클러스터</b></span> &nbsp;|&nbsp;
        중앙상단 <span style="color:#FFD700"><b>스포츠 브릿지</b></span><br>
        💡 <b>실선</b>: 내부 연결 &nbsp;·&nbsp; <b>점선</b>: 외부 트렌드 경로 &nbsp;·&nbsp;
        <span style="color:#FFD700"><b>노드 클릭→클릭</b></span>으로 최단 경로 탐색 (빈 곳 클릭 시 초기화)
    </div>
    """
    st.markdown(tip_html, unsafe_allow_html=True)

    graph_html = build_graph(nodes_df, edges_df, highlight_mode, search_term)
    components.html(graph_html, height=750, scrolling=False)

with right_col:
    st.markdown("### 💡 핵심 인사이트")

    # 하이라이트 모드 안내
    mode_color = {"전체 보기": "#8899cc", "내부 강조": "#00A651", "외부 강조": "#ED1C24"}
    mode_emoji = {"전체 보기": "🌐", "내부 강조": "🔵", "외부 강조": "🔴"}
    st.markdown(f"""
    <div class="ins" style="background:rgba(0,0,0,0.03);border-left:4px solid {mode_color.get(highlight_mode,'#8899cc')}; color:#222222;">
        <b>{mode_emoji.get(highlight_mode,'🌐')} 현재 모드: {highlight_mode}</b><br>
        {"선택 그룹 노드·엣지가 <b>선명</b>하게 강조되며, 비선택 그룹은 <b>회색 흐림</b> 처리됩니다." if highlight_mode != "전체 보기" else "모든 노드와 엣지가 선명하게 표시됩니다."}<br>
        <span style="color:#FF8C00;font-size:0.8rem">⬤ '스포츠' 공통 노드는 항상 강조됩니다.</span>
    </div>
    """, unsafe_allow_html=True)

    # K리그 내부 문제
    st.markdown("""
    <div class="ins" style="background:linear-gradient(135deg,rgba(0,166,81,0.08),rgba(0,166,81,0.02));
         border-left:4px solid #00A651; color:#222222;">
        <b style="color:#00A651">● K리그 (내부 데이터)</b><br>
        <span style="color:#D11820">관중 정체</span>·<span style="color:#D11820">팬덤 고령화</span> 문제가 노출됨.<br>
        새로운 소비층 유입을 위한 외부 트렌드 접목이 필요한 상황.
    </div>
    """, unsafe_allow_html=True)

    # KBO 외부 트렌드
    st.markdown("""
    <div class="ins" style="background:linear-gradient(135deg,rgba(237,28,36,0.08),rgba(237,28,36,0.02));
         border-left:4px solid #ED1C24; color:#222222;">
        <b style="color:#ED1C24">■ KBO (외부 트렌드)</b><br>
        <span style="color:#FF8C00">MZ 세대 유입</span>·<span style="color:#FF8C00">역대급 관중</span>으로 스포츠 소비 생태계가 확장 중.<br>
        이 트렌드가 세븐일레븐 상품(크보빵)과 직결됨.
    </div>
    """, unsafe_allow_html=True)

    # 스포츠 브릿지
    st.markdown("""
    <div class="ins" style="background:linear-gradient(135deg,rgba(255,165,0,0.12),rgba(255,165,0,0.04));
         border-left:4px solid #FFA500; color:#222222;">
        <b style="color:#FF8C00">⬤ '스포츠' 브릿지 허브</b><br>
        주황색 엣지(──)가 두 영역을 연결합니다.<br>
        KBO의 성장 트렌드 →<b>스포츠</b>→ K리그IP 경로가<br>
        슛!비타민워터 상품 기획의 근거가 됩니다.
    </div>
    """, unsafe_allow_html=True)

    # 인터랙션 가이드
    st.markdown("""
    <div class="ins" style="background:rgba(0,0,0,0.03);border-left:4px solid #667799; color:#445566;">
        <b>🖱️ 인터랙션 가이드</b><br>
        · <b>사이드바 라디오</b>: 그룹 하이라이트 전환<br>
        · <b>호버</b>: 연결 노드·엣지만 밝게 표시<br>
        · <b>노드→노드 클릭</b>: 최단 경로 탐색<br>
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
        st.dataframe(nodes_df.reset_index(drop=True), use_container_width=True)
    with t2:
        st.dataframe(edges_df.reset_index(drop=True), use_container_width=True)

st.markdown("""
<p style='text-align:center;color:rgba(255,255,255,0.25);font-size:0.73rem;margin-top:14px;'>
경희대학교 산학협력 캡스톤디자인 2026 · 세븐일레븐 B팀 · LLM-RAG 기반 상품 기획 지원 시스템
</p>
""", unsafe_allow_html=True)
