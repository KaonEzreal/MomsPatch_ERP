import io
import os
from datetime import datetime

import pandas as pd
import psycopg2
import psycopg2.extras
import streamlit as st

st.set_page_config(
    page_title="맘스패치 ERP",
    page_icon="🟢",
    layout="wide",
    initial_sidebar_state="expanded",
)

# =========================
# DB 연결 (Supabase PostgreSQL)
# =========================
def get_conn():
    db_url = st.secrets.get("DATABASE_URL", os.environ.get("DATABASE_URL", ""))
    if not db_url:
        st.error("DATABASE_URL이 설정되지 않았습니다. Streamlit Secrets를 확인해주세요.")
        st.stop()
    return psycopg2.connect(db_url, sslmode="require")


def init_db():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS sales (
            id SERIAL PRIMARY KEY,
            created_at TEXT,
            "user" TEXT,
            type TEXT,
            sale_date TEXT,
            item TEXT,
            qty INTEGER,
            price INTEGER,
            total INTEGER,
            region TEXT
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS delete_log (
            id SERIAL PRIMARY KEY,
            deleted_at TEXT,
            reason TEXT,
            data TEXT
        )
    """)
    conn.commit()
    cur.close()
    conn.close()


init_db()


# =========================
# DB 함수
# =========================
def insert_sale(data):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        """INSERT INTO sales (created_at, "user", type, sale_date, item, qty, price, total, region)
           VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
        data
    )
    conn.commit()
    cur.close()
    conn.close()


def load_df():
    conn = get_conn()
    df = pd.read_sql('SELECT * FROM sales ORDER BY id DESC', conn)
    conn.close()
    return df


def load_delete_log_df():
    conn = get_conn()
    df = pd.read_sql('SELECT * FROM delete_log ORDER BY id DESC', conn)
    conn.close()
    return df


def log_delete(reason, df):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO delete_log (deleted_at, reason, data) VALUES (%s,%s,%s)",
        (datetime.now().strftime("%Y-%m-%d %H:%M:%S"), reason,
         df.to_json(force_ascii=False, orient="records"))
    )
    conn.commit()
    cur.close()
    conn.close()


def delete_by_ids(ids):
    if not ids:
        return 0
    df = load_df()
    target = df[df["id"].isin(ids)]
    if not target.empty:
        log_delete("개별삭제", target)
    conn = get_conn()
    cur = conn.cursor()
    cur.executemany("DELETE FROM sales WHERE id=%s", [(int(i),) for i in ids])
    conn.commit()
    cur.close()
    conn.close()
    return len(ids)


def delete_by_date(date_val):
    date_str = str(date_val)
    df = load_df()
    target = df[df["sale_date"] == date_str]
    if not target.empty:
        log_delete("날짜삭제", target)
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("DELETE FROM sales WHERE sale_date=%s", (date_str,))
    conn.commit()
    cur.close()
    conn.close()
    return len(target)


def delete_by_user(user):
    df = load_df()
    target = df[df["user"] == user]
    if not target.empty:
        log_delete("담당자삭제", target)
    conn = get_conn()
    cur = conn.cursor()
    cur.execute('DELETE FROM sales WHERE "user"=%s', (user,))
    conn.commit()
    cur.close()
    conn.close()
    return len(target)


# =========================
# 엑셀 다운로드
# =========================
def to_excel(df: pd.DataFrame) -> bytes:
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="data")
        ws = writer.book["data"]
        for col in ws.columns:
            max_len = max((len(str(c.value)) if c.value else 0) for c in col)
            ws.column_dimensions[col[0].column_letter].width = min(max_len + 3, 30)
    return output.getvalue()


def won(x):
    try:
        return f"₩{int(x):,}"
    except Exception:
        return x


# =========================
# CSS
# =========================
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@300;400;500;700&display=swap');

html, body, [class*="css"], .stApp {
    font-family: 'Noto Sans KR', sans-serif !important;
    background-color: #F7F8FA !important;
    color: #2D2D2D !important;
}
:root { color-scheme: light !important; }

