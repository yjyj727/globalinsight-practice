"""
기후변화 뉴스 분석 대시보드 — CNN vs BBC
주제: 기후변화 | 색상 테마: teal/green (#0D7377)
"""

import streamlit as st
import requests
from bs4 import BeautifulSoup
import pandas as pd
from collections import Counter
import re
from datetime import datetime, timedelta
import plotly.express as px
import plotly.graph_objects as go
from textblob import TextBlob

# ──────────────────────────────────────────────
# 0. 페이지 설정
# ──────────────────────────────────────────────
st.set_page_config(
    page_title="Climate Change News Analysis",
    page_icon="📰",
    layout="wide"
)

# ──────────────────────────────────────────────
# 1. 전역 상수 설정
# ──────────────────────────────────────────────
TOPIC = "기후변화"
MEDIA1_NAME = "CNN"
MEDIA2_NAME = "BBC"

# 주제 + 미디어 조합에 따른 RSS URL
MEDIA1_RSS = "http://rss.cnn.com/rss/edition_world.rss"          # CNN + 기후변화 → 기타(world)
MEDIA2_RSS = "http://feeds.bbci.co.uk/news/science_and_environment/rss.xml"  # BBC + 기후변화

# 기후변화 강조 키워드
HIGHLIGHT_KEYWORDS = {
    "climate", "carbon", "emissions", "temperature",
    "fossil", "renewable", "flood", "wildfire", "drought"
}

# 색상 테마 (기후변화 → teal/green)
PRIMARY_COLOR = "#0D7377"
COLOR_MEDIA1 = "#14FFEC"   # CNN 차트 색상 (밝은 teal)
COLOR_MEDIA2 = "#0D7377"   # BBC 차트 색상 (진한 teal)
COLOR_HIGHLIGHT = "#F4A261"  # 강조 키워드 색상 (오렌지 포인트)

# 불용어 목록 (키워드 분석 시 제외)
STOPWORDS = {
    "the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for",
    "of", "with", "by", "from", "as", "is", "was", "are", "were", "be",
    "been", "being", "have", "has", "had", "do", "does", "did", "will",
    "would", "could", "should", "may", "might", "shall", "can", "need",
    "that", "this", "it", "its", "he", "she", "they", "we", "you", "i",
    "his", "her", "their", "our", "your", "my", "not", "no", "nor",
    "so", "yet", "both", "either", "neither", "each", "few", "more",
    "most", "other", "some", "such", "than", "too", "very", "just",
    "about", "after", "before", "between", "into", "through", "during",
    "up", "down", "out", "off", "over", "under", "again", "then",
    "once", "here", "there", "when", "where", "why", "how", "all",
    "also", "said", "says", "new", "us", "s", "what", "who", "which",
    "if", "while", "including", "amid", "more", "has", "say", "one",
    "two", "three", "first", "last", "year", "years", "day", "days",
    "time", "week", "month", "world", "people", "government"
}

