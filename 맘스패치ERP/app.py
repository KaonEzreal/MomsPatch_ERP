import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime
import os

st.set_page_config(page_title="맘스패치 ERP", page_icon="🟢", layout="wide")

DB_FILE = "momspatch.db"

# =========================
# 🎨 카카오 느낌 UI (화이트 + 연두)
# =========================
st.markdown("""
<style>
body { background-color: #ffffff; }
section[data-testid="stSidebar"] { background-color: #f4fff4; }
h1 { color:#2ecc71; }
.stButton>button { background:#7ed957; color:black; border-radius:8px; }
.stButton>button:hover { background:#2ecc71; }
</style>
""", unsafe_allow_html=True)

st.title("🟢 맘스패치 ERP 시스템")

# =========================
# DB
# =========================
def get_conn():
    return sqlite3.connect(DB_FILE, check_same_thread=False)

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
    conn.commit()
    conn.close()

init_db()

# =========================
# 유틸
# =========================
def won(x):
    return f"{int(x):,}원"

# =========================
# 데이터 처리
# =========================
def insert_sale(data):
    conn = get_conn()
    c = conn.cursor()
    c.execute("""
    INSERT INTO sales (created_at,user,type,sale_date,item,qty,price,total,region)
    VALUES (?,?,?,?,?,?,?,?,?)
    """, data)
    conn.commit()
    conn.close()

def load_df():
    conn = get_conn()
    df = pd.read_sql("SELECT * FROM sales", conn)
    conn.close()
    return df

# =========================
# 메뉴
# =========================
menu = st.sidebar.radio("메뉴", ["입력","대시보드","DB관리"])

# =========================
# 입력
# =========================
if menu == "입력":
    st.subheader("판매 입력")
    with st.form("f"):
        name = st.text_input("담당자")
        t = st.selectbox("구분", ["전화주문","온라인판매","현장판매"])
        d = st.date_input("날짜")
        item = st.text_input("상품")
        qty = st.number_input("수량",1)
        price = st.number_input("단가",0,step=1000)
        region = st.text_input("지역") if t=="현장판매" else ""

        if st.form_submit_button("저장"):
            total = qty*price
            insert_sale((datetime.now(), name, t, str(d), item, qty, price, total, region))
            st.success(f"저장 완료 {won(total)}")

# =========================
# 대시보드 (그래프 포함)
# =========================
elif menu == "대시보드":
    df = load_df()

    if df.empty:
        st.warning("데이터 없음")
    else:
        df['sale_date'] = pd.to_datetime(df['sale_date'])

        period = st.radio("조회", ["일별","월별","연도별"])

        if period == "일별":
            df['group'] = df['sale_date'].dt.date
        elif period == "월별":
            df['group'] = df['sale_date'].dt.to_period('M').astype(str)
        else:
            df['group'] = df['sale_date'].dt.year

        g = df.groupby('group')['total'].sum().reset_index()

        st.subheader("매출 그래프")
        st.line_chart(g.set_index('group'))

        st.subheader("매출 테이블")
        g['total'] = g['total'].apply(won)
        st.dataframe(g)

# =========================
# DB관리
# =========================
elif menu == "DB관리":
    df = load_df()

    st.subheader("전체 데이터")
    st.dataframe(df)

    ids = st.multiselect("삭제 ID", df['id'])
    if st.button("선택 삭제"):
        conn = get_conn()
        c = conn.cursor()
        for i in ids:
            c.execute("DELETE FROM sales WHERE id=?",(i,))
        conn.commit()
        conn.close()
        st.success("삭제 완료")
        st.rerun()

    st.subheader("전체 초기화")
    if st.button("DB 전체 삭제"):
        os.remove(DB_FILE)
        init_db()
        st.success("초기화 완료")
