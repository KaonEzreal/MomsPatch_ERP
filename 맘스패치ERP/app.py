import os
import io
import time
import sqlite3
from datetime import datetime

import pandas as pd
import streamlit as st

st.set_page_config(
    page_title="맘스패치 ERP",
    page_icon="🟢",
    layout="wide",
    initial_sidebar_state="expanded",
)

# =========================
# DB 경로 설정
# =========================
# 1) 기본: 현재 실행 폴더 아래 data/momspatch.db
# 2) 환경변수 MOMSPATCH_DB_PATH 지정 시 그 경로 우선 사용
#    예: MOMSPATCH_DB_PATH=/mount/data/momspatch.db
DEFAULT_DB_DIR = os.path.join(os.getcwd(), "data")
os.makedirs(DEFAULT_DB_DIR, exist_ok=True)

DB_FILE = os.environ.get("MOMSPATCH_DB_PATH", os.path.join(DEFAULT_DB_DIR, "momspatch.db"))


# =========================
# LIGHT 모드 강제 스타일
# =========================
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@300;400;500;700&display=swap');

html, body, [class*="css"], .stApp {
    font-family: 'Noto Sans KR', sans-serif;
    background-color: #F9F9F9 !important;
    color: #2D2D2D !important;
}

/* 다크 테마 강제 덮어쓰기 */
:root {
    color-scheme: light !important;
}

section[data-testid="stSidebar"] {
    background-color: #FFFFFF !important;
    border-right: 1px solid #EEEEEE !important;
}

section[data-testid="stSidebar"] .stRadio > label,
section[data-testid="stSidebar"] * {
    color: #333333 !important;
}

/* 메인 텍스트 */
h1, h2, h3, h4, h5, h6, p, span, div, label {
    color: #2D2D2D;
}