# ──────────────────────────────────────────────
# 2. 커스텀 CSS 스타일링
# ──────────────────────────────────────────────
st.markdown(f"""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Space+Mono:wght@400;700&family=DM+Sans:wght@300;400;500;700&display=swap');

    html, body, [class*="css"] {{
        font-family: 'DM Sans', sans-serif;
    }}

    .main {{
        background-color: #0A0F0F;
        color: #E0F2F1;
    }}

    .stApp {{
        background-color: #0A0F0F;
    }}

    h1, h2, h3 {{
        font-family: 'Space Mono', monospace !important;
        color: {PRIMARY_COLOR} !important;
    }}

    .metric-card {{
        background: linear-gradient(135deg, #0D2626 0%, #0D3B3B 100%);
        border: 1px solid {PRIMARY_COLOR};
        border-radius: 8px;
        padding: 20px;
        text-align: center;
        box-shadow: 0 0 20px rgba(13,115,119,0.2);
    }}

    .metric-value {{
        font-family: 'Space Mono', monospace;
        font-size: 2.5rem;
        font-weight: 700;
        color: #14FFEC;
        margin: 0;
    }}

    .metric-label {{
        font-size: 0.85rem;
        color: #80CBC4;
        margin-top: 4px;
        letter-spacing: 0.05em;
        text-transform: uppercase;
    }}

    .insight-box {{
        background: #0D2626;
        border-left: 3px solid {PRIMARY_COLOR};
        padding: 14px 18px;
        border-radius: 4px;
        margin-bottom: 10px;
        font-size: 0.9rem;
        color: #B2DFDB;
    }}

    .header-badge {{
        display: inline-block;
        background: {PRIMARY_COLOR};
        color: #000;
        font-family: 'Space Mono', monospace;
        font-size: 0.7rem;
        font-weight: 700;
        padding: 3px 10px;
        border-radius: 20px;
        margin-right: 8px;
        letter-spacing: 0.08em;
    }}

    .stTabs [data-baseweb="tab-list"] {{
        gap: 4px;
        background: #0D1A1A;
        border-radius: 8px;
        padding: 4px;
    }}

    .stTabs [data-baseweb="tab"] {{
        background: transparent;
        color: #80CBC4;
        border-radius: 6px;
        font-family: 'Space Mono', monospace;
        font-size: 0.8rem;
    }}

    .stTabs [aria-selected="true"] {{
        background: {PRIMARY_COLOR} !important;
        color: #000 !important;
    }}

    div[data-testid="stDataFrame"] {{
        background: #0D1A1A;
        border-radius: 8px;
    }}

    .stSidebar {{
        background: #0A1414 !important;
    }}

    .stSidebar .stMarkdown {{
        color: #80CBC4;
    }}

    .sample-data-notice {{
        background: #1A2626;
        border: 1px dashed #0D7377;
        border-radius: 6px;
        padding: 10px 16px;
        color: #80CBC4;
        font-size: 0.8rem;
        margin-bottom: 16px;
    }}
</style>
""", unsafe_allow_html=True)


# ──────────────────────────────────────────────
# 3. RSS 데이터 수집 함수
# ──────────────────────────────────────────────
@st.cache_data(ttl=3600)
def fetch_rss(url: str, media_name: str) -> pd.DataFrame:
    """RSS XML을 파싱해 DataFrame으로 반환. 실패 시 샘플 데이터 반환."""
    try:
        headers = {"User-Agent": "Mozilla/5.0 (compatible; NewsBot/1.0)"}
        resp = requests.get(url, headers=headers, timeout=15)
        resp.raise_for_status()

        soup = BeautifulSoup(resp.content, "xml")
        items = soup.find_all("item")

        if not items:
            raise ValueError("기사 항목이 없습니다.")

        records = []
        for item in items[:50]:  # 최대 50개
            title = item.find("title")
            pub_date = item.find("pubDate")
            description = item.find("description")
            link = item.find("link")

            # 날짜 파싱
            date_str = pub_date.get_text(strip=True) if pub_date else ""
            try:
                parsed_date = datetime.strptime(date_str[:25], "%a, %d %b %Y %H:%M:%S")
            except Exception:
                try:
                    parsed_date = datetime.strptime(date_str[:16], "%Y-%m-%dT%H:%M")
                except Exception:
                    parsed_date = datetime.now() - timedelta(days=len(records))

            # HTML 태그 제거
            desc_raw = description.get_text(strip=True) if description else ""
            desc_clean = re.sub(r"<[^>]+>", "", desc_raw)[:300]

            records.append({
                "title": title.get_text(strip=True) if title else "N/A",
                "date": parsed_date,
                "description": desc_clean,
                "link": link.get_text(strip=True) if link else "",
                "media": media_name
            })

        df = pd.DataFrame(records)
        df["date"] = pd.to_datetime(df["date"])
        return df, False  # (데이터프레임, 샘플여부)

    except Exception as e:
        # 수집 실패 시 샘플 데이터로 전환
        return _generate_sample_data(media_name), True