section[data-testid="stSidebar"] {
    background-color: #FFFFFF !important;
    border-right: 1px solid #EEEEEE !important;
}
section[data-testid="stSidebar"] * { color: #333333 !important; }

h1 { color: #2D2D2D !important; font-weight: 700 !important; }
h2, h3 { color: #2D2D2D !important; font-weight: 600 !important; }

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

input, textarea, .stTextInput > div > div > input,
.stNumberInput input, .stDateInput input {
    background-color: #FFFFFF !important;
    color: #2D2D2D !important;
    border-radius: 10px !important;
    border: 1.5px solid #E0E0E0 !important;
    font-size: 14px !important;
}
input:focus, textarea:focus {
    border-color: #FEE500 !important;
    box-shadow: 0 0 0 3px rgba(254,229,0,0.2) !important;
}

.stSelectbox > div > div, div[data-baseweb="select"] > div {
    background-color: #FFFFFF !important;
    color: #2D2D2D !important;
    border-radius: 10px !important;
    border: 1.5px solid #E0E0E0 !important;
}

.stTabs [data-baseweb="tab-list"] {
    background-color: #EFEFEF !important;
    border-radius: 12px; padding: 4px;
}
.stTabs [data-baseweb="tab"] {
    border-radius: 10px !important;
    font-weight: 600 !important;
    color: #555 !important;
}
.stTabs [aria-selected="true"] {
    background-color: #FEE500 !important;
    color: #2D2D2D !important;
}

.kpi-card {
    background: #FFFFFF;
    border-radius: 16px;
    padding: 20px 22px;
    box-shadow: 0 2px 12px rgba(0,0,0,0.06);
    border: 1px solid #F0F0F0;
    min-height: 130px;
    transition: transform 0.2s, box-shadow 0.2s;
}
.kpi-card:hover { transform: translateY(-2px); box-shadow: 0 6px 20px rgba(0,0,0,0.1); }
.kpi-icon { font-size: 26px; margin-bottom: 6px; }
.kpi-label { font-size: 12px; color: #999 !important; font-weight: 500; margin-bottom: 4px; }
.kpi-value { font-size: 24px; font-weight: 700; color: #2D2D2D !important; }
.kpi-sub { font-size: 11px; color: #BBB !important; margin-top: 4px; }

.section-header {
    background: linear-gradient(135deg, #FEE500 0%, #FFD700 100%);
    border-radius: 12px;
    padding: 14px 20px;
    margin-bottom: 20px;
    font-weight: 700;
    font-size: 16px;
    color: #2D2D2D !important;
    box-shadow: 0 2px 8px rgba(254,229,0,0.25);
}
.form-card {
    background: #FFFFFF;
    border-radius: 20px;
    padding: 28px;
    box-shadow: 0 4px 20px rgba(0,0,0,0.05);
    border: 1px solid #F0F0F0;
    margin-bottom: 16px;
}
.preview-box {
    background: #FFF9C4;
    border-radius: 10px;
    padding: 14px 18px;
    margin: 10px 0;
    border-left: 4px solid #FEE500;
}
hr { border: none; border-top: 1.5px solid #F0F0F0; margin: 20px 0; }
[data-testid="stDataFrame"] {
    background: #FFFFFF !important;
    border-radius: 12px !important;
    border: 1px solid #F0F0F0 !important;
}
</style>
""", unsafe_allow_html=True)


# =========================
# 사이드바
# =========================
with st.sidebar:
    st.markdown("""
    <div style="text-align:center;padding:20px 0 10px;">
        <div style="font-size:40px;">🟢</div>
        <div style="font-size:19px;font-weight:700;color:#2D2D2D;margin-top:6px;">맘스패치</div>
        <div style="font-size:12px;color:#AAAAAA;margin-top:2px;">ERP 관리 시스템</div>
    </div><hr/>
    """, unsafe_allow_html=True)

    menu = st.radio(
        "메뉴",
        ["📊 대시보드", "✏️ 매출 입력", "📈 정산 현황", "🗄️ 전체 DB", "🗑️ 삭제 관리", "📋 삭제 로그"],
        label_visibility="collapsed"
    )
    menu = menu.split(" ", 1)[1]

    st.markdown("<hr/>", unsafe_allow_html=True)
    st.markdown(f"""
    <div style="font-size:11px;color:#CCCCCC;text-align:center;padding-bottom:10px;">
        ☁️ Supabase PostgreSQL<br/>데이터 안전 저장 중<br/><br/>
        {datetime.now().strftime("%Y.%m.%d %H:%M")}
    </div>
    """, unsafe_allow_html=True)


# =========================
# 대시보드
# =========================
if menu == "대시보드":
    st.markdown('<div class="section-header">📊 매출 대시보드</div>', unsafe_allow_html=True)
    df = load_df()

    if df.empty:
        st.info("아직 매출 데이터가 없어요. '매출 입력' 메뉴에서 데이터를 입력해주세요! 😊")
    else:
        df["sale_date"] = pd.to_datetime(df["sale_date"], errors="coerce")
        df = df.dropna(subset=["sale_date"]).copy()

        today = pd.Timestamp.today().normalize()
        this_month = today.to_period("M")
        this_year = today.year

        today_total = df[df["sale_date"].dt.normalize() == today]["total"].sum()
        month_total = df[df["sale_date"].dt.to_period("M") == this_month]["total"].sum()
        year_total  = df[df["sale_date"].dt.year == this_year]["total"].sum()
        total_all   = df["total"].sum()
        total_count = len(df)

        c1, c2, c3, c4 = st.columns(4)
        for col, icon, label, value, sub in [
            (c1, "📅", "오늘 매출",    won(today_total), today.strftime("%m월 %d일")),
            (c2, "📆", "이번 달 매출", won(month_total), str(this_month)),
            (c3, "🗓️", "올해 매출",   won(year_total),  f"{this_year}년"),
            (c4, "💰", "누적 총 매출", won(total_all),   f"총 {total_count}건"),
        ]:
            with col:
                st.markdown(f"""
                <div class="kpi-card">
                    <div class="kpi-icon">{icon}</div>
                    <div class="kpi-label">{label}</div>
                    <div class="kpi-value">{value}</div>
                    <div class="kpi-sub">{sub}</div>
                </div>""", unsafe_allow_html=True)

        st.markdown("<br/>", unsafe_allow_html=True)

        tab1, tab2, tab3 = st.tabs(["📅 일별 매출", "📆 월별 매출", "🗓️ 연도별 매출"])

        with tab1:
            daily = (df.groupby(df["sale_date"].dt.date)["total"]
                     .sum().reset_index()
                     .rename(columns={"sale_date":"날짜","total":"매출"})
                     .sort_values("날짜").tail(60))
            st.markdown(f"**최근 {len(daily)}일 일별 매출 추이**")
            st.bar_chart(daily.set_index("날짜")["매출"], color="#FEE500", height=300)
            col_t, col_dl = st.columns([3,1])
            dl = daily.copy(); dl["매출"] = dl["매출"].apply(won)
            with col_t:
                st.dataframe(dl, use_container_width=True, hide_index=True)
            with col_dl:
                st.download_button("📥 일별 엑셀", to_excel(daily),
                    f"일별매출_{datetime.now().strftime('%Y%m%d')}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

        with tab2:
            df["month"] = df["sale_date"].dt.to_period("M")
            monthly = df.groupby("month")["total"].sum().reset_index()
            monthly["month"] = monthly["month"].astype(str)
            monthly.columns = ["월","매출"]
            st.markdown("**월별 매출 추이**")
            st.bar_chart(monthly.set_index("월")["매출"], color="#FEE500", height=300)
            col_t, col_dl = st.columns([3,1])
            ml = monthly.copy(); ml["매출"] = ml["매출"].apply(won)
            with col_t:
                st.dataframe(ml, use_container_width=True, hide_index=True)
            with col_dl:
                st.download_button("📥 월별 엑셀", to_excel(monthly),
                    f"월별매출_{datetime.now().strftime('%Y%m%d')}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

        with tab3:
            yearly = (df.groupby(df["sale_date"].dt.year)["total"]
                      .sum().reset_index()
                      .rename(columns={"sale_date":"연도","total":"매출"}))
            st.markdown("**연도별 매출 추이**")
            st.bar_chart(yearly.set_index("연도")["매출"], color="#FEE500", height=300)
            col_t, col_dl = st.columns([3,1])
            yl = yearly.copy(); yl["매출"] = yl["매출"].apply(won)
            with col_t:
                st.dataframe(yl, use_container_width=True, hide_index=True)
            with col_dl:
                st.download_button("📥 연도별 엑셀", to_excel(yearly),
                    f"연도별매출_{datetime.now().strftime('%Y%m%d')}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

        st.markdown("<br/>", unsafe_allow_html=True)
        col_a, col_b = st.columns(2)
        with col_a:
            st.markdown("**판매 유형별 건수**")
            tc = df["type"].value_counts().reset_index()
            tc.columns = ["유형","건수"]
            st.dataframe(tc, use_container_width=True, hide_index=True)
        with col_b:
            st.markdown("**담당자별 매출**")
            us = df.groupby("user")["total"].sum().reset_index()
            us.columns = ["담당자","매출"]
            us["매출"] = us["매출"].apply(won)
            st.dataframe(us, use_container_width=True, hide_index=True)


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
            t    = st.selectbox("📦 판매 구분", ["전화주문","온라인판매","현장판매"])
            d    = st.date_input("📅 판매 날짜")
        with col2:
            item  = st.text_input("🛍️ 상품명", placeholder="상품명을 입력하세요")
            qty   = st.number_input("🔢 수량", min_value=1, value=1, step=1)
            price = st.number_input("💵 단가 (원)", min_value=0, step=1000, value=0)

        region = ""
        if t == "현장판매":
            region = st.text_input("📍 지역", placeholder="판매 지역을 입력하세요")

        preview = int(qty) * int(price)
        st.markdown(f"""
        <div class="preview-box">
            <span style="font-size:13px;color:#888;">예상 합계금액</span><br/>
            <span style="font-size:22px;font-weight:700;color:#2D2D2D;">₩{preview:,}</span>
        </div>""", unsafe_allow_html=True)

        if st.form_submit_button("💾 저장하기", use_container_width=True):
            name   = str(name).strip()
            item   = str(item).strip()
            region = str(region).strip()
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
                        name, t, str(d), item,
                        int(qty), int(price), total, region
                    ))
                    st.success(f"✅ 저장 완료! 합계: ₩{total:,}")
                    st.balloons()
                except Exception as e:
                    st.error(f"저장 중 오류: {e}")

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

        tab = st.radio("기간 선택", ["📅 일별","📆 월별","🗓️ 연도별"], horizontal=True)

        if "일별" in tab:
            g = (df.groupby(df["sale_date"].dt.date)["total"]
                 .sum().reset_index()
                 .rename(columns={"sale_date":"날짜","total":"매출"}))
            raw = g.copy()
            g["매출"] = g["매출"].apply(won)
            st.dataframe(g, use_container_width=True, hide_index=True)
            st.download_button("📥 일별 엑셀", to_excel(raw),
                f"일별정산_{datetime.now().strftime('%Y%m%d')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

        elif "월별" in tab:
            df["month"] = df["sale_date"].dt.to_period("M")
            g = df.groupby("month")["total"].sum().reset_index()
            g["month"] = g["month"].astype(str)
            g.columns = ["월","매출"]
            raw = g.copy()
            g["매출"] = g["매출"].apply(won)
            st.dataframe(g, use_container_width=True, hide_index=True)
            st.download_button("📥 월별 엑셀", to_excel(raw),
                f"월별정산_{datetime.now().strftime('%Y%m%d')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

        else:
            g = (df.groupby(df["sale_date"].dt.year)["total"]
                 .sum().reset_index()
                 .rename(columns={"sale_date":"연도","total":"매출"}))
            raw = g.copy()
            g["매출"] = g["매출"].apply(won)
            st.dataframe(g, use_container_width=True, hide_index=True)
            st.download_button("📥 연도별 엑셀", to_excel(raw),
                f"연도별정산_{datetime.now().strftime('%Y%m%d')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")


# =========================
# 전체 DB
# =========================
elif menu == "전체 DB":
    st.markdown('<div class="section-header">🗄️ 전체 데이터</div>', unsafe_allow_html=True)
    df = load_df()

    if df.empty:
        st.info("데이터가 없습니다.")
    else:
        col1, col2 = st.columns([2,1])
        with col1:
            search = st.text_input("🔍 검색 (담당자/상품명/지역)", placeholder="검색어를 입력하세요")
        with col2:
            filter_type = st.selectbox("판매 구분 필터", ["전체","전화주문","온라인판매","현장판매"])

        fdf = df.copy()
        if search:
            s = str(search).strip()
            fdf = fdf[
                fdf["user"].astype(str).str.contains(s, na=False) |
                fdf["item"].astype(str).str.contains(s, na=False) |
                fdf["region"].astype(str).str.contains(s, na=False)
            ]
        if filter_type != "전체":
            fdf = fdf[fdf["type"] == filter_type]

        st.markdown(f"**총 {len(fdf)}건** | 합계: **{won(fdf['total'].sum())}**")
        st.download_button("📥 전체 엑셀 다운로드", to_excel(fdf),
            f"전체DB_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

        disp = fdf.copy()
        disp["price"] = disp["price"].apply(won)
        disp["total"] = disp["total"].apply(won)
        st.dataframe(disp, use_container_width=True, hide_index=True)

        st.markdown("<hr/>")
        st.markdown("**🗑️ ID로 삭제**")
        ids = st.multiselect("삭제할 항목 ID 선택", fdf["id"].tolist())
        if st.button("선택 항목 삭제", disabled=(len(ids)==0)):
            try:
                n = delete_by_ids(ids)
                st.success(f"{n}건 삭제 완료!")
                st.rerun()
            except Exception as e:
                st.error(f"삭제 오류: {e}")


# =========================
# 삭제 관리
# =========================
elif menu == "삭제 관리":
    st.markdown('<div class="section-header">🗑️ 삭제 관리</div>', unsafe_allow_html=True)

    tab1, tab2 = st.tabs(["📅 날짜로 삭제","👤 담당자로 삭제"])

    with tab1:
        st.markdown("선택한 날짜의 **모든 매출 데이터**를 삭제합니다.")
        d = st.date_input("삭제할 날짜 선택", key="del_date")
        df = load_df()
        cnt = len(df[df["sale_date"] == str(d)])
        if cnt > 0:
            st.warning(f"⚠️ {d} 날짜의 데이터 **{cnt}건**이 삭제됩니다.")
        else:
            st.info(f"{d} 날짜의 데이터가 없습니다.")
        if st.button("🗑️ 날짜 삭제 실행"):
            try:
                n = delete_by_date(d)
                st.success(f"삭제 완료! ({n}건)")
                st.rerun()
            except Exception as e:
                st.error(f"삭제 오류: {e}")

    with tab2:
        st.markdown("선택한 담당자의 **모든 매출 데이터**를 삭제합니다.")
        df = load_df()
        users = sorted(df["user"].dropna().astype(str).unique().tolist()) if not df.empty else []
        user = st.selectbox("담당자 선택", ["선택하세요"] + users)
        if user != "선택하세요":
            cnt = len(df[df["user"] == user])
            st.warning(f"⚠️ '{user}' 담당자의 데이터 **{cnt}건**이 삭제됩니다.")
            if st.button("🗑️ 담당자 삭제 실행"):
                try:
                    n = delete_by_user(user)
                    st.success(f"삭제 완료! ({n}건)")
                    st.rerun()
                except Exception as e:
                    st.error(f"삭제 오류: {e}")


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
        st.dataframe(log_df[["id","deleted_at","reason"]], use_container_width=True, hide_index=True)
        st.download_button("📥 삭제 로그 엑셀", to_excel(log_df),
            f"삭제로그_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