h1 { color: #2D2D2D !important; font-weight: 700 !important; letter-spacing: -0.5px; }
h2 { color: #2D2D2D !important; font-weight: 600 !important; }
h3 { color: #3C3C3C !important; font-weight: 600 !important; }

/* 버튼 */
.stButton > button,
.stDownloadButton > button,
div[data-testid="stFormSubmitButton"] > button {
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
.stButton > button:hover,
.stDownloadButton > button:hover,
div[data-testid="stFormSubmitButton"] > button:hover {
    background-color: #F5DC00 !important;
    transform: translateY(-1px) !important;
    box-shadow: 0 4px 12px rgba(0,0,0,0.15) !important;
}

/* 입력 필드 */
.stTextInput > div > div > input,
.stNumberInput input,
.stDateInput input,
textarea,
input {
    background-color: #FFFFFF !important;
    color: #2D2D2D !important;
    border-radius: 10px !important;
    border: 1.5px solid #E0E0E0 !important;
    padding: 10px 14px !important;
    font-size: 14px !important;
    transition: border-color 0.2s !important;
}
.stTextInput > div > div > input:focus,
.stNumberInput input:focus,
textarea:focus,
input:focus {
    border-color: #FEE500 !important;
    box-shadow: 0 0 0 3px rgba(254,229,0,0.2) !important;
}

/* selectbox */
.stSelectbox > div > div,
div[data-baseweb="select"] > div {
    background-color: #FFFFFF !important;
    color: #2D2D2D !important;
    border-radius: 10px !important;
    border: 1.5px solid #E0E0E0 !important;
}

/* 카드 */
.metric-card {
    background: #FFFFFF;
    border-radius: 16px;
    padding: 20px 24px;
    box-shadow: 0 2px 12px rgba(0,0,0,0.06);
    border: 1px solid #F0F0F0;
    transition: transform 0.2s ease, box-shadow 0.2s ease;
    min-height: 145px;
}
.metric-card:hover {
    transform: translateY(-2px);
    box-shadow: 0 6px 20px rgba(0,0,0,0.1);
}
.metric-label {
    font-size: 13px;
    color: #888888 !important;
    font-weight: 500;
    margin-bottom: 6px;
}
.metric-value {
    font-size: 26px;
    font-weight: 700;
    color: #2D2D2D !important;
}
.metric-sub {
    font-size: 12px;
    color: #AAAAAA !important;
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
    color: #2D2D2D !important;
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

/* 탭 */
.stTabs [data-baseweb="tab-list"] {
    background-color: #F5F5F5 !important;
    border-radius: 12px;
    padding: 4px;
}
.stTabs [data-baseweb="tab"] {
    border-radius: 10px !important;
    font-weight: 600 !important;
    color: #444 !important;
}
.stTabs [aria-selected="true"] {
    background-color: #FEE500 !important;
    color: #2D2D2D !important;
}

/* dataframe */
[data-testid="stDataFrame"] {
    background-color: #FFFFFF !important;
    border-radius: 12px !important;
    overflow: hidden !important;
    border: 1px solid #F0F0F0 !important;
}

/* 기타 */
hr {
    border: none;
    border-top: 1.5px solid #F0F0F0;
    margin: 20px 0;
}

small, .caption, [data-testid="stCaptionContainer"] {
    color: #888 !important;
}
</style>
""", unsafe_allow_html=True)


# =========================
# 공용 함수
# =========================
def won(x):
    try:
        return f"₩{int(x):,}"
    except Exception:
        return x


def safe_text(x):
    if x is None:
        return ""
    return str(x)


def get_conn():
    """
    여러 사용자 동시 접근 시 SQLite 잠금 문제를 줄이기 위한 설정:
    - check_same_thread=False
    - WAL 모드
    - busy_timeout
    """
    conn = sqlite3.connect(DB_FILE, timeout=30, check_same_thread=False)
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA synchronous=NORMAL;")
    conn.execute("PRAGMA busy_timeout=30000;")
    return conn


def run_write(query, params=None, many=False, retries=5, retry_sleep=0.3):
    """
    DB locked 상황을 대비한 재시도 래퍼
    """
    params = params or ()
    last_error = None

    for _ in range(retries):
        conn = None
        try:
            conn = get_conn()
            cur = conn.cursor()
            if many:
                cur.executemany(query, params)
            else:
                cur.execute(query, params)
            conn.commit()
            return True
        except sqlite3.OperationalError as e:
            last_error = e
            if "locked" in str(e).lower():
                time.sleep(retry_sleep)
                continue
            raise
        finally:
            if conn:
                conn.close()

    if last_error:
        raise last_error
    return False


# =========================
# DB 초기화
# =========================
def init_db():
    conn = get_conn()
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
    run_write(
        "INSERT INTO sales (created_at, user, type, sale_date, item, qty, price, total, region) VALUES (?,?,?,?,?,?,?,?,?)",
        data
    )


def load_df():
    conn = get_conn()
    try:
        df = pd.read_sql("SELECT * FROM sales ORDER BY id DESC", conn)
        return df
    finally:
        conn.close()


def load_delete_log_df():
    conn = get_conn()
    try:
        df = pd.read_sql("SELECT * FROM delete_log ORDER BY id DESC", conn)
        return df
    finally:
        conn.close()


def log_delete(reason, df):
    run_write(
        "INSERT INTO delete_log (deleted_at, reason, data) VALUES (?,?,?)",
        (
            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            reason,
            df.to_json(force_ascii=False, orient="records")
        )
    )


def delete_by_ids(ids):
    if not ids:
        return 0

    df = load_df()
    target = df[df["id"].isin(ids)]
    if not target.empty:
        log_delete("개별삭제", target)

    run_write(
        "DELETE FROM sales WHERE id=?",
        [(int(i),) for i in ids],
        many=True
    )
    return len(ids)


def delete_by_date(date_val):
    date_str = str(date_val)
    df = load_df()
    target = df[df["sale_date"] == date_str]
    if not target.empty:
        log_delete("날짜삭제", target)

    run_write("DELETE FROM sales WHERE sale_date=?", (date_str,))
    return len(target)


def delete_by_user(user):
    df = load_df()
    target = df[df["user"] == user]
    if not target.empty:
        log_delete("담당자삭제", target)

    run_write("DELETE FROM sales WHERE user=?", (user,))
    return len(target)


# =========================
# 엑셀 다운로드 함수
# =========================
def dataframe_to_excel_bytes(df: pd.DataFrame) -> bytes:
    output = io.BytesIO()

    export_df = df.copy()

    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        export_df.to_excel(writer, index=False, sheet_name="sales")

        ws = writer.book["sales"]
        for col in ws.columns:
            max_length = 0
            col_letter = col[0].column_letter
            for cell in col:
                try:
                    value_len = len(str(cell.value)) if cell.value is not None else 0
                    if value_len > max_length:
                        max_length = value_len
                except Exception:
                    pass
            ws.column_dimensions[col_letter].width = min(max_length + 2, 30)

    output.seek(0)
    return output.read()


# =========================
# 사이드바
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
    menu = menu.split(" ", 1)[1]

    st.markdown("<hr/>", unsafe_allow_html=True)
    st.markdown(f"""
    <div style="font-size:11px; color:#CCCCCC; text-align:center; padding-bottom:10px;">
        DB 경로<br/>{DB_FILE}<br/><br/>
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
        df["sale_date"] = pd.to_datetime(df["sale_date"], errors="coerce")
        df = df.dropna(subset=["sale_date"]).copy()

        today = pd.Timestamp.today().normalize()
        this_month = today.to_period("M")
        this_year = today.year

        today_total = df[df["sale_date"].dt.normalize() == today]["total"].sum()
        month_total = df[df["sale_date"].dt.to_period("M") == this_month]["total"].sum()
        year_total = df[df["sale_date"].dt.year == this_year]["total"].sum()
        total_all = df["total"].sum()

        c1, c2, c3, c4 = st.columns(4)
        with c1:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-icon">📅</div>
                <div class="metric-label">오늘 매출</div>
                <div class="metric-value">{won(today_total)}</div>
                <div class="metric-sub">{today.strftime('%m월 %d일')}</div>
            </div>
            """, unsafe_allow_html=True)
        with c2:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-icon">📆</div>
                <div class="metric-label">이번 달 매출</div>
                <div class="metric-value">{won(month_total)}</div>
                <div class="metric-sub">{str(this_month)}월</div>
            </div>
            """, unsafe_allow_html=True)
        with c3:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-icon">🗓️</div>
                <div class="metric-label">올해 매출</div>
                <div class="metric-value">{won(year_total)}</div>
                <div class="metric-sub">{this_year}년</div>
            </div>
            """, unsafe_allow_html=True)
        with c4:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-icon">💰</div>
                <div class="metric-label">누적 총 매출</div>
                <div class="metric-value">{won(total_all)}</div>
                <div class="metric-sub">전체 기간</div>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("<br/>", unsafe_allow_html=True)

        tab1, tab2, tab3 = st.tabs(["📅 일별 매출", "📆 월별 매출", "🗓️ 연도별 매출"])

        with tab1:
            daily = df.groupby(df["sale_date"].dt.date)["total"].sum().reset_index()
            daily.columns = ["날짜", "매출"]
            daily = daily.sort_values("날짜").tail(30)
            st.markdown("**최근 30일 일별 매출 추이**")
            st.bar_chart(daily.set_index("날짜")["매출"], height=320)

            daily_display = daily.copy()
            daily_display["매출"] = daily_display["매출"].apply(won)
            st.dataframe(daily_display, use_container_width=True, hide_index=True)

        with tab2:
            df["month"] = df["sale_date"].dt.to_period("M")
            monthly = df.groupby("month")["total"].sum().reset_index()
            monthly["month"] = monthly["month"].astype(str)
            monthly.columns = ["월", "매출"]
            st.markdown("**월별 매출 추이**")
            st.bar_chart(monthly.set_index("월")["매출"], height=320)

            monthly_display = monthly.copy()
            monthly_display["매출"] = monthly_display["매출"].apply(won)
            st.dataframe(monthly_display, use_container_width=True, hide_index=True)

        with tab3:
            yearly = df.groupby(df["sale_date"].dt.year)["total"].sum().reset_index()
            yearly.columns = ["연도", "매출"]
            st.markdown("**연도별 매출 추이**")
            st.bar_chart(yearly.set_index("연도")["매출"], height=320)

            yearly_display = yearly.copy()
            yearly_display["매출"] = yearly_display["매출"].apply(won)
            st.dataframe(yearly_display, use_container_width=True, hide_index=True)

        st.markdown("<br/>", unsafe_allow_html=True)

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
            qty = st.number_input("🔢 수량", min_value=1, value=1, step=1)
            price = st.number_input("💵 단가 (원)", min_value=0, step=1000, value=0)

        region = ""
        if t == "현장판매":
            region = st.text_input("📍 지역", placeholder="판매 지역을 입력하세요")

        total_preview = int(qty) * int(price)
        st.markdown(f"""
        <div style="background:#FFF9C4; border-radius:10px; padding:14px 18px; margin:10px 0; border-left:4px solid #FEE500;">
            <span style="font-size:13px; color:#888;">예상 합계금액</span><br/>
            <span style="font-size:22px; font-weight:700; color:#2D2D2D;">₩{total_preview:,}</span>
        </div>
        """, unsafe_allow_html=True)

        submitted = st.form_submit_button("💾 저장하기", use_container_width=True)

        if submitted:
            name = safe_text(name).strip()
            item = safe_text(item).strip()
            region = safe_text(region).strip()

            if not name:
                st.warning("담당자 이름을 입력해주세요!")
            elif not item:
                st.warning("상품명을 입력해주세요!")
            elif int(price) == 0:
                st.warning("단가를 입력해주세요!")
            else:
                total = int(qty) * int(price)
                try:
                    insert_sale((
                        datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        name,
                        t,
                        str(d),
                        item,
                        int(qty),
                        int(price),
                        int(total),
                        region
                    ))
                    st.success(f"✅ 저장 완료! 합계: ₩{total:,}")
                    st.balloons()
                except Exception as e:
                    st.error(f"저장 중 오류가 발생했습니다: {e}")

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
        df["sale_date"] = pd.to_datetime(df["sale_date"], errors="coerce")
        df = df.dropna(subset=["sale_date"]).copy()
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
        col1, col2 = st.columns([2, 1])

        with col1:
            search = st.text_input("🔍 검색 (담당자/상품명/지역)", placeholder="검색어를 입력하세요")

        with col2:
            filter_type = st.selectbox("판매 구분 필터", ["전체", "전화주문", "온라인판매", "현장판매"])

        filtered_df = df.copy()

        if search:
            search = safe_text(search).strip()
            filtered_df = filtered_df[
                filtered_df["user"].astype(str).str.contains(search, na=False) |
                filtered_df["item"].astype(str).str.contains(search, na=False) |
                filtered_df["region"].astype(str).str.contains(search, na=False)
            ]

        if filter_type != "전체":
            filtered_df = filtered_df[filtered_df["type"] == filter_type]

        st.markdown(f"**총 {len(filtered_df)}건** | 합계: **{won(filtered_df['total'].sum())}**")

        # 다운로드 버튼
        excel_bytes = dataframe_to_excel_bytes(filtered_df)
        st.download_button(
            label="📥 엑셀 다운로드",
            data=excel_bytes,
            file_name=f"momspatch_db_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=False
        )

        display_df = filtered_df.copy()
        display_df["price"] = display_df["price"].apply(won)
        display_df["total"] = display_df["total"].apply(won)

        st.dataframe(display_df, use_container_width=True, hide_index=True)

        st.markdown("<hr/>", unsafe_allow_html=True)
        st.markdown("**🗑️ ID로 삭제**")

        ids = st.multiselect("삭제할 항목 ID 선택", filtered_df["id"].tolist())

        if st.button("선택 항목 삭제", disabled=(len(ids) == 0)):
            try:
                deleted_count = delete_by_ids(ids)
                st.success(f"{deleted_count}건 삭제 완료!")
                st.rerun()
            except Exception as e:
                st.error(f"삭제 중 오류가 발생했습니다: {e}")


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
            try:
                deleted_count = delete_by_date(d)
                st.success(f"삭제 완료! ({deleted_count}건)")
                st.rerun()
            except Exception as e:
                st.error(f"삭제 중 오류가 발생했습니다: {e}")

    with tab2:
        st.markdown("선택한 담당자의 **모든 매출 데이터**를 삭제합니다.")
        df = load_df()
        users = sorted(df["user"].dropna().astype(str).unique().tolist()) if not df.empty else []
        user = st.selectbox("담당자 선택", ["선택하세요"] + users)

        if user != "선택하세요":
            target_count = len(df[df["user"] == user])
            st.warning(f"⚠️ '{user}' 담당자의 데이터 **{target_count}건**이 삭제됩니다.")

            if st.button("🗑️ 담당자 삭제 실행"):
                try:
                    deleted_count = delete_by_user(user)
                    st.success(f"삭제 완료! ({deleted_count}건)")
                    st.rerun()
                except Exception as e:
                    st.error(f"삭제 중 오류가 발생했습니다: {e}")


# =========================
# 삭제 로그
# =========================
elif menu == "삭제 로그":
    st.markdown('<div class="section-header">📋 삭제 로그</div>', unsafe_allow_html=True)

    log_df = load_delete_log_df()

    if log_df.empty:
        st.info("삭제 이력이 없습니다.")
    else:
        st.markdown(f"**총 {len(log_df)}건**의 삭제 기록")
        st.dataframe(log_df[["id", "deleted_at", "reason"]], use_container_width=True, hide_index=True)

        log_excel = dataframe_to_excel_bytes(log_df)
        st.download_button(
            label="📥 삭제 로그 엑셀 다운로드",
            data=log_excel,
            file_name=f"momspatch_delete_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
