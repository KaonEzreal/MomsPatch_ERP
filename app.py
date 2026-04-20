import streamlit as st
import pandas as pd
import sqlite3
from datetime import date, datetime
from io import BytesIO

st.set_page_config(page_title="맘스패치 정산 시스템", page_icon="📊", layout="wide")

DB_FILE = "momspatch.db"

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
        user_id TEXT,
        user_name TEXT,
        type TEXT,
        sale_date TEXT,
        item TEXT,
        qty INTEGER,
        price INTEGER,
        total INTEGER,
        region TEXT,
        memo TEXT
    )
    """)
    conn.commit()
    conn.close()

init_db()

# =========================
# 사용자
# =========================
USERS = {
    "admin": {"name": "관리자", "password": "1234"},
    "staff1": {"name": "직원1", "password": "1111"},
}

SALES_TYPES = ["전화주문", "온라인판매", "현장판매"]
REGIONS = ["서울","경기","부산","대구","기타"]

# =========================
# 로그인
# =========================
if "login" not in st.session_state:
    st.session_state.login = False

if not st.session_state.login:
    st.title("맘스패치 로그인")
    user = st.text_input("아이디")
    pw = st.text_input("비밀번호", type="password")
    if st.button("로그인"):
        if user in USERS and USERS[user]["password"] == pw:
            st.session_state.login = True
            st.session_state.user = user
            st.session_state.name = USERS[user]["name"]
            st.rerun()
        else:
            st.error("로그인 실패")
    st.stop()

# =========================
# DB 함수
# =========================
def insert_sale(data):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("""
    INSERT INTO sales VALUES (NULL,?,?,?,?,?,?,?,?,?,?,?)
    """, data)
    conn.commit()
    conn.close()


def load_data():
    conn = sqlite3.connect(DB_FILE)
    df = pd.read_sql("SELECT * FROM sales", conn)
    conn.close()
    return df

# =========================
# UI
# =========================
st.sidebar.write(f"접속자: {st.session_state.name}")
menu = st.sidebar.radio("메뉴", ["입력","정산","지역분석","엑셀"])

if menu == "입력":
    st.title("판매 입력")
    with st.form("f"):
        t = st.selectbox("구분", SALES_TYPES)
        d = st.date_input("날짜")
        item = st.text_input("상품")
        qty = st.number_input("수량", 1)
        price = st.number_input("단가", 0)
        region = st.selectbox("지역", REGIONS) if t=="현장판매" else ""
        memo = st.text_input("메모")
        if st.form_submit_button("저장"):
            total = qty*price
            insert_sale((datetime.now(), st.session_state.user, st.session_state.name, t, d, item, qty, price, total, region, memo))
            st.success("저장 완료 (DB 저장됨 - 절대 안날아감)")

elif menu == "정산":
    df = load_data()
    if df.empty:
        st.warning("데이터 없음")
    else:
        df["sale_date"] = pd.to_datetime(df["sale_date"])
        period = st.radio("정산", ["일별","월별","연도별"])

        if period == "일별":
            df["p"] = df["sale_date"].dt.date
        elif period == "월별":
            df["p"] = df["sale_date"].dt.to_period("M")
        else:
            df["p"] = df["sale_date"].dt.year

        g = df.groupby(["p","type"]).agg({"total":"sum","qty":"sum"}).reset_index()
        st.dataframe(g)

elif menu == "지역분석":
    df = load_data()
    df = df[df["type"]=="현장판매"]
    g = df.groupby("region").agg({"total":"sum","qty":"sum"}).reset_index()
    st.dataframe(g)

elif menu == "엑셀":
    df = load_data()
    st.download_button("엑셀 다운로드", df.to_csv(index=False).encode('utf-8-sig'), "data.csv")

st.sidebar.button("로그아웃", on_click=lambda: st.session_state.update({"login":False}))
