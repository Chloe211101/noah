import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime

st.set_page_config(page_title="公司经营看板", page_icon="📊", layout="wide")

st.title("📊 公司收款及产品发出看板")

st.markdown(f"**更新时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}**")
st.markdown("---")

# 尝试从 GitHub 读取 Excel 文件
@st.cache_data(ttl=0)
def load_data():
    try:
        # 直接从 GitHub 读取 Excel 文件
        url = "https://raw.githubusercontent.com/Chloe211101/noah/main/订单数据.xlsx"
        data = pd.read_excel(url)
        
        # 必要的列检查
        required_cols = ['订单号', '业务员', '客户名称', '总金额', '已收金额', '发出状态', '订单状态', '订单日期']
        missing_cols = [col for col in required_cols if col not in data.columns]
        if missing_cols:
            st.error(f"Excel 缺少以下列：{missing_cols}")
            return pd.DataFrame()
        
        # 处理数据
        data['总金额'] = pd.to_numeric(data['总金额'], errors='coerce').fillna(0)
        data['已收金额'] = pd.to_numeric(data['已收金额'], errors='coerce').fillna(0)
        data['未收金额'] = data['总金额'] - data['已收金额']
        data['订单日期'] = pd.to_datetime(data['订单日期'], errors='coerce')
        
        if '出货日期' in data.columns:
            data['出货日期'] = pd.to_datetime(data['出货日期'], errors='coerce')
        else:
            data['出货日期'] = pd.NaT
            
        return data
    except Exception as e:
        st.error(f"读取文件出错：{str(e)}")
        st.info("请检查：1) 订单数据.xlsx 是否在 GitHub 仓库中 2) 列名是否正确")
        return pd.DataFrame()

df = load_data()

if df.empty:
    st.stop()

st.success(f"✅ 成功加载 {len(df)} 条订单数据")

# 获取当前年月
current_year = datetime.now().year
current_month = datetime.now().month

# ===== KPI 卡片 =====
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("📝 订单签订总额", f"¥{df['总金额'].sum():,.0f}")

with col2:
    shipped = df[df['发出状态'] == '已发出']['总金额'].sum()
    st.metric("🚚 已出货订单总额", f"¥{shipped:,.0f}")

with col3:
    monthly = df[(df['订单日期'].dt.year == current_year) & (df['订单日期'].dt.month == current_month)]['总金额'].sum()
    st.metric("📅 本月签订订单总额", f"¥{monthly:,.0f}")

with col4:
    monthly_shipped = df[(df['出货日期'].dt.year == current_year) & (df['出货日期'].dt.month == current_month) & (df['发出状态'] == '已发出')]['总金额'].sum()
    st.metric("📦 本月出货订单总额", f"¥{monthly_shipped:,.0f}")

st.markdown("---")

# ===== 订单明细 =====
st.subheader("📋 订单明细")

def calc_days(row):
    if pd.notna(row['订单日期']) and pd.notna(row['出货日期']):
        return (row['出货日期'] - row['订单日期']).days
    return None

df['创建到发货天数'] = df.apply(calc_days, axis=1)

display_cols = ['订单号', '业务员', '客户名称', '总金额', '已收金额', '未收金额', '发出状态', '订单状态', '订单日期', '出货日期', '创建到发货天数']
existing_cols = [col for col in display_cols if col in df.columns]

st.dataframe(df[existing_cols], use_container_width=True, hide_index=True)

st.markdown("---")
st.caption("数据来自 GitHub 仓库中的订单数据.xlsx")
