import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime
import os

st.set_page_config(page_title="맘스패치 ERP", page_icon="🟢", layout="wide")

DB_FILE = "momspatch.db"

# =========================
# 카카오 스타일 CSS
# =========================
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@300;400;500;700&display=swap');

html, body, [class*="css"] {
    font-family: 'Noto Sans KR', sans-serif;
}

/* 전체 배경 */
.stApp {
    background-color: #F9F9F9;
}

/* 사이드바 */
section[data-testid="stSidebar"] {
    background-color: #FFFFFF;
    border-right: 1px solid #EEEEEE;
}

section[data-testid="stSidebar"] .stRadio > label {
    font-size: 15px;
    font-weight: 500;
    color: #333333;
}

/* 제목 */
h1 { color: #2D2D2D !important; font-weight: 700 !important; letter-spacing: -0.5px; }
h2 { color: #2D2D2D !important; font-weight: 600 !important; }
h3 { color: #3C3C3C !important; font-weight: 600 !important; }

/* 버튼 */
.stButton > button {
    background-color: #FEE500 !important;
    color: #2D2D2D !important;
    border: none !important;
    border-radius: 12px !important;
    font-weight: 700 !important;
    font-size: 14px !important;
    padding: 10px 24px !important;
    transition: all 0.2s ease !important;
    box-shadow: 0 2px 8px rgba(0,0,0,0.08) !important;
}
.stButton > button:hover {
    background-color: #F5DC00 !important;
    transform: translateY(-1px) !important;
    box-shadow: 0 4px 12px rgba(0,0,0,0.15) !important;
}

/* 입력 필드 */
.stTextInput > div > div > input,
.stNumberInput > div > div > input,
.stDateInput > div > div > input {
    border-radius: 10px !important;
    border: 1.5px solid #E0E0E0 !important;
    padding: 10px 14px !important;
    font-size: 14px !important;
    transition: border-color 0.2s !important;
}
.stTextInput > div > div > input:focus,
.stNumberInput > div > div > input:focus {
    border-color: #FEE500 !important;
    box-shadow: 0 0 0 3px rgba(254,229,0,0.2) !important;
}

/* 셀렉트박스 */
.stSelectbox > div > div {
    border-radius: 10px !important;
    border: 1.5px solid #E0E0E0 !important;
}

/* 카드 스타일 */
.metric-card {
    background: #FFFFFF;
    border-radius: 16px;
    padding: 20px 24px;
    box-shadow: 0 2px 12px rgba(0,0,0,0.06);
    border: 1px solid #F0F0F0;
    transition: transform 0.2s ease, box-shadow 0.2s ease;
}
.metric-card:hover {
    transform: translateY(-2px);
    box-shadow: 0 6px 20px rgba(0,0,0,0.1);
}
.metric-label {
    font-size: 13px;
    color: #888888;
    font-weight: 500;
    margin-bottom: 6px;
}
.metric-value {
    font-size: 26px;
    font-weight: 700;
    color: #2D2D2D;
}
.metric-sub {
    font-size: 12px;
    color: #AAAAAA;
    margin-top: 4px;
}
.metric-icon {
    font-size: 28px;
    margin-bottom: 8px;
}

/* 섹션 헤더 */
.section-header {
    background: linear-gradient(135deg, #FEE500 0%, #FFD700 100%);
    border-radius: 12px;
    padding: 16px 20px;
    margin-bottom: 20px;
    font-weight: 700;
    font-size: 16px;
    color: #2D2D2D;
    box-shadow: 0 2px 8px rgba(254,229,0,0.3);
}

/* 폼 카드 */
.form-card {
    background: #FFFFFF;
    border-radius: 20px;
    padding: 28px;
    box-shadow: 0 4px 20px rgba(0,0,0,0.06);
    border: 1px solid #F0F0F0;
    margin-bottom: 16px;
}

/* 성공 메시지 */
.stSuccess {
    border-radius: 10px !important;
}

/* 데이터프레임 */
.stDataFrame {
    border-radius: 12px !important;
    overflow: hidden !important;
}

/* 탭 */
.stTabs [data-baseweb="tab-list"] {
    background-color: #F5F5F5;
    border-radius: 12px;
    padding: 4px;
}
.stTabs [data-baseweb="tab"] {
    border-radius: 10px !important;
    font-weight: 600 !important;
}
.stTabs [aria-selected="true"] {
    background-color: #FEE500 !important;
    color: #2D2D2D !important;
}

/* 라디오 버튼 */
.stRadio [data-baseweb="radio"] {
    cursor: pointer;
}

/* 구분선 */
hr {
    border: none;
    border-top: 1.5px solid #F0F0F0;
    margin: 20px 0;
}
</style>
""", unsafe_allow_html=True)

# =========================
# 포맷
# =========================
def won(x):
    try:
        return f"₩{int(x):,}"
    except:
        return x

# =========================
# DB 초기화
# =========================
def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("""
    CREATE TABLE IF NOT EXISTS sales (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        created_at TEXT,
        user TEXT,
        type TEXT,
        sale_date TEXT,
        item TEXT,
        qty INTEGER,
        price INTEGER,
        total INTEGER,
        region TEXT
    )
    """)
    c.execute("""
    CREATE TABLE IF NOT EXISTS delete_log (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        deleted_at TEXT,
        reason TEXT,
        data TEXT
    )
    """)
    conn.commit()
    conn.close()

init_db()

# =========================
# DB 함수
# =========================
def insert_sale(data):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    # ✅ 버그 수정: datetime → str 변환, 튜플 순서 명확히
    c.execute(
        "INSERT INTO sales (created_at, user, type, sale_date, item, qty, price, total, region) VALUES (?,?,?,?,?,?,?,?,?)",
        data
    )
    conn.commit()
    conn.close()

def load_df():
    conn = sqlite3.connect(DB_FILE)
    df = pd.read_sql("SELECT * FROM sales", conn)
    conn.close()
    return df

def log_delete(reason, df):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("INSERT INTO delete_log VALUES (NULL,?,?,?)",
              (datetime.now().strftime("%Y-%m-%d %H:%M:%S"), reason, df.to_json()))
    conn.commit()
    conn.close()

def delete_by_ids(ids):
    df = load_df()
    target = df[df["id"].isin(ids)]
    log_delete("개별삭제", target)
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.executemany("DELETE FROM sales WHERE id=?", [(i,) for i in ids])
    conn.commit()
    conn.close()

def delete_by_date(date_val):
    df = load_df()
    target = df[df["sale_date"] == str(date_val)]
    log_delete("날짜삭제", target)
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("DELETE FROM sales WHERE sale_date=?", (str(date_val),))
    conn.commit()
    conn.close()

def delete_by_user(user):
    df = load_df()
    target = df[df["user"] == user]
    log_delete("담당자삭제", target)
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("DELETE FROM sales WHERE user=?", (user,))
    conn.commit()
    conn.close()

# =========================
# 사이드바 메뉴
# =========================
with st.sidebar:
    st.markdown("""
    <div style="text-align:center; padding: 20px 0 10px 0;">
        <div style="font-size:42px;">🟢</div>
        <div style="font-size:20px; font-weight:700; color:#2D2D2D; margin-top:6px;">맘스패치</div>
        <div style="font-size:12px; color:#AAAAAA; margin-top:2px;">ERP 관리 시스템</div>
    </div>
    <hr/>
    """, unsafe_allow_html=True)

    menu = st.radio(
        "메뉴 선택",
        ["📊 대시보드", "✏️ 매출 입력", "📈 정산 현황", "🗄️ 전체 DB", "🗑️ 삭제 관리", "📋 삭제 로그"],
        label_visibility="collapsed"
    )
    menu = menu.split(" ", 1)[1]  # 이모지 제거

    st.markdown("<hr/>", unsafe_allow_html=True)
    st.markdown(f"""
    <div style="font-size:11px; color:#CCCCCC; text-align:center; padding-bottom:10px;">
        마지막 업데이트<br/>{datetime.now().strftime("%Y.%m.%d %H:%M")}
    </div>
    """, unsafe_allow_html=True)

# =========================
# 대시보드
# =========================
if menu == "대시보드":
    st.markdown('<div class="section-header">📊 매출 대시보드</div>', unsafe_allow_html=True)

    df = load_df()

    if df.empty:
        st.info("아직 등록된 매출 데이터가 없어요. '매출 입력' 메뉴에서 데이터를 입력해주세요! 😊")
    else:
        df["sale_date"] = pd.to_datetime(df["sale_date"])
        today = pd.Timestamp.today().normalize()
        this_month = today.to_period("M")
        this_year = today.year

        today_total = df[df["sale_date"] == today]["total"].sum()
        month_total = df[df["sale_date"].dt.to_period("M") == this_month]["total"].sum()
        year_total = df[df["sale_date"].dt.year == this_year]["total"].sum()
        total_all = df["total"].sum()

        # KPI 카드
        c1, c2, c3, c4 = st.columns(4)
        with c1:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-icon">📅</div>
                <div class="metric-label">오늘 매출</div>
                <div class="metric-value">{won(today_total)}</div>
                <div class="metric-sub">{today.strftime('%m월 %d일')}</div>
            </div>""", unsafe_allow_html=True)
        with c2:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-icon">📆</div>
                <div class="metric-label">이번 달 매출</div>
                <div class="metric-value">{won(month_total)}</div>
                <div class="metric-sub">{this_month}월</div>
            </div>""", unsafe_allow_html=True)
        with c3:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-icon">🗓️</div>
                <div class="metric-label">올해 매출</div>
                <div class="metric-value">{won(year_total)}</div>
                <div class="metric-sub">{this_year}년</div>
            </div>""", unsafe_allow_html=True)
        with c4:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-icon">💰</div>
                <div class="metric-label">누적 총 매출</div>
                <div class="metric-value">{won(total_all)}</div>
                <div class="metric-sub">전체 기간</div>
            </div>""", unsafe_allow_html=True)

        st.markdown("<br/>", unsafe_allow_html=True)

        # 그래프 탭
        tab1, tab2, tab3 = st.tabs(["📅 일별 매출", "📆 월별 매출", "🗓️ 연도별 매출"])

        with tab1:
            daily = df.groupby(df["sale_date"].dt.date)["total"].sum().reset_index()
            daily.columns = ["날짜", "매출"]
            daily = daily.sort_values("날짜").tail(30)
            st.markdown("**최근 30일 일별 매출 추이**")
            st.bar_chart(daily.set_index("날짜")["매출"], color="#FEE500", height=320)

            # 일별 상세 테이블
            daily_display = daily.copy()
            daily_display["매출"] = daily_display["매출"].apply(won)
            st.dataframe(daily_display, use_container_width=True, hide_index=True)

        with tab2:
            df["month"] = df["sale_date"].dt.to_period("M")
            monthly = df.groupby("month")["total"].sum().reset_index()
            monthly["month"] = monthly["month"].astype(str)
            monthly.columns = ["월", "매출"]
            st.markdown("**월별 매출 추이**")
            st.bar_chart(monthly.set_index("월")["매출"], color="#FEE500", height=320)

            # 월별 상세 테이블
            monthly_display = monthly.copy()
            monthly_display["매출"] = monthly_display["매출"].apply(won)
            st.dataframe(monthly_display, use_container_width=True, hide_index=True)

        with tab3:
            yearly = df.groupby(df["sale_date"].dt.year)["total"].sum().reset_index()
            yearly.columns = ["연도", "매출"]
            st.markdown("**연도별 매출 추이**")
            st.bar_chart(yearly.set_index("연도")["매출"], color="#FEE500", height=320)

            yearly_display = yearly.copy()
            yearly_display["매출"] = yearly_display["매출"].apply(won)
            st.dataframe(yearly_display, use_container_width=True, hide_index=True)

        st.markdown("<br/>", unsafe_allow_html=True)

        # 구분별 매출 파이 (추가 인사이트)
        col_a, col_b = st.columns(2)
        with col_a:
            st.markdown("**판매 유형별 건수**")
            type_cnt = df["type"].value_counts().reset_index()
            type_cnt.columns = ["유형", "건수"]
            st.dataframe(type_cnt, use_container_width=True, hide_index=True)

        with col_b:
            st.markdown("**담당자별 매출**")
            user_sales = df.groupby("user")["total"].sum().reset_index()
            user_sales.columns = ["담당자", "매출"]
            user_sales["매출(원)"] = user_sales["매출"].apply(won)
            st.dataframe(user_sales[["담당자", "매출(원)"]], use_container_width=True, hide_index=True)

# =========================
# 매출 입력
# =========================
elif menu == "매출 입력":
    st.markdown('<div class="section-header">✏️ 매출 입력</div>', unsafe_allow_html=True)

    st.markdown('<div class="form-card">', unsafe_allow_html=True)

    with st.form("sale_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            name = st.text_input("👤 담당자", placeholder="이름을 입력하세요")
            t = st.selectbox("📦 판매 구분", ["전화주문", "온라인판매", "현장판매"])
            d = st.date_input("📅 판매 날짜")
        with col2:
            item = st.text_input("🛍️ 상품명", placeholder="상품명을 입력하세요")
            qty = st.number_input("🔢 수량", min_value=1, value=1)
            price = st.number_input("💵 단가 (원)", min_value=0, step=1000, value=0)

        region = ""
        if t == "현장판매":
            region = st.text_input("📍 지역", placeholder="판매 지역을 입력하세요")

        total_preview = qty * price
        st.markdown(f"""
        <div style="background:#FFF9C4; border-radius:10px; padding:14px 18px; margin:10px 0; border-left:4px solid #FEE500;">
            <span style="font-size:13px; color:#888;">예상 합계금액</span><br/>
            <span style="font-size:22px; font-weight:700; color:#2D2D2D;">₩{total_preview:,}</span>
        </div>
        """, unsafe_allow_html=True)

        submitted = st.form_submit_button("💾 저장하기", use_container_width=True)
        if submitted:
            if not name:
                st.warning("담당자 이름을 입력해주세요!")
            elif not item:
                st.warning("상품명을 입력해주세요!")
            elif price == 0:
                st.warning("단가를 입력해주세요!")
            else:
                total = qty * price
                # ✅ 버그 수정: datetime.now()를 문자열로 변환
                insert_sale((
                    datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    name, t,
                    str(d),
                    item, qty, price, total, region
                ))
                st.success(f"✅ 저장 완료! 합계: ₩{total:,}")
                st.balloons()

    st.markdown('</div>', unsafe_allow_html=True)

# =========================
# 정산 현황
# =========================
elif menu == "정산 현황":
    st.markdown('<div class="section-header">📈 정산 현황</div>', unsafe_allow_html=True)

    df = load_df()
    if df.empty:
        st.info("데이터가 없습니다.")
    else:
        df["sale_date"] = pd.to_datetime(df["sale_date"])
        df["month"] = df["sale_date"].dt.to_period("M")
        df["year"] = df["sale_date"].dt.year

        tab = st.radio("기간 선택", ["📅 일별", "📆 월별", "🗓️ 연도별"], horizontal=True)

        if "일별" in tab:
            g = df.groupby(df["sale_date"].dt.date)["total"].sum().reset_index()
            g.columns = ["날짜", "매출"]
            g["매출"] = g["매출"].apply(won)
            st.dataframe(g, use_container_width=True, hide_index=True)
        elif "월별" in tab:
            g = df.groupby("month")["total"].sum().reset_index()
            g["month"] = g["month"].astype(str)
            g.columns = ["월", "매출"]
            g["매출"] = g["매출"].apply(won)
            st.dataframe(g, use_container_width=True, hide_index=True)
        else:
            g = df.groupby("year")["total"].sum().reset_index()
            g.columns = ["연도", "매출"]
            g["매출"] = g["매출"].apply(won)
            st.dataframe(g, use_container_width=True, hide_index=True)

# =========================
# 전체 DB
# =========================
elif menu == "전체 DB":
    st.markdown('<div class="section-header">🗄️ 전체 데이터</div>', unsafe_allow_html=True)

    df = load_df()
    if df.empty:
        st.info("데이터가 없습니다.")
    else:
        # 검색 필터
        col1, col2 = st.columns([2, 1])
        with col1:
            search = st.text_input("🔍 검색 (담당자/상품명)", placeholder="검색어를 입력하세요")
        with col2:
            filter_type = st.selectbox("판매 구분 필터", ["전체", "전화주문", "온라인판매", "현장판매"])

        filtered_df = df.copy()
        if search:
            filtered_df = filtered_df[
                filtered_df["user"].str.contains(search, na=False) |
                filtered_df["item"].str.contains(search, na=False)
            ]
        if filter_type != "전체":
            filtered_df = filtered_df[filtered_df["type"] == filter_type]

        st.markdown(f"**총 {len(filtered_df)}건** | 합계: **{won(filtered_df['total'].sum())}**")

        display_df = filtered_df.copy()
        display_df["total"] = display_df["total"].apply(won)
        display_df["price"] = display_df["price"].apply(won)
        st.dataframe(display_df, use_container_width=True, hide_index=True)

        st.markdown("<hr/>", unsafe_allow_html=True)
        st.markdown("**🗑️ ID로 삭제**")
        ids = st.multiselect("삭제할 항목 ID 선택", filtered_df["id"].tolist())
        if st.button("선택 항목 삭제", disabled=len(ids)==0):
            delete_by_ids(ids)
            st.success(f"{len(ids)}건 삭제 완료!")
            st.rerun()

# =========================
# 삭제 관리
# =========================
elif menu == "삭제 관리":
    st.markdown('<div class="section-header">🗑️ 삭제 관리</div>', unsafe_allow_html=True)

    tab1, tab2 = st.tabs(["📅 날짜로 삭제", "👤 담당자로 삭제"])

    with tab1:
        st.markdown("선택한 날짜의 **모든 매출 데이터**를 삭제합니다.")
        d = st.date_input("삭제할 날짜 선택", key="del_date")

        df = load_df()
        target_count = len(df[df["sale_date"] == str(d)])
        if target_count > 0:
            st.warning(f"⚠️ {d} 날짜의 데이터 **{target_count}건**이 삭제됩니다.")
        else:
            st.info(f"{d} 날짜의 데이터가 없습니다.")

        if st.button("🗑️ 날짜 삭제 실행", key="del_date_btn"):
            delete_by_date(d)
            st.success("삭제 완료!")
            st.rerun()

    with tab2:
        st.markdown("선택한 담당자의 **모든 매출 데이터**를 삭제합니다.")
        df = load_df()
        users = df["user"].unique().tolist() if not df.empty else []
        user = st.selectbox("담당자 선택", ["선택하세요"] + users)

        if user != "선택하세요":
            target_count = len(df[df["user"] == user])
            st.warning(f"⚠️ '{user}' 담당자의 데이터 **{target_count}건**이 삭제됩니다.")

            if st.button("🗑️ 담당자 삭제 실행"):
                delete_by_user(user)
                st.success("삭제 완료!")
                st.rerun()

# =========================
# 삭제 로그
# =========================
elif menu == "삭제 로그":
    st.markdown('<div class="section-header">📋 삭제 로그</div>', unsafe_allow_html=True)

    conn = sqlite3.connect(DB_FILE)
    log_df = pd.read_sql("SELECT * FROM delete_log", conn)
    conn.close()

    if log_df.empty:
        st.info("삭제 이력이 없습니다.")
    else:
        st.markdown(f"**총 {len(log_df)}건**의 삭제 기록")
        st.dataframe(log_df[["id", "deleted_at", "reason"]], use_container_width=True, hide_index=True)
