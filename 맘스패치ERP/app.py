import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime
import os

st.set_page_config(page_title="맘스패치 ERP", page_icon="🟢", layout="wide")

DB_FILE = "momspatch.db"

# =========================
# 🎨 UI 스타일 (화이트 + 연두 ONLY)
# =========================
st.markdown("""
<style>
/* 전체 배경 */
body {
    background-color: #ffffff;
}

/* 메인 컨테이너 */
.main {
    background-color: #ffffff;
}

/* 사이드바 */
section[data-testid="stSidebar"] {
    background-color: #f5fff5;
}

/* 제목 */
h1, h2, h3 {
    color: #2ecc71;
}

/* 버튼 */
.stButton > button {
    background-color: #a8f0a5;
    color: black;
    border-radius: 10px;
    border: none;
}

.stButton > button:hover {
    background-color: #7ed957;
}

/* 입력창 */
input, textarea {
    border: 1px solid #a8f0a5 !important;
    border-radius: 8px;
}

/* 셀렉트박스 */
[data-baseweb="select"] {
    border: 1px solid #a8f0a5;
    border-radius: 8px;
}

/* 테이블 */
[data-testid="stDataFrame"] {
    background-color: #ffffff;
}

/* 헤더 고정 느낌 */
.block-container {
    padding-top: 1rem;
}
</style>
""", unsafe_allow_html=True)

st.title("🟢 맘스패치 ERP 시스템")

# =========================
# 포맷
# =========================
def won(x):
    try:
        return f"{int(x):,}원"
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
    c.execute("INSERT INTO sales VALUES (NULL,?,?,?,?,?,?,?,?,?)", data)
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
              (datetime.now(), reason, df.to_json()))
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
# 메뉴
# =========================
menu = st.sidebar.radio("메뉴",
    ["입력","정산","전체DB","삭제관리","로그"])

# =========================
# 입력
# =========================
if menu == "입력":
    with st.form("f"):
        name = st.text_input("담당자")
        t = st.selectbox("구분", ["전화주문","온라인판매","현장판매"])
        d = st.date_input("날짜")
        item = st.text_input("상품")
        qty = st.number_input("수량", 1)
        price = st.number_input("단가", 0, step=1000)
        region = st.text_input("지역") if t=="현장판매" else ""

        if st.form_submit_button("저장"):
            total = qty*price
            insert_sale((datetime.now(), name, t, d, item, qty, price, total, region))
            st.success(f"저장 완료: {won(total)}")

# =========================
# 정산
# =========================
elif menu == "정산":
    df = load_df()
    if not df.empty:
        df["sale_date"] = pd.to_datetime(df["sale_date"])
        df["month"] = df["sale_date"].dt.to_period("M")
        df["year"] = df["sale_date"].dt.year

        tab = st.radio("정산", ["일별","월별","연도별"])

        if tab == "일별":
            g = df.groupby(df["sale_date"].dt.date)["total"].sum()
        elif tab == "월별":
            g = df.groupby("month")["total"].sum()
        else:
            g = df.groupby("year")["total"].sum()

        st.dataframe(g.apply(won))

# =========================
# 전체 DB
# =========================
elif menu == "전체DB":
    df = load_df()
    if not df.empty:
        df["total"] = df["total"].apply(won)
        st.dataframe(df)

        ids = st.multiselect("삭제할 ID 선택", df["id"])
        if st.button("선택 삭제"):
            delete_by_ids(ids)
            st.success("삭제 완료")
            st.rerun()

# =========================
# 삭제관리
# =========================
elif menu == "삭제관리":
    st.subheader("조건 삭제")
    d = st.date_input("날짜 삭제")
    if st.button("날짜 삭제 실행"):
        delete_by_date(d)
        st.success("삭제 완료")

    user = st.text_input("담당자 삭제")
    if st.button("담당자 삭제 실행"):
        delete_by_user(user)
        st.success("삭제 완료")

# =========================
# 로그
# =========================
elif menu == "로그":
    conn = sqlite3.connect(DB_FILE)
    log_df = pd.read_sql("SELECT * FROM delete_log", conn)
    conn.close()
    st.dataframe(log_df)