def _generate_sample_data(media_name: str) -> pd.DataFrame:
    """RSS 수집 실패 시 사용할 샘플 데이터 생성"""
    if media_name == "CNN":
        titles = [
            "Climate crisis: Record heat wave sweeps across three continents",
            "Carbon emissions hit new high despite renewable energy growth",
            "Wildfire season worsens as drought conditions persist in West",
            "Scientists warn of irreversible tipping points in climate system",
            "Fossil fuel companies face mounting pressure from investors",
            "Flood damage costs surge as extreme weather events multiply",
            "Renewable energy investment reaches record $1 trillion globally",
            "UN climate report: Temperature rise threatens global food supply",
            "Arctic sea ice hits lowest extent ever recorded in September",
            "Climate migrants: 200 million people displaced by 2050, study says",
            "Electric vehicle adoption accelerates despite battery concerns",
            "Methane emissions from agriculture far higher than estimated",
            "Coral reefs face extinction threat as ocean temperatures rise",
            "Green hydrogen: The fuel of the future or expensive distraction?",
            "Climate finance gap widens as wealthy nations fall short on pledges",
        ]
        descriptions = [
            "Unprecedented temperatures recorded across Europe, North America, and Asia as scientists link extreme heat to accelerating climate change.",
            "Global carbon dioxide levels continue rising despite pledges, with fossil fuel combustion remaining the primary driver of emissions growth.",
            "Hundreds of thousands of acres burning across western states as years of drought deplete soil moisture and fuel record-breaking fire seasons.",
            "New research published in Nature identifies six critical climate tipping points that could trigger cascading effects irreversible for centuries.",
            "Major institutional investors are divesting from oil and gas holdings, citing stranded asset risks as clean energy transition accelerates.",
            "Economic losses from flooding events doubled over the past decade, with developing nations bearing disproportionate costs of climate damage.",
            "Solar and wind power capacity additions broke records for the fifth consecutive year, signaling a fundamental shift in energy markets.",
            "The latest IPCC assessment warns current policies will lead to 2.5°C warming, causing severe disruptions to agriculture and water supplies.",
            "Satellite measurements confirm Arctic ice minimum reached a new record low, accelerating sea level rise and disrupting global weather patterns.",
            "Climate-driven displacement will create the largest refugee crisis in human history, straining international systems and national borders.",
            "EV sales jumped 40% year-over-year, but questions remain about supply chains, grid capacity, and the environmental cost of battery production.",
            "Livestock and rice cultivation produce significantly more methane than previously measured, complicating net-zero targets for many countries.",
            "Mass bleaching events now affect 80% of the world's coral reefs, with scientists calling the damage largely irreversible without rapid action.",
            "Green hydrogen projects are multiplying globally, but analysts debate whether the technology can scale fast enough to meet climate targets.",
            "Developed nations have pledged $100 billion annually for climate adaptation but disbursements remain far below commitments made in 2009.",
        ]
    else:  # BBC
        titles = [
            "Climate change: UK summer 2024 among hottest on record",
            "Net zero: Britain's energy transition faces critical challenges",
            "Flooding threatens homes across Bangladesh as monsoon intensifies",
            "COP negotiations stall over loss and damage compensation fund",
            "Renewable energy: Scotland reaches 100% wind power milestone",
            "Drought grips southern Europe, threatening agriculture and tourism",
            "Climate anxiety: Young people's mental health crisis explained",
            "Carbon capture: Can technology save us from climate disaster?",
            "Polar ice melt accelerating faster than models predicted",
            "Biodiversity and climate: How extinction worsens global warming",
            "Green belt development row highlights UK planning dilemma",
            "Pacific Island nations face existential threat from rising seas",
            "Climate-smart agriculture: Feeding the world sustainably",
            "Air pollution linked to millions of deaths globally each year",
            "Energy poverty: Millions struggle to heat homes amid crisis",
        ]
        descriptions = [
            "Met Office data confirms last summer ranked among the five warmest ever recorded in the UK, with multiple temperature records broken in July.",
            "Analysis reveals the UK faces significant hurdles in meeting its legally binding net zero target by 2050, including grid infrastructure and public acceptance.",
            "Torrential monsoon rains have inundated one-third of Bangladesh, displacing millions and devastating crops in one of the world's most climate-vulnerable nations.",
            "Talks between wealthy and developing nations over who pays for climate-related loss and damage have broken down again ahead of the next COP summit.",
            "Scotland's electricity grid ran entirely on wind power for several consecutive days, marking a symbolic milestone in the nation's clean energy journey.",
            "Severe drought is gripping Spain, Portugal and southern Italy, leading to water restrictions, crop failures and rising food prices across the region.",
            "Research shows record numbers of young people report feeling hopeless about the climate future, with many saying it influences their life decisions.",
            "Scientists are divided on whether carbon capture and storage technology can be deployed at sufficient scale to compensate for continued fossil fuel use.",
            "New satellite analysis shows glaciers in Greenland and Antarctica are losing ice at rates 40% faster than those projected by climate models a decade ago.",
            "Studies increasingly show the loss of species and ecosystems reduces natural carbon sequestration, creating a dangerous feedback loop with warming temperatures.",
            "The government's proposal to build housing on parts of the green belt has reignited debate about land use, planning rules and environmental protections.",
            "Leaders of Tuvalu, Kiribati and Marshall Islands call for urgent international action as saltwater intrusion, flooding and erosion threaten their existence.",
            "Researchers are developing drought-resistant crops, precision irrigation systems and low-emission farming techniques to feed a growing population sustainably.",
            "A comprehensive global study attributes 8 million premature deaths annually to air pollution, with fossil fuel combustion identified as the primary cause.",
            "Millions of households across Europe and the UK are in fuel poverty, unable to afford adequate heating — a crisis intensified by energy market disruptions.",
        ]

    base_date = datetime.now() - timedelta(days=3)
    records = []
    for i, (t, d) in enumerate(zip(titles, descriptions)):
        records.append({
            "title": t,
            "date": base_date - timedelta(hours=i * 8),
            "description": d,
            "link": f"https://example.com/{media_name.lower()}/article-{i}",
            "media": media_name
        })
    return pd.DataFrame(records)


