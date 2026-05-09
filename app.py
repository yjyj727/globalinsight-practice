"""
📰 Media Comparison Dashboard
같은 키워드를 두 미디어가 어떻게 다르게 보도하는지 비교 분석
Google News RSS + TextBlob + WordCloud + Plotly
"""

import streamlit as st
import requests
from bs4 import BeautifulSoup
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from textblob import TextBlob
from wordcloud import WordCloud
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use("Agg")
import re
from collections import Counter
from datetime import datetime, date, timedelta
from urllib.parse import quote
from dateutil import parser as dateutil_parser

# ──────────────────────────────────────────────
# 0. 페이지 설정
# ──────────────────────────────────────────────
st.set_page_config(
    page_title="Media Comparison Dashboard",
    page_icon="📰",
    layout="wide"
)

# ──────────────────────────────────────────────
# 1. 미디어 도메인 매핑
# ──────────────────────────────────────────────
MEDIA_DOMAINS = {
    "BBC":             "bbc.com",
    "Al Jazeera":      "aljazeera.com",
    "Reuters":         "reuters.com",
    "CNN":             "cnn.com",
    "The Guardian":    "theguardian.com",
    "NY Times":        "nytimes.com",
    "Washington Post": "washingtonpost.com",
    "Fox News":        "foxnews.com",
    "Deutsche Welle":  "dw.com",
    "France 24":       "france24.com",
}

# 미디어별 테마 색상 쌍 (컬러맵, 차트 색)
MEDIA_COLORS = {
    "BBC":             ("#1565C0", "Blues"),
    "Al Jazeera":      ("#E65100", "Oranges"),
    "Reuters":         ("#6A1B9A", "Purples"),
    "CNN":             ("#B71C1C", "Reds"),
    "The Guardian":    ("#1B5E20", "Greens"),
    "NY Times":        ("#263238", "Greys"),
    "Washington Post": ("#01579B", "Blues"),
    "Fox News":        ("#BF360C", "Oranges"),
    "Deutsche Welle":  ("#004D40", "YlGn"),
    "France 24":       ("#880E4F", "RdPu"),
}

# 기본 불용어
BASE_STOPWORDS = {
    "the", "a", "an", "is", "in", "of", "to", "and", "for", "that",
    "this", "it", "as", "at", "on", "with", "by", "are", "was", "be",
    "been", "has", "have", "had", "do", "does", "did", "will", "would",
    "could", "should", "from", "or", "but", "not", "its", "he", "she",
    "they", "we", "you", "i", "his", "her", "their", "more", "also",
    "up", "out", "about", "after", "into", "over", "s", "new", "says",
    "said", "one", "two", "three", "us", "who", "what", "how", "when",
    "where", "than", "so", "if", "all", "no", "says", "say"
}