# ──────────────────────────────────────────────
# 4. 텍스트 처리 유틸리티
# ──────────────────────────────────────────────
def extract_keywords(texts: list, top_n: int = 20) -> Counter:
    """텍스트 리스트에서 상위 N개 키워드 추출"""
    all_words = []
    for text in texts:
        words = re.findall(r"\b[a-zA-Z]{3,}\b", str(text).lower())
        all_words.extend([w for w in words if w not in STOPWORDS])
    return Counter(all_words).most_common(top_n)


def get_sentiment(text: str) -> dict:
    """TextBlob으로 감성 분석 → polarity, label 반환"""
    try:
        blob = TextBlob(str(text))
        polarity = blob.sentiment.polarity
        if polarity > 0.05:
            label = "Positive"
        elif polarity < -0.05:
            label = "Negative"
        else:
            label = "Neutral"
        return {"polarity": polarity, "label": label}
    except Exception:
        return {"polarity": 0.0, "label": "Neutral"}


# ──────────────────────────────────────────────
# 5. 데이터 로드
# ──────────────────────────────────────────────
with st.spinner("📡 뉴스 데이터를 수집 중입니다..."):
    df1_raw, is_sample1 = fetch_rss(MEDIA1_RSS, MEDIA1_NAME)
    df2_raw, is_sample2 = fetch_rss(MEDIA2_RSS, MEDIA2_NAME)

df_all_raw = pd.concat([df1_raw, df2_raw], ignore_index=True)

# 감성 분석 적용
df_all_raw["sentiment_data"] = df_all_raw["title"].apply(
    lambda x: get_sentiment(x + " " + x)
)
df_all_raw["polarity"] = df_all_raw["sentiment_data"].apply(lambda x: x["polarity"])
df_all_raw["sentiment"] = df_all_raw["sentiment_data"].apply(lambda x: x["label"])
df_all_raw.drop(columns=["sentiment_data"], inplace=True)


# ──────────────────────────────────────────────
# 6. 사이드바
# ──────────────────────────────────────────────
with st.sidebar:
    st.markdown(f"""
    <div style="text-align:center; padding: 10px 0 20px;">
        <div style="font-family:'Space Mono',monospace; font-size:1.1rem;
                    color:{PRIMARY_COLOR}; font-weight:700;">📰 NEWS LENS</div>
        <div style="color:#80CBC4; font-size:0.75rem; margin-top:4px;">
            Climate Change Edition
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("### 🗓️ 날짜 범위")

    if not df_all_raw.empty:
        min_date = df_all_raw["date"].min().date()
        max_date = df_all_raw["date"].max().date()
        delta_days = max(1, (max_date - min_date).days)

        date_range = st.slider(
            "분석 기간 선택",
            min_value=0,
            max_value=delta_days,
            value=(0, delta_days),
            format="%d days ago"
        )
        filter_start = max_date - timedelta(days=date_range[1])
        filter_end = max_date - timedelta(days=date_range[0])
    else:
        filter_start = datetime.now().date() - timedelta(days=30)
        filter_end = datetime.now().date()

    st.markdown("### 📺 미디어 선택")
    show_m1 = st.checkbox(f"✅ {MEDIA1_NAME}", value=True)
    show_m2 = st.checkbox(f"✅ {MEDIA2_NAME}", value=True)

    st.markdown("---")
    st.markdown("### ℹ️ About")
    st.markdown(f"""
    <div style="color:#80CBC4; font-size:0.8rem; line-height:1.6;">
        <b style="color:{PRIMARY_COLOR};">주제:</b> 기후변화<br>
        <b style="color:{PRIMARY_COLOR};">미디어:</b> CNN vs BBC<br>
        <b style="color:{PRIMARY_COLOR};">갱신 주기:</b> 1시간<br>
        <b style="color:{PRIMARY_COLOR};">분석 도구:</b> TextBlob, Plotly<br><br>
        RSS 수집 실패 시 샘플 데이터가 자동으로 사용됩니다.
    </div>
    """, unsafe_allow_html=True)


# ──────────────────────────────────────────────
# 7. 날짜 필터링 적용
# ──────────────────────────────────────────────
df_all = df_all_raw.copy()
df_all = df_all[
    (df_all["date"].dt.date >= filter_start) &
    (df_all["date"].dt.date <= filter_end)
]

# 미디어 선택 필터
active_media = []
if show_m1:
    active_media.append(MEDIA1_NAME)
if show_m2:
    active_media.append(MEDIA2_NAME)

if active_media:
    df_all = df_all[df_all["media"].isin(active_media)]

df1 = df_all[df_all["media"] == MEDIA1_NAME]
df2 = df_all[df_all["media"] == MEDIA2_NAME]


# ──────────────────────────────────────────────
# 8. 헤더
# ──────────────────────────────────────────────
st.markdown(f"""
<div style="padding: 30px 0 10px;">
    <span class="header-badge">CLIMATE CHANGE</span>
    <span class="header-badge">CNN vs BBC</span>
    <span class="header-badge">LIVE ANALYSIS</span>
</div>
<h1 style="font-size:2.2rem; margin:0; line-height:1.2;">
    Climate Change<br>
    <span style="color:#14FFEC;">News Analysis</span> Dashboard
</h1>
<p style="color:#80CBC4; margin-top:8px; font-size:0.9rem;">
    Real-time comparative analysis of climate coverage across major news networks
</p>
""", unsafe_allow_html=True)

# 샘플 데이터 알림
if is_sample1 or is_sample2:
    sample_names = []
    if is_sample1:
        sample_names.append(MEDIA1_NAME)
    if is_sample2:
        sample_names.append(MEDIA2_NAME)
    st.markdown(f"""
    <div class="sample-data-notice">
        ⚠️ <b>{', '.join(sample_names)}</b> — RSS 수집에 실패하여 샘플 데이터로 분석합니다.
        실제 환경에서 RSS 엔드포인트에 접근이 허용되면 라이브 데이터가 표시됩니다.
    </div>
    """, unsafe_allow_html=True)

st.markdown("---")


# ──────────────────────────────────────────────
# 9. 상단 메트릭 (3열)
# ──────────────────────────────────────────────
col_m1, col_m2, col_m3 = st.columns(3)

analysis_period = f"{filter_start.strftime('%b %d')} – {filter_end.strftime('%b %d, %Y')}"

with col_m1:
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-value" style="color:#14FFEC;">{len(df1)}</div>
        <div class="metric-label">📺 {MEDIA1_NAME} Articles</div>
    </div>
    """, unsafe_allow_html=True)

with col_m2:
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-value" style="color:#0D7377;">{len(df2)}</div>
        <div class="metric-label">📡 {MEDIA2_NAME} Articles</div>
    </div>
    """, unsafe_allow_html=True)

with col_m3:
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-value" style="color:#80CBC4; font-size:1.5rem;">{analysis_period}</div>
        <div class="metric-label">📅 Analysis Period</div>
    </div>
    """, unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)


# ──────────────────────────────────────────────
# 10. 탭 구성
# ──────────────────────────────────────────────
tab1, tab2, tab3 = st.tabs(["📋  Data", "🔤  Keywords", "😊  Sentiment"])