# ──────────────────────────────────────────────
# 2. 커스텀 CSS
# ──────────────────────────────────────────────
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Syne:wght@400;600;700;800&family=Inter:wght@300;400;500&display=swap');

    html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
    h1, h2, h3 { font-family: 'Syne', sans-serif !important; }

    .stApp { background-color: #0c0c14; color: #e2e8f0; }
    .stSidebar { background: #080810 !important; }

    .media-header {
        font-family: 'Syne', sans-serif; font-size: 1.05rem; font-weight: 700;
        padding: 6px 14px; border-radius: 20px; display: inline-block;
        margin-bottom: 12px; letter-spacing: 0.04em;
    }
    .m1-header { background: #1e3a5f; color: #93c5fd; border: 1px solid #3b82f6; }
    .m2-header { background: #3d1a00; color: #fdba74; border: 1px solid #f97316; }

    .metric-card {
        background: linear-gradient(135deg, #111827 0%, #1f2937 100%);
        border: 1px solid #374151; border-radius: 12px; padding: 18px;
        text-align: center;
    }
    .metric-val { font-family: 'Syne', sans-serif; font-size: 1.9rem; font-weight: 700; margin: 0; }
    .metric-lbl { font-size: 0.72rem; color: #9ca3af; margin-top: 4px;
                  text-transform: uppercase; letter-spacing: 0.07em; }

    .sentiment-badge {
        display: inline-block; padding: 3px 10px; border-radius: 12px;
        font-size: 0.78rem; font-weight: 600; font-family: 'Syne', sans-serif;
    }
    .badge-positive { background: #14532d; color: #86efac; border: 1px solid #22c55e; }
    .badge-negative { background: #450a0a; color: #fca5a5; border: 1px solid #ef4444; }
    .badge-neutral  { background: #1f2937; color: #d1d5db; border: 1px solid #6b7280; }

    .article-card {
        background: #111827; border: 1px solid #1f2937; border-radius: 10px;
        padding: 14px; margin-bottom: 10px;
    }
    .article-title { font-weight: 600; color: #f1f5f9; font-size: 0.9rem; line-height: 1.4; }
    .article-meta  { font-size: 0.75rem; color: #6b7280; margin-top: 5px; }
    .article-desc  { font-size: 0.82rem; color: #9ca3af; margin-top: 6px; line-height: 1.5; }

    .insight-box {
        background: #0f172a; border-left: 4px solid #3b82f6;
        padding: 14px 18px; border-radius: 0 10px 10px 0;
        color: #cbd5e1; font-size: 0.88rem; margin-top: 16px; line-height: 1.6;
    }
    .report-box {
        background: #0f172a; border: 1px solid #1e3a5f; border-radius: 12px;
        padding: 24px; font-size: 0.9rem; color: #cbd5e1; line-height: 1.8;
    }

    .stTabs [data-baseweb="tab-list"] { background: #0a0a12; border-radius: 10px; padding: 4px; gap: 3px; }
    .stTabs [data-baseweb="tab"] { background: transparent; color: #6b7280; border-radius: 7px;
                                    font-family: 'Syne', sans-serif; font-size: 0.78rem; font-weight: 600; }
    .stTabs [aria-selected="true"] { background: #3b82f6 !important; color: #fff !important; }

    .stTextInput input {
        background: #111827 !important; color: #f1f5f9 !important;
        border: 1px solid #374151 !important; font-family: 'Inter', sans-serif !important;
    }
    .stSelectbox div[data-baseweb="select"] > div {
        background: #111827 !important; border: 1px solid #374151 !important; color: #f1f5f9 !important;
    }
    .stButton>button {
        background: linear-gradient(135deg, #3b82f6, #1d4ed8) !important; color: white !important;
        border: none !important; border-radius: 8px !important; font-family: 'Syne', sans-serif !important;
        font-weight: 700 !important; transition: all 0.2s !important;
    }
    .stButton>button:hover { transform: translateY(-1px) !important;
                              box-shadow: 0 6px 16px rgba(59,130,246,0.4) !important; }
    div[data-testid="stDataFrame"] { background: #111827; border-radius: 8px; }
</style>
""", unsafe_allow_html=True)


# ──────────────────────────────────────────────
# 3. 데이터 수집 함수
# ──────────────────────────────────────────────
@st.cache_data(ttl=1800)
def fetch_media_news(keyword: str, media_name: str) -> pd.DataFrame:
    """Google News RSS에서 키워드 + 미디어 사이트 필터로 뉴스 수집 (30분 캐싱)"""
    domain = MEDIA_DOMAINS[media_name]
    # 공백 → '+', URL 인코딩
    q = quote(keyword.replace(" ", "+") + f"+site:{domain}")
    url = f"https://news.google.com/rss/search?q={q}&hl=en&gl=US&ceid=US:en"

    headers = {"User-Agent": "Mozilla/5.0 (compatible; NewsCompareBot/1.0)"}
    resp = requests.get(url, headers=headers, timeout=15)
    resp.raise_for_status()

    soup = BeautifulSoup(resp.content, "xml")
    items = soup.find_all("item")
    if not items:
        raise ValueError("기사 없음")

    records = []
    for item in items[:50]:
        title_t  = item.find("title")
        pub_t    = item.find("pubDate")
        desc_t   = item.find("description")
        source_t = item.find("source")
        link_t   = item.find("link")

        title  = title_t.get_text(strip=True)  if title_t  else ""
        desc_r = desc_t.get_text(strip=True)   if desc_t   else ""
        desc   = re.sub(r"<[^>]+>", "", desc_r)[:400]
        source = source_t.get_text(strip=True)  if source_t else media_name
        link   = link_t.get_text(strip=True)    if link_t   else ""

        # 날짜 파싱 — 실패 시 오늘 날짜 대체
        try:
            parsed_date = dateutil_parser.parse(pub_t.get_text(strip=True)).date()
        except Exception:
            parsed_date = date.today()

        # 제목 기준 TextBlob 감성 분석
        polarity = round(TextBlob(title).sentiment.polarity, 4)
        if polarity > 0.05:
            sentiment = "Positive"
        elif polarity < -0.05:
            sentiment = "Negative"
        else:
            sentiment = "Neutral"

        records.append({
            "title": title, "description": desc, "source": source,
            "date": parsed_date, "link": link,
            "polarity": polarity, "sentiment": sentiment,
            "media": media_name
        })

    df = pd.DataFrame(records)
    df["date"] = pd.to_datetime(df["date"])
    return df


# ──────────────────────────────────────────────
# 4. 텍스트 유틸리티
# ──────────────────────────────────────────────
def get_stopwords(keyword: str) -> set:
    """기본 불용어 + 검색 키워드 단어 포함"""
    extra = set(keyword.lower().split())
    return BASE_STOPWORDS | extra


def extract_word_freq(texts: list, stopwords: set) -> Counter:
    """텍스트 리스트 → 단어 빈도 Counter"""
    all_words = []
    for text in texts:
        words = re.findall(r"\b[a-zA-Z]{3,}\b", str(text).lower())
        all_words.extend([w for w in words if w not in stopwords])
    return Counter(all_words)


def make_wordcloud(text: str, colormap: str) -> plt.Figure:
    """WordCloud 생성 후 matplotlib Figure 반환"""
    wc = WordCloud(
        background_color="white", max_words=60,
        width=700, height=380, colormap=colormap,
        collocations=False
    ).generate(text if text.strip() else "no data available")
    fig, ax = plt.subplots(figsize=(8, 4))
    ax.imshow(wc, interpolation="bilinear")
    ax.axis("off")
    fig.patch.set_facecolor("#0c0c14")
    plt.tight_layout(pad=0)
    return fig


def sentiment_badge(label: str) -> str:
    """감성 레이블 → HTML 뱃지"""
    cls = {"Positive": "badge-positive", "Negative": "badge-negative"}.get(label, "badge-neutral")
    emoji = {"Positive": "😊", "Negative": "😟"}.get(label, "😐")
    return f'<span class="sentiment-badge {cls}">{emoji} {label}</span>'


def sentiment_label(polarity: float) -> str:
    if polarity > 0.05:
        return "Positive"
    elif polarity < -0.05:
        return "Negative"
    return "Neutral"


# ──────────────────────────────────────────────
# 5. 세션 상태 초기화
# ──────────────────────────────────────────────
defaults = {
    "search_history": [],
    "last_keyword":   "",
    "last_media1":    "BBC",
    "last_media2":    "CNN",
    "df1": None, "df2": None,
    "current_kw": "", "current_m1": "", "current_m2": ""
}
for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v


# ──────────────────────────────────────────────
# 6. 사이드바
# ──────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
    <div style="text-align:center; padding:10px 0 20px;">
        <div style="font-family:'Syne',sans-serif; font-size:1.15rem;
                    color:#3b82f6; font-weight:800; letter-spacing:0.05em;">📰 MEDIA LENS</div>
        <div style="color:#6b7280; font-size:0.73rem; margin-top:4px;">Comparative News Analysis</div>
    </div>
    """, unsafe_allow_html=True)

    # 최근 검색 기록 (최대 5개)
    st.markdown("### 🕐 Search History")
    if st.session_state.search_history:
        for entry in reversed(st.session_state.search_history[-5:]):
            label = f"🔍 {entry['keyword']} ({entry['m1']} vs {entry['m2']})"
            if st.button(label, key=f"hist_{label}", use_container_width=True):
                st.session_state.last_keyword = entry["keyword"]
                st.session_state.last_media1  = entry["m1"]
                st.session_state.last_media2  = entry["m2"]
                st.rerun()
    else:
        st.markdown("<div style='color:#374151; font-size:0.8rem;'>No recent searches.</div>",
                    unsafe_allow_html=True)

    st.markdown("---")

    # 날짜 범위 필터
    st.markdown("### 📅 Date Filter")
    date_range_days = st.slider("Show articles from last N days", 1, 60, 30, key="date_filter")

    # 최소 기사 수 필터
    st.markdown("### 🔢 Min. Articles")
    min_articles = st.slider("Minimum articles required", 1, 20, 3, key="min_art")

    st.markdown("---")
    st.markdown("### 📌 About")
    st.markdown("""
    <div style="color:#6b7280; font-size:0.78rem; line-height:1.7;">
        <b style="color:#3b82f6;">Data source:</b> Google News RSS<br>
        <b style="color:#3b82f6;">Sentiment analysis:</b> TextBlob<br>
        <b style="color:#3b82f6;">Built with:</b> Streamlit<br>
        <b style="color:#3b82f6;">Cache:</b> 30-minute refresh<br><br>
        Compare how different news outlets frame the same story using
        keyword analysis, sentiment scoring, and vocabulary comparison.
    </div>
    """, unsafe_allow_html=True)


# ──────────────────────────────────────────────
# 7. 헤더 & 검색 영역
# ──────────────────────────────────────────────
st.markdown("""
<h1 style="font-size:1.9rem; margin-bottom:4px; color:#f1f5f9; font-weight:800;">
    📰 How Do Different Media Cover the Same Story?
</h1>
<p style="color:#6b7280; font-size:0.9rem; margin-top:0; margin-bottom:20px;">
    Enter a keyword and compare how two media outlets report it differently.
</p>
""", unsafe_allow_html=True)

# 검색 입력 4열 레이아웃
sc1, sc2, sc3, sc4 = st.columns([3, 2, 2, 1])

with sc1:
    keyword_input = st.text_input(
        "🔍 Keyword",
        value=st.session_state.last_keyword,
        placeholder="e.g. Gaza, AI regulation, climate",
        label_visibility="collapsed",
        key="kw_input"
    )
with sc2:
    media1_sel = st.selectbox(
        "📺 Media 1", list(MEDIA_DOMAINS.keys()),
        index=list(MEDIA_DOMAINS.keys()).index(st.session_state.last_media1),
        key="m1_sel"
    )
with sc3:
    media2_sel = st.selectbox(
        "📺 Media 2", list(MEDIA_DOMAINS.keys()),
        index=list(MEDIA_DOMAINS.keys()).index(st.session_state.last_media2),
        key="m2_sel"
    )
with sc4:
    compare_btn = st.button("🔍 Compare", use_container_width=True)

# ── 유효성 검사 ──
if compare_btn:
    kw = keyword_input.strip()
    if not kw:
        st.warning("👆 Please enter a keyword first.")
    elif media1_sel == media2_sel:
        st.warning("⚠️ Please select two **different** media outlets.")
    else:
        # 검색 실행 → 세션 저장
        st.session_state.last_keyword = kw
        st.session_state.last_media1  = media1_sel
        st.session_state.last_media2  = media2_sel

        # 검색 기록 갱신
        entry = {"keyword": kw, "m1": media1_sel, "m2": media2_sel}
        if entry not in st.session_state.search_history:
            st.session_state.search_history.append(entry)
        st.session_state.search_history = st.session_state.search_history[-5:]

        # 데이터 수집
        st.session_state.df1 = None
        st.session_state.df2 = None
        st.session_state.current_kw = kw
        st.session_state.current_m1 = media1_sel
        st.session_state.current_m2 = media2_sel

        with st.spinner(f"📡 Fetching {media1_sel} articles..."):
            try:
                st.session_state.df1 = fetch_media_news(kw, media1_sel)
            except Exception as e:
                st.warning(f"⚠️ Could not fetch {media1_sel}: {e}")

        with st.spinner(f"📡 Fetching {media2_sel} articles..."):
            try:
                st.session_state.df2 = fetch_media_news(kw, media2_sel)
            except Exception as e:
                st.warning(f"⚠️ Could not fetch {media2_sel}: {e}")

# ── 아직 검색 전이면 안내 ──
if not st.session_state.current_kw:
    st.info("👆 Enter a keyword and select two media outlets to start.")
    st.stop()

# ── 데이터 참조 ──
KEYWORD = st.session_state.current_kw
M1      = st.session_state.current_m1
M2      = st.session_state.current_m2
df1_raw = st.session_state.df1
df2_raw = st.session_state.df2

# 데이터 없으면 중단
if df1_raw is None and df2_raw is None:
    st.error("Could not retrieve data for either media. Please try a different keyword.")
    st.stop()

# 기사 0개 개별 경고
for df_check, media_check in [(df1_raw, M1), (df2_raw, M2)]:
    if df_check is not None and len(df_check) == 0:
        st.warning(f"⚠️ No articles found for '{KEYWORD}' in {media_check}. Try a different keyword.")

# 빈 df 대체
EMPTY_DF = pd.DataFrame(columns=["title","description","source","date","link","polarity","sentiment","media"])
df1_raw = df1_raw if df1_raw is not None else EMPTY_DF.copy()
df2_raw = df2_raw if df2_raw is not None else EMPTY_DF.copy()

# ── 날짜 범위 필터 적용 ──
cutoff = pd.Timestamp(date.today() - timedelta(days=st.session_state.date_filter))
df1 = df1_raw[df1_raw["date"] >= cutoff].copy() if not df1_raw.empty else df1_raw.copy()
df2 = df2_raw[df2_raw["date"] >= cutoff].copy() if not df2_raw.empty else df2_raw.copy()

# ── 색상 설정 ──
m1_color, m1_cmap = MEDIA_COLORS.get(M1, ("#3b82f6", "Blues"))
m2_color, m2_cmap = MEDIA_COLORS.get(M2, ("#f97316", "Oranges"))


# ──────────────────────────────────────────────
# 8. 상단 메트릭 5열
# ──────────────────────────────────────────────
st.markdown("---")
mc1, mc2, mc3, mc4, mc5 = st.columns(5)

def avg_sentiment(df):
    if df.empty:
        return 0.0, "Neutral"
    p = df["polarity"].mean()
    return round(p, 4), sentiment_label(p)

avg_p1, lbl1 = avg_sentiment(df1)
avg_p2, lbl2 = avg_sentiment(df2)
delta_sent = round(avg_p1 - avg_p2, 4)

badge1 = sentiment_badge(lbl1)
badge2 = sentiment_badge(lbl2)

with mc1:
    st.markdown(f"""<div class="metric-card">
        <div class="metric-val" style="color:{m1_color};">{len(df1)}</div>
        <div class="metric-lbl">{M1} Articles</div>
    </div>""", unsafe_allow_html=True)

with mc2:
    st.markdown(f"""<div class="metric-card">
        <div class="metric-val" style="color:{m2_color};">{len(df2)}</div>
        <div class="metric-lbl">{M2} Articles</div>
    </div>""", unsafe_allow_html=True)

with mc3:
    st.markdown(f"""<div class="metric-card">
        <div class="metric-val" style="font-size:1.1rem; padding-top:8px;">{badge1}</div>
        <div class="metric-lbl">{M1} Sentiment ({avg_p1:+.3f})</div>
    </div>""", unsafe_allow_html=True)

with mc4:
    st.markdown(f"""<div class="metric-card">
        <div class="metric-val" style="font-size:1.1rem; padding-top:8px;">{badge2}</div>
        <div class="metric-lbl">{M2} Sentiment ({avg_p2:+.3f})</div>
    </div>""", unsafe_allow_html=True)

with mc5:
    delta_color = "#86efac" if delta_sent > 0 else ("#fca5a5" if delta_sent < 0 else "#9ca3af")
    direction   = f"{M1} more positive" if delta_sent > 0 else (f"{M2} more positive" if delta_sent < 0 else "Equal")
    st.markdown(f"""<div class="metric-card">
        <div class="metric-val" style="color:{delta_color}; font-size:1.6rem;">{delta_sent:+.3f}</div>
        <div class="metric-lbl">Sentiment Δ · {direction}</div>
    </div>""", unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)


# ──────────────────────────────────────────────
# 9. 공통 계산 (모든 탭에서 재사용)
# ──────────────────────────────────────────────
sw = get_stopwords(KEYWORD)

texts1 = (df1["title"] + " " + df1["description"]).tolist() if not df1.empty else []
texts2 = (df2["title"] + " " + df2["description"]).tolist() if not df2.empty else []

freq1 = extract_word_freq(texts1, sw)
freq2 = extract_word_freq(texts2, sw)

all_words_union = set(freq1.keys()) | set(freq2.keys())

# 고유 단어: 미디어1만 많이 쓰는 단어 (빈도 차이 내림차순)
unique_m1 = sorted(
    [(w, freq1[w] - freq2.get(w, 0)) for w in freq1 if freq1[w] - freq2.get(w, 0) > 0],
    key=lambda x: x[1], reverse=True
)[:10]

unique_m2 = sorted(
    [(w, freq2[w] - freq1.get(w, 0)) for w in freq2 if freq2[w] - freq1.get(w, 0) > 0],
    key=lambda x: x[1], reverse=True
)[:10]

# 공통 단어 (두 미디어 모두 상위 50에 속하는 단어)
top50_1 = {w for w, _ in freq1.most_common(50)}
top50_2 = {w for w, _ in freq2.most_common(50)}
common_words = sorted(
    [(w, freq1[w], freq2[w]) for w in top50_1 & top50_2],
    key=lambda x: x[1] + x[2], reverse=True
)[:10]


# ──────────────────────────────────────────────
# 10. 탭 구성
# ──────────────────────────────────────────────
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "☁️  Word Cloud",
    "🔤  Unique Words",
    "😊  Sentiment Compare",
    "📰  Headlines",
    "📊  Summary Report"
])


# ────────────────────────────────────────
# 탭1: Word Cloud
# ────────────────────────────────────────
with tab1:
    wc_col1, wc_col2 = st.columns(2)

    for col_w, df_m, media_nm, cmap, hdr_cls, texts_m in [
        (wc_col1, df1, M1, m1_cmap, "m1-header", texts1),
        (wc_col2, df2, M2, m2_cmap, "m2-header", texts2),
    ]:
        with col_w:
            st.markdown(f'<div class="media-header {hdr_cls}">📺 {media_nm}</div>',
                        unsafe_allow_html=True)
            if not texts_m:
                st.info(f"No data for {media_nm}.")
            else:
                raw_text = re.sub(r"[^a-zA-Z\s]", " ", " ".join(texts_m))
                # 불용어 제거한 텍스트
                clean_words = [w for w in raw_text.lower().split() if w not in sw and len(w) > 2]
                wc_text = " ".join(clean_words)
                wc_fig = make_wordcloud(wc_text, cmap)
                st.pyplot(wc_fig)
                plt.close(wc_fig)

    st.caption(
        f"Word clouds generated from article titles and descriptions. "
        f"Left: {M1} (Blues colormap) · Right: {M2} (Oranges colormap). "
        "Font size reflects word frequency; the search keyword and stop words are excluded."
    )

    # ── 상위 15개 단어 그룹 바 차트 ──
    st.markdown("---")
    st.markdown("#### 📊 Top 15 Words — Side-by-Side Comparison")

    top15_words_set = [w for w, _ in (freq1 + freq2).most_common(15)]
    if top15_words_set:
        compare_rows = []
        for w in top15_words_set:
            compare_rows.append({"Word": w, "Count": freq1.get(w, 0), "Media": M1})
            compare_rows.append({"Word": w, "Count": freq2.get(w, 0), "Media": M2})
        df_top15 = pd.DataFrame(compare_rows)

        fig_top15 = px.bar(
            df_top15, x="Word", y="Count", color="Media", barmode="group",
            color_discrete_map={M1: m1_color, M2: m2_color},
            labels={"Count": "Frequency", "Word": ""}
        )
        fig_top15.update_layout(
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(17,24,39,0.6)",
            font=dict(color="#9ca3af", family="Inter"),
            xaxis=dict(color="#6b7280", gridcolor="#1f2937"),
            yaxis=dict(color="#6b7280", gridcolor="#1f2937"),
            legend=dict(bgcolor="rgba(0,0,0,0)", font=dict(color="#d1d5db")),
            margin=dict(t=10, b=20), height=360
        )
        st.plotly_chart(fig_top15, use_container_width=True)
        st.caption(
            f"Top 15 most frequent words (excluding keyword and stop words) "
            f"compared side-by-side between {M1} and {M2}."
        )


# ────────────────────────────────────────
# 탭2: Unique Words
# ────────────────────────────────────────
with tab2:
    st.markdown("#### 🔤 Vocabulary Divergence — What Each Media Uniquely Emphasizes")

    uw_col1, uw_mid, uw_col2 = st.columns([2, 1.5, 2])

    # 미디어1 고유 단어 가로 바 차트
    with uw_col1:
        st.markdown(f'<div class="media-header m1-header">🔵 {M1} — Unique Top 10</div>',
                    unsafe_allow_html=True)
        if unique_m1:
            u1_words  = [x[0] for x in unique_m1][::-1]
            u1_counts = [x[1] for x in unique_m1][::-1]
            fig_u1 = go.Figure(go.Bar(
                x=u1_counts, y=u1_words, orientation="h",
                marker_color=m1_color, text=u1_counts, textposition="outside",
                textfont=dict(color="#d1d5db", size=10)
            ))
            fig_u1.update_layout(
                paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(17,24,39,0.6)",
                font=dict(color="#9ca3af"), xaxis=dict(color="#6b7280", gridcolor="#1f2937", title="Frequency diff"),
                yaxis=dict(color="#d1d5db", tickfont=dict(size=10)),
                margin=dict(l=5, r=40, t=10, b=20), height=380
            )
            st.plotly_chart(fig_u1, use_container_width=True)
        else:
            st.info("No unique words found.")
        st.caption(f"Words used significantly more by {M1} than {M2} (frequency difference).")

    # 공통 단어 표
    with uw_mid:
        st.markdown('<div style="text-align:center; color:#6b7280; font-size:0.85rem; '
                    'font-weight:600; margin-bottom:10px;">🤝 COMMON TOP 10</div>',
                    unsafe_allow_html=True)
        if common_words:
            df_common = pd.DataFrame(common_words, columns=["Word", M1, M2])
            st.dataframe(df_common, use_container_width=True, hide_index=True, height=380)
        else:
            st.info("No common words found.")
        st.caption("Words appearing in the top 50 of both outlets.")

    # 미디어2 고유 단어 가로 바 차트
    with uw_col2:
        st.markdown(f'<div class="media-header m2-header">🟠 {M2} — Unique Top 10</div>',
                    unsafe_allow_html=True)
        if unique_m2:
            u2_words  = [x[0] for x in unique_m2][::-1]
            u2_counts = [x[1] for x in unique_m2][::-1]
            fig_u2 = go.Figure(go.Bar(
                x=u2_counts, y=u2_words, orientation="h",
                marker_color=m2_color, text=u2_counts, textposition="outside",
                textfont=dict(color="#d1d5db", size=10)
            ))
            fig_u2.update_layout(
                paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(17,24,39,0.6)",
                font=dict(color="#9ca3af"), xaxis=dict(color="#6b7280", gridcolor="#1f2937", title="Frequency diff"),
                yaxis=dict(color="#d1d5db", tickfont=dict(size=10)),
                margin=dict(l=5, r=40, t=10, b=20), height=380
            )
            st.plotly_chart(fig_u2, use_container_width=True)
        else:
            st.info("No unique words found.")
        st.caption(f"Words used significantly more by {M2} than {M1} (frequency difference).")

    # 인사이트 박스 (실제 데이터 기반 f-string)
    m1_top_words = ", ".join([f"'{w}'" for w, _ in unique_m1[:2]]) if len(unique_m1) >= 2 else "N/A"
    m2_top_words = ", ".join([f"'{w}'" for w, _ in unique_m2[:2]]) if len(unique_m2) >= 2 else "N/A"
    st.markdown(f"""
    <div class="insight-box">
        💡 <b>Editorial Vocabulary Insight:</b><br>
        <b>{M1}</b> tends to use words like <b>{m1_top_words}</b>,
        suggesting a focus on {', '.join([w for w, _ in unique_m1[:3]]) if unique_m1 else 'similar themes'}.<br>
        Meanwhile, <b>{M2}</b> focuses more on <b>{m2_top_words}</b>,
        indicating a different editorial angle on the same topic '<b>{KEYWORD}</b>'.
    </div>
    """, unsafe_allow_html=True)


# ────────────────────────────────────────
# 탭3: Sentiment Compare
# ────────────────────────────────────────
with tab3:
    st.markdown("#### 😊 Sentiment Analysis Comparison")

    # 도넛 차트 2개
    donut_c1, donut_c2 = st.columns(2)
    sent_color_map = {"Positive": "#22c55e", "Negative": "#ef4444", "Neutral": "#6b7280"}

    for col_d, df_m, media_nm in [(donut_c1, df1, M1), (donut_c2, df2, M2)]:
        with col_d:
            st.markdown(f"##### {media_nm}")
            if df_m.empty:
                st.info("No data.")
                continue
            sc = df_m["sentiment"].value_counts().reset_index()
            sc.columns = ["Sentiment", "Count"]
            fig_pie = go.Figure(go.Pie(
                labels=sc["Sentiment"], values=sc["Count"], hole=0.52,
                marker_colors=[sent_color_map.get(s, "#6b7280") for s in sc["Sentiment"]],
                textfont=dict(size=11, family="Syne")
            ))
            fig_pie.update_layout(
                paper_bgcolor="rgba(0,0,0,0)",
                font=dict(color="#d1d5db"), legend=dict(bgcolor="rgba(0,0,0,0)"),
                margin=dict(t=10, b=10), height=280
            )
            st.plotly_chart(fig_pie, use_container_width=True)

    st.caption("Donut charts show the proportion of positive, negative, and neutral coverage for each outlet.")

    # ── 감성 비율 그룹 바 차트 ──
    st.markdown(f"---\n#### Sentiment Distribution: {M1} vs {M2}")
    sent_cmp_rows = []
    for df_m, media_nm in [(df1, M1), (df2, M2)]:
        if df_m.empty:
            continue
        total = len(df_m)
        for lbl in ["Positive", "Negative", "Neutral"]:
            cnt = len(df_m[df_m["sentiment"] == lbl])
            sent_cmp_rows.append({"Sentiment": lbl, "Percentage": round(cnt / total * 100, 1), "Media": media_nm})
    if sent_cmp_rows:
        df_sent_cmp = pd.DataFrame(sent_cmp_rows)
        fig_scmp = px.bar(
            df_sent_cmp, x="Sentiment", y="Percentage", color="Media", barmode="group",
            color_discrete_map={M1: m1_color, M2: m2_color},
            labels={"Percentage": "%", "Sentiment": ""}
        )
        fig_scmp.update_layout(
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(17,24,39,0.6)",
            font=dict(color="#9ca3af"), xaxis=dict(color="#6b7280"),
            yaxis=dict(color="#6b7280", gridcolor="#1f2937", title="Percentage (%)"),
            legend=dict(bgcolor="rgba(0,0,0,0)", font=dict(color="#d1d5db")),
            margin=dict(t=10, b=20), height=320
        )
        st.plotly_chart(fig_scmp, use_container_width=True)
        st.caption("Grouped bar chart showing how positive, negative, and neutral proportions differ between outlets.")

    # ── 날짜별 감성 추이 라인 차트 ──
    st.markdown("---\n#### Sentiment Trend Over Time")
    fig_trend = go.Figure()
    for df_m, media_nm, col in [(df1, M1, m1_color), (df2, M2, m2_color)]:
        if df_m.empty:
            continue
        daily = df_m.groupby("date")["polarity"].mean().reset_index()
        fig_trend.add_trace(go.Scatter(
            x=daily["date"], y=daily["polarity"],
            mode="lines+markers", name=media_nm,
            line=dict(color=col, width=2),
            marker=dict(size=6)
        ))
    fig_trend.add_hline(y=0, line_dash="dot", line_color="#4b5563", opacity=0.8,
                        annotation_text="Neutral (0)", annotation_font_color="#6b7280")
    fig_trend.update_layout(
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(17,24,39,0.6)",
        font=dict(color="#9ca3af"),
        xaxis=dict(color="#6b7280", gridcolor="#1f2937", title="Date"),
        yaxis=dict(color="#6b7280", gridcolor="#1f2937", title="Avg. Polarity"),
        legend=dict(bgcolor="rgba(0,0,0,0)", font=dict(color="#d1d5db")),
        margin=dict(t=10, b=20), height=320
    )
    st.plotly_chart(fig_trend, use_container_width=True)
    st.caption("Daily average sentiment polarity for each outlet. Grey dashed line = neutral (0).")

    # ── Top 3 긍정/부정 기사 ──
    st.markdown("---")
    neg_c, pos_c = st.columns(2)
    tbl_cols   = ["title", "date", "polarity"]
    tbl_labels = {"title": "Title", "date": "Date", "polarity": "Score"}

    with neg_c:
        st.markdown("##### 😟 Most Negative Articles — Top 3")
        for df_m, media_nm in [(df1, M1), (df2, M2)]:
            if df_m.empty:
                continue
            st.markdown(f"**{media_nm}**")
            bot3 = df_m.nsmallest(3, "polarity")[tbl_cols].copy()
            bot3["date"] = bot3["date"].dt.strftime("%Y-%m-%d")
            st.dataframe(bot3.rename(columns=tbl_labels), use_container_width=True, hide_index=True,
                         column_config={"Score": st.column_config.NumberColumn(format="%.4f")})

    with pos_c:
        st.markdown("##### 😊 Most Positive Articles — Top 3")
        for df_m, media_nm in [(df1, M1), (df2, M2)]:
            if df_m.empty:
                continue
            st.markdown(f"**{media_nm}**")
            top3 = df_m.nlargest(3, "polarity")[tbl_cols].copy()
            top3["date"] = top3["date"].dt.strftime("%Y-%m-%d")
            st.dataframe(top3.rename(columns=tbl_labels), use_container_width=True, hide_index=True,
                         column_config={"Score": st.column_config.NumberColumn(format="%.4f")})

    st.caption("Articles ranked by TextBlob headline polarity score (range −1.0 to +1.0).")


# ────────────────────────────────────────
# 탭4: Headlines Side-by-Side
# ────────────────────────────────────────
with tab4:
    st.markdown("#### 📰 Headlines Side-by-Side")

    # 감성 필터
    sent_filter = st.selectbox(
        "Filter by Sentiment",
        ["All", "Positive", "Negative", "Neutral"],
        key="hl_sent_filter"
    )

    hl_col1, hl_col2 = st.columns(2)

    def render_cards(df_m, media_nm, sent_f):
        """기사 카드 렌더링 (최신 순 상위 20개)"""
        df_f = df_m.copy()
        if sent_f != "All":
            df_f = df_f[df_f["sentiment"] == sent_f]
        df_f = df_f.sort_values("date", ascending=False).head(20)

        if df_f.empty:
            st.info(f"No {sent_f.lower()} articles from {media_nm}.")
            return

        for _, row in df_f.iterrows():
            emoji = {"Positive": "😊", "Negative": "😟"}.get(row["sentiment"], "😐")
            date_str = row["date"].strftime("%b %d, %Y") if pd.notna(row["date"]) else "N/A"
            desc_text = row["description"][:180] + "..." if len(str(row["description"])) > 180 else row["description"]
            st.markdown(f"""
            <div class="article-card">
                <div class="article-title">{row['title']}</div>
                <div class="article-meta">{date_str} &nbsp;·&nbsp; {emoji} {row['sentiment']}
                     &nbsp;·&nbsp; Score: {row['polarity']:+.3f}</div>
                {"<div class='article-desc'>" + desc_text + "</div>" if desc_text else ""}
            </div>
            """, unsafe_allow_html=True)

    with hl_col1:
        st.markdown(f'<div class="media-header m1-header">📺 {M1}</div>', unsafe_allow_html=True)
        render_cards(df1, M1, sent_filter)

    with hl_col2:
        st.markdown(f'<div class="media-header m2-header">📺 {M2}</div>', unsafe_allow_html=True)
        render_cards(df2, M2, sent_filter)

    st.caption("Showing up to 20 most recent articles per outlet. Use the sentiment filter to narrow results.")


# ────────────────────────────────────────
# 탭5: Summary Report
# ────────────────────────────────────────
with tab5:
    st.markdown("#### 📊 Summary Report")

    # 보고서 수치 계산
    def safe_top_words(freq, n=3):
        return [w for w, _ in freq.most_common(n)] if freq else ["N/A"] * n

    top3_m1 = safe_top_words(freq1)
    top3_m2 = safe_top_words(freq2)
    dist_m1 = unique_m1[0][0] if unique_m1 else "N/A"
    dist_m2 = unique_m2[0][0] if unique_m2 else "N/A"
    more_pos = M1 if avg_p1 >= avg_p2 else M2
    tone     = "positively" if max(avg_p1, avg_p2) > 0.05 else "negatively" if max(avg_p1, avg_p2) < -0.05 else "neutrally"

    pos_pct1 = round(len(df1[df1["sentiment"]=="Positive"]) / max(len(df1),1)*100,1) if not df1.empty else 0
    neg_pct1 = round(len(df1[df1["sentiment"]=="Negative"]) / max(len(df1),1)*100,1) if not df1.empty else 0
    pos_pct2 = round(len(df2[df2["sentiment"]=="Positive"]) / max(len(df2),1)*100,1) if not df2.empty else 0
    neg_pct2 = round(len(df2[df2["sentiment"]=="Negative"]) / max(len(df2),1)*100,1) if not df2.empty else 0

    # 요약 텍스트 (학생 발표 스크립트용)
    report_text = f"""MEDIA COMPARISON REPORT
========================
Keyword: "{KEYWORD}"
Generated: {datetime.today().strftime('%Y-%m-%d %H:%M')}

OVERVIEW
--------
This analysis compared how {M1} and {M2} covered the keyword "{KEYWORD}".

{M1} published {len(df1)} articles with an average sentiment score of {avg_p1:+.4f} ({lbl1}).
{M2} published {len(df2)} articles with an average sentiment score of {avg_p2:+.4f} ({lbl2}).

VOCABULARY
----------
The most distinctive word used by {M1} was "{dist_m1}",
while {M2} frequently used "{dist_m2}".

{M1}'s top words: {", ".join(top3_m1)}
{M2}'s top words: {", ".join(top3_m2)}

SENTIMENT
---------
Overall, {more_pos} tended to cover this topic more {tone}.

{M1}: {pos_pct1}% positive, {neg_pct1}% negative
{M2}: {pos_pct2}% positive, {neg_pct2}% negative

The sentiment gap between the two outlets was {abs(delta_sent):.4f} points.

DATA SOURCE: Google News RSS · Analysis: TextBlob NLP · Built with Streamlit
"""

    # 보고서 박스 표시
    st.markdown(f'<div class="report-box"><pre style="font-family:Inter,sans-serif; '
                f'white-space:pre-wrap; margin:0; color:#cbd5e1;">{report_text}</pre></div>',
                unsafe_allow_html=True)

    # 다운로드 버튼
    st.download_button(
        label="⬇️ Download Report as .txt",
        data=report_text,
        file_name=f"media_report_{KEYWORD.replace(' ','_')}_{M1}_vs_{M2}.txt",
        mime="text/plain",
        use_container_width=False
    )

    # 비교 테이블
    st.markdown("---\n#### 📋 Comparison Table")
    compare_table = pd.DataFrame({
        "Metric": [
            "Articles collected", "Avg. sentiment score", "Sentiment label",
            "Positive %", "Negative %",
            "Top keyword 1", "Top keyword 2", "Top keyword 3"
        ],
        M1: [
            len(df1), f"{avg_p1:+.4f}", lbl1,
            f"{pos_pct1}%", f"{neg_pct1}%",
            top3_m1[0], top3_m1[1], top3_m1[2]
        ],
        M2: [
            len(df2), f"{avg_p2:+.4f}", lbl2,
            f"{pos_pct2}%", f"{neg_pct2}%",
            top3_m2[0], top3_m2[1], top3_m2[2]
        ]
    })
    st.dataframe(compare_table, use_container_width=True, hide_index=True)
    st.caption(
        "Summary table of key metrics for both outlets. "
        "Download the full report above to use as a presentation script."
    )


# ──────────────────────────────────────────────
# 11. 푸터
# ──────────────────────────────────────────────
st.markdown("---")
st.markdown(f"""
<div style="text-align:center; color:#1f2937; font-size:0.73rem;
            font-family:'Syne',sans-serif; padding:8px 0 16px;">
    📰 Media Comparison Dashboard · Google News RSS · TextBlob · Plotly · WordCloud<br>
    Comparing <span style="color:#3b82f6;">"{KEYWORD}"</span> across
    <span style="color:{m1_color};">{M1}</span> &amp;
    <span style="color:{m2_color};">{M2}</span>
    · Cache refreshes every 30 min
</div>
""", unsafe_allow_html=True)