# ── 탭1: Data ──────────────────────────────────
with tab1:
    st.markdown("#### 📋 수집된 기사 목록")

    if df_all.empty:
        st.warning("선택한 조건에 해당하는 기사가 없습니다.")
    else:
        # 표시용 컬럼 정리
        display_df = df_all[["media", "date", "title", "description", "sentiment"]].copy()
        display_df["date"] = display_df["date"].dt.strftime("%Y-%m-%d %H:%M")
        display_df.columns = ["Media", "Date", "Title", "Description", "Sentiment"]

        st.dataframe(
            display_df,
            use_container_width=True,
            height=420,
            column_config={
                "Media": st.column_config.TextColumn("Media", width="small"),
                "Date": st.column_config.TextColumn("Date", width="medium"),
                "Title": st.column_config.TextColumn("Title", width="large"),
                "Description": st.column_config.TextColumn("Description", width="large"),
                "Sentiment": st.column_config.TextColumn("Sentiment", width="small"),
            }
        )

        st.caption(
            f"Showing {len(df_all)} articles collected from {MEDIA1_NAME} and {MEDIA2_NAME} "
            f"between {filter_start} and {filter_end}."
        )


# ── 탭2: Keywords ──────────────────────────────
with tab2:
    st.markdown("#### 🔤 미디어별 상위 키워드 비교")

    kw_col1, kw_col2 = st.columns(2)

    for col_widget, df_media, media_name, bar_color in [
        (kw_col1, df1, MEDIA1_NAME, COLOR_MEDIA1),
        (kw_col2, df2, MEDIA2_NAME, COLOR_MEDIA2)
    ]:
        with col_widget:
            st.markdown(f"##### 📺 {media_name}")

            if df_media.empty:
                st.info(f"{media_name} 기사가 없습니다.")
                continue

            # 제목 + 설명 텍스트 합치기
            texts = (df_media["title"] + " " + df_media["description"]).tolist()
            top_keywords = extract_keywords(texts, top_n=20)

            if not top_keywords:
                st.info("키워드를 추출할 수 없습니다.")
                continue

            kw_words = [kw[0] for kw in top_keywords]
            kw_counts = [kw[1] for kw in top_keywords]

            # 강조 키워드 색상 분리
            colors = [
                COLOR_HIGHLIGHT if w in HIGHLIGHT_KEYWORDS else bar_color
                for w in kw_words
            ]

            fig_kw = go.Figure(go.Bar(
                x=kw_counts[::-1],
                y=kw_words[::-1],
                orientation="h",
                marker_color=colors[::-1],
                text=kw_counts[::-1],
                textposition="outside",
                textfont=dict(size=10, color="#B2DFDB")
            ))

            fig_kw.update_layout(
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(13,26,26,0.8)",
                font=dict(color="#B2DFDB", family="DM Sans"),
                xaxis=dict(
                    title="Frequency",
                    color="#80CBC4",
                    gridcolor="#0D3B3B",
                    showgrid=True
                ),
                yaxis=dict(color="#B2DFDB", tickfont=dict(size=10)),
                margin=dict(l=10, r=40, t=20, b=30),
                height=480,
                showlegend=False
            )

            st.plotly_chart(fig_kw, use_container_width=True)
            st.caption(
                f"Top 20 keywords in {media_name}'s climate coverage. "
                f"Highlighted bars (orange) indicate climate-specific keywords: "
                f"{', '.join(HIGHLIGHT_KEYWORDS)}."
            )

    # 공통 강조 키워드 비교 차트
    st.markdown("---")
    st.markdown("#### 🌍 기후 핵심 키워드 출현 빈도 비교")

    compare_data = []
    for df_media, media_name in [(df1, MEDIA1_NAME), (df2, MEDIA2_NAME)]:
        if df_media.empty:
            continue
        texts = (df_media["title"] + " " + df_media["description"]).tolist()
        all_text = " ".join(texts).lower()
        for kw in sorted(HIGHLIGHT_KEYWORDS):
            count = len(re.findall(r"\b" + kw + r"\b", all_text))
            compare_data.append({"keyword": kw, "count": count, "media": media_name})

    if compare_data:
        df_compare = pd.DataFrame(compare_data)
        fig_compare = px.bar(
            df_compare,
            x="keyword",
            y="count",
            color="media",
            barmode="group",
            color_discrete_map={MEDIA1_NAME: COLOR_MEDIA1, MEDIA2_NAME: COLOR_MEDIA2},
            labels={"count": "Frequency", "keyword": "Keyword", "media": "Media"}
        )
        fig_compare.update_layout(
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(13,26,26,0.8)",
            font=dict(color="#B2DFDB", family="DM Sans"),
            xaxis=dict(color="#80CBC4", gridcolor="#0D3B3B"),
            yaxis=dict(color="#80CBC4", gridcolor="#0D3B3B"),
            legend=dict(
                bgcolor="rgba(13,26,26,0.8)",
                bordercolor="#0D7377",
                borderwidth=1,
                font=dict(color="#B2DFDB")
            ),
            margin=dict(t=20, b=20),
            height=360
        )
        st.plotly_chart(fig_compare, use_container_width=True)
        st.caption(
            "Side-by-side comparison of how frequently CNN and BBC use key climate-related terms. "
            "Higher bars indicate a stronger editorial focus on that specific topic."
        )


# ── 탭3: Sentiment ─────────────────────────────
with tab3:
    st.markdown("#### 😊 감성 분석 — 기사 톤 비교")

    sent_col1, sent_col2 = st.columns(2)

    sentiment_colors = {
        "Positive": "#14FFEC",
        "Neutral": "#80CBC4",
        "Negative": "#F4A261"
    }

    for col_widget, df_media, media_name in [
        (sent_col1, df1, MEDIA1_NAME),
        (sent_col2, df2, MEDIA2_NAME)
    ]:
        with col_widget:
            st.markdown(f"##### 📺 {media_name}")

            if df_media.empty:
                st.info(f"{media_name} 기사가 없습니다.")
                continue

            sent_counts = df_media["sentiment"].value_counts().reset_index()
            sent_counts.columns = ["Sentiment", "Count"]

            fig_pie = px.pie(
                sent_counts,
                names="Sentiment",
                values="Count",
                color="Sentiment",
                color_discrete_map=sentiment_colors,
                hole=0.45
            )
            fig_pie.update_traces(
                textfont=dict(color="#000", size=12, family="Space Mono"),
                textinfo="label+percent"
            )
            fig_pie.update_layout(
                paper_bgcolor="rgba(0,0,0,0)",
                font=dict(color="#B2DFDB", family="DM Sans"),
                showlegend=True,
                legend=dict(
                    bgcolor="rgba(0,0,0,0)",
                    font=dict(color="#B2DFDB")
                ),
                margin=dict(t=20, b=20),
                height=320
            )
            st.plotly_chart(fig_pie, use_container_width=True)
            st.caption(
                f"Sentiment distribution of {media_name} headlines analyzed using TextBlob polarity scoring. "
                "Polarity > 0.05 = Positive, < -0.05 = Negative, otherwise Neutral."
            )

    # 상위/하위 감성 기사
    st.markdown("---")
    top_col, bot_col = st.columns(2)

    with top_col:
        st.markdown("##### 🌟 가장 긍정적 기사 Top 3")
        for df_media, media_name in [(df1, MEDIA1_NAME), (df2, MEDIA2_NAME)]:
            if df_media.empty:
                continue
            st.markdown(f"**{media_name}**")
            top3 = df_media.nlargest(3, "polarity")[["title", "polarity"]]
            for _, row in top3.iterrows():
                st.markdown(f"""
                <div style="background:#0D3B2A; border-left:3px solid #14FFEC;
                            padding:8px 12px; border-radius:4px; margin:4px 0;
                            font-size:0.85rem; color:#B2DFDB;">
                    {row['title']}<br>
                    <span style="color:#14FFEC; font-size:0.75rem;">
                        Polarity: {row['polarity']:.3f}
                    </span>
                </div>
                """, unsafe_allow_html=True)

    with bot_col:
        st.markdown("##### ⚡ 가장 부정적 기사 Top 3")
        for df_media, media_name in [(df1, MEDIA1_NAME), (df2, MEDIA2_NAME)]:
            if df_media.empty:
                continue
            st.markdown(f"**{media_name}**")
            bot3 = df_media.nsmallest(3, "polarity")[["title", "polarity"]]
            for _, row in bot3.iterrows():
                st.markdown(f"""
                <div style="background:#3B1A0D; border-left:3px solid #F4A261;
                            padding:8px 12px; border-radius:4px; margin:4px 0;
                            font-size:0.85rem; color:#B2DFDB;">
                    {row['title']}<br>
                    <span style="color:#F4A261; font-size:0.75rem;">
                        Polarity: {row['polarity']:.3f}
                    </span>
                </div>
                """, unsafe_allow_html=True)

    st.caption(
        "Articles ranked by TextBlob sentiment polarity score (range: -1.0 to +1.0). "
        "Scores reflect the emotional tone of headlines, not editorial quality."
    )


# ──────────────────────────────────────────────
# 11. Key Insights 섹션
# ──────────────────────────────────────────────
st.markdown("---")
st.markdown("### 💡 Key Insights")

# 강조 키워드 비교 계산
def count_keyword_in_df(df_media, keyword):
    if df_media.empty:
        return 0
    all_text = " ".join((df_media["title"] + " " + df_media["description"]).tolist()).lower()
    return len(re.findall(r"\b" + keyword + r"\b", all_text))

crisis_count_m1 = count_keyword_in_df(df1, "climate")
crisis_count_m2 = count_keyword_in_df(df2, "climate")
fossil_m1 = count_keyword_in_df(df1, "fossil")
fossil_m2 = count_keyword_in_df(df2, "fossil")
renewable_m1 = count_keyword_in_df(df1, "renewable")
renewable_m2 = count_keyword_in_df(df2, "renewable")

# 감성 통계
def sentiment_pct(df_media, label):
    if df_media.empty or len(df_media) == 0:
        return 0.0
    return round(len(df_media[df_media["sentiment"] == label]) / len(df_media) * 100, 1)

neg_m1 = sentiment_pct(df1, "Negative")
neg_m2 = sentiment_pct(df2, "Negative")
pos_m1 = sentiment_pct(df1, "Positive")
pos_m2 = sentiment_pct(df2, "Positive")

# 평균 기사 길이
avg_len_m1 = int(df1["description"].str.len().mean()) if not df1.empty else 0
avg_len_m2 = int(df2["description"].str.len().mean()) if not df2.empty else 0

insight_col1, insight_col2, insight_col3 = st.columns(3)

with insight_col1:
    st.markdown(f"""
    <div class="insight-box">
        🌡️ <b>Climate Focus:</b><br>
        {MEDIA1_NAME} used the word <b>"climate"</b> <b style="color:#14FFEC;">{crisis_count_m1} times</b>,
        while {MEDIA2_NAME} used it <b style="color:#0D7377;">{crisis_count_m2} times</b>.
        {'CNN leads in raw climate keyword usage.' if crisis_count_m1 > crisis_count_m2 else 'BBC leads in raw climate keyword usage.'}
    </div>
    """, unsafe_allow_html=True)

with insight_col2:
    st.markdown(f"""
    <div class="insight-box">
        😟 <b>Negative Tone:</b><br>
        {MEDIA1_NAME} reported with a negative tone in
        <b style="color:#F4A261;">{neg_m1}%</b> of articles,
        compared to <b style="color:#F4A261;">{neg_m2}%</b> for {MEDIA2_NAME}.
        {'CNN takes a more alarming editorial stance.' if neg_m1 > neg_m2 else 'BBC takes a more alarming editorial stance.'}
    </div>
    """, unsafe_allow_html=True)

with insight_col3:
    st.markdown(f"""
    <div class="insight-box">
        ♻️ <b>Solution Focus:</b><br>
        {MEDIA1_NAME} mentioned <b>"renewable"</b> <b style="color:#14FFEC;">{renewable_m1} times</b>
        vs {MEDIA2_NAME}'s <b style="color:#0D7377;">{renewable_m2} times</b>.
        {'CNN gives more coverage to clean energy solutions.' if renewable_m1 > renewable_m2 else 'BBC gives more coverage to clean energy solutions.'}
    </div>
    """, unsafe_allow_html=True)


# ──────────────────────────────────────────────
# 12. 푸터
# ──────────────────────────────────────────────
st.markdown("---")
st.markdown(f"""
<div style="text-align:center; color:#3D7070; font-size:0.75rem;
            font-family:'Space Mono',monospace; padding:10px 0 20px;">
    📰 Climate Change News Lens · CNN vs BBC · Powered by Streamlit + TextBlob + Plotly<br>
    Data refreshes every hour · Built for comparative media analysis
</div>
""", unsafe_allow_html=True)
