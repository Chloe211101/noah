import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime

# 页面配置
st.set_page_config(
    page_title="公司经营看板",
    page_icon="📊",
    layout="wide"
)

# 标题
st.title("📊 公司收款及产品发出看板")

# 刷新按钮行
col_title, col_refresh = st.columns([4, 1])
with col_title:
    st.markdown(f"**更新时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}**")
with col_refresh:
    if st.button("🔄 刷新数据", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

st.markdown("---")

# 从 GitHub 加载数据
@st.cache_data(ttl=0)
def load_data():
    try:
        # 直接从 GitHub 原始文件链接读取 Excel
        url = "https://raw.githubusercontent.com/Chloe211101/noah/main/订单数据.xlsx"
        data = pd.read_excel(url)
        
        # 确保必要的列存在
        required_cols = ['订单号', '业务员', '客户名称', '总金额', '已收金额', '发出状态', '订单状态', '订单日期']
        for col in required_cols:
            if col not in data.columns:
                st.error(f"❌ Excel中缺少必要的列：{col}")
                return pd.DataFrame()
        
        # 确保金额为数字
        data['总金额'] = pd.to_numeric(data['总金额'], errors='coerce').fillna(0)
        data['已收金额'] = pd.to_numeric(data['已收金额'], errors='coerce').fillna(0)
        
        # 计算未收金额
        data['未收金额'] = data['总金额'] - data['已收金额']
        
        # 转换日期格式
        data['订单日期'] = pd.to_datetime(data['订单日期'], errors='coerce')
        if '出货日期' in data.columns:
            data['出货日期'] = pd.to_datetime(data['出货日期'], errors='coerce')
        else:
            data['出货日期'] = pd.NaT
        
        return data
    except Exception as e:
        st.error(f"❌ 读取文件出错：{e}")
        st.info("请确保 GitHub 仓库中有 订单数据.xlsx 文件")
        return pd.DataFrame()

df = load_data()

if df.empty:
    st.warning("⚠️ 请将订单数据.xlsx文件上传到 GitHub 仓库")
    st.stop()

# 显示加载成功信息
st.success(f"✅ 成功加载 {len(df)} 条订单数据")

# 获取当前年月
current_year = datetime.now().year
current_month = datetime.now().month

# 计算全年数据
yearly_data = df[df['订单日期'].dt.year == current_year]
yearly_shipped = yearly_data[yearly_data['发出状态'] == '已发出']

# 计算本月数据
monthly_data = df[(df['订单日期'].dt.year == current_year) & (df['订单日期'].dt.month == current_month)]
monthly_shipped = monthly_data[monthly_data['发出状态'] == '已发出']

# ===== 顶部KPI卡片 =====
col1, col2, col3, col4 = st.columns(4)

with col1:
    total_contract = yearly_data['总金额'].sum()
    st.metric("📝 全年销售订单签订总额", f"¥{total_contract:,.0f}", help="本年度所有签订的销售订单总金额")

with col2:
    total_shipped = yearly_shipped['总金额'].sum()
    st.metric("🚚 全年已出货订单总额", f"¥{total_shipped:,.0f}", help="本年度已完成出货的订单总金额")

with col3:
    monthly_contract = monthly_data['总金额'].sum()
    st.metric("📅 本月签订订单总额", f"¥{monthly_contract:,.0f}", help="本月签订的销售订单总金额")

with col4:
    monthly_shipped_amount = monthly_shipped['总金额'].sum()
    st.metric("📦 本月出货订单总额", f"¥{monthly_shipped_amount:,.0f}", help="本月已完成出货的订单总金额")

st.markdown("---")

# ===== 业务员业绩分析 =====
st.subheader("👔 业务员业绩分析")
st.markdown("按业务员查看签订和出货情况")

if '业务员' in df.columns and df['业务员'].notna().any():
    # 业务员数据汇总（全年）
    salesperson_summary = yearly_data.groupby('业务员').agg({
        '总金额': 'sum',
        '已收金额': 'sum',
        '未收金额': 'sum'
    }).reset_index()
    salesperson_summary.columns = ['业务员', '签订总额', '已收总额', '未收总额']

    # 计算各业务员出货总额（全年）
    shipped_by_seller = yearly_shipped.groupby('业务员')['总金额'].sum().reset_index()
    shipped_by_seller.columns = ['业务员', '出货总额']
    salesperson_summary = salesperson_summary.merge(shipped_by_seller, on='业务员', how='left').fillna(0)

    # 显示业务员表格
    st.dataframe(
        salesperson_summary,
        column_config={
            "业务员": "业务员",
            "签订总额": st.column_config.NumberColumn("签订总额", format="¥%.0f"),
            "出货总额": st.column_config.NumberColumn("出货总额", format="¥%.0f"),
            "已收总额": st.column_config.NumberColumn("已收总额", format="¥%.0f"),
            "未收总额": st.column_config.NumberColumn("未收总额", format="¥%.0f"),
        },
        use_container_width=True,
        hide_index=True
    )

    # 业务员业绩图表
    col_chart1, col_chart2 = st.columns(2)

    with col_chart1:
        fig1 = px.bar(salesperson_summary, x='业务员', y='签订总额', title='各业务员签订订单总额', text='签订总额', color='业务员')
        fig1.update_traces(texttemplate='¥%{text:.0f}', textposition='outside')
        fig1.update_layout(height=400, showlegend=False)
        st.plotly_chart(fig1, use_container_width=True)

    with col_chart2:
        fig2 = px.bar(salesperson_summary, x='业务员', y='出货总额', title='各业务员出货订单总额', text='出货总额', color='业务员')
        fig2.update_traces(texttemplate='¥%{text:.0f}', textposition='outside')
        fig2.update_layout(height=400, showlegend=False)
        st.plotly_chart(fig2, use_container_width=True)
else:
    st.info("暂无业务员数据")

st.markdown("---")

# ===== 图表区域 =====
col1, col2 = st.columns(2)

with col1:
    st.subheader("📊 收款情况分布")
    total_received = df['已收金额'].sum()
    total_unpaid = df['未收金额'].sum()
    
    if total_received > 0 or total_unpaid > 0:
        fig_payment = go.Figure(data=[go.Pie(
            labels=['已收金额', '未收金额'],
            values=[total_received, total_unpaid],
            hole=.3,
            marker_colors=['#2ecc71', '#e74c3c']
        )])
        fig_payment.update_layout(height=400)
        st.plotly_chart(fig_payment, use_container_width=True)
    else:
        st.info("暂无收款数据")

with col2:
    st.subheader("🚚 发货状态统计")
    ship_count = df['发出状态'].value_counts().reset_index()
    ship_count.columns = ['发出状态', '数量']
    fig_ship = px.bar(ship_count, x='发出状态', y='数量', color='发出状态')
    fig_ship.update_layout(height=400, showlegend=False)
    st.plotly_chart(fig_ship, use_container_width=True)

col3, col4 = st.columns(2)

with col3:
    st.subheader("📈 各业务员订单收款情况")
    seller_payment = df.groupby('业务员').agg({
        '已收金额': 'sum',
        '未收金额': 'sum'
    }).reset_index()
    
    fig_seller_payment = go.Figure()
    fig_seller_payment.add_trace(go.Bar(
        x=seller_payment['业务员'], 
        y=seller_payment['已收金额'], 
        name='已收金额', 
        marker_color='#2ecc71'
    ))
    fig_seller_payment.add_trace(go.Bar(
        x=seller_payment['业务员'], 
        y=seller_payment['未收金额'], 
        name='未收金额', 
        marker_color='#e74c3c'
    ))
    fig_seller_payment.update_layout(barmode='stack', height=400, xaxis_title="业务员", yaxis_title="金额 (¥)")
    st.plotly_chart(fig_seller_payment, use_container_width=True)

with col4:
    st.subheader("💰 订单状态分布")
    payment_count = df['订单状态'].value_counts().reset_index()
    payment_count.columns = ['订单状态', '数量']
    fig_payment_status = px.pie(payment_count, values='数量', names='订单状态')
    fig_payment_status.update_layout(height=400)
    st.plotly_chart(fig_payment_status, use_container_width=True)

st.markdown("---")

# ===== 订单明细表格 =====
st.subheader("📋 订单明细")

# 筛选器
col_filter1, col_filter2, col_filter3 = st.columns(3)

with col_filter1:
    seller_options = ["全部"] + list(df['业务员'].unique())
    seller_filter = st.multiselect("👔 筛选业务员", options=seller_options, default=["全部"])

with col_filter2:
    ship_options = ["全部"] + list(df['发出状态'].unique())
    ship_filter = st.multiselect("📦 筛选发货状态", options=ship_options, default=["全部"])

with col_filter3:
    status_options = ["全部"] + list(df['订单状态'].unique())
    status_filter = st.multiselect("💰 筛选订单状态", options=status_options, default=["全部"])

# 应用筛选
filtered_df = df.copy()

if "全部" not in seller_filter:
    filtered_df = filtered_df[filtered_df['业务员'].isin(seller_filter)]
if "全部" not in ship_filter:
    filtered_df = filtered_df[filtered_df['发出状态'].isin(ship_filter)]
if "全部" not in status_filter:
    filtered_df = filtered_df[filtered_df['订单状态'].isin(status_filter)]

# 计算创建到发货的天数
def calc_days(row):
    if pd.notna(row['订单日期']) and pd.notna(row['出货日期']):
        return (row['出货日期'] - row['订单日期']).days
    return None

filtered_df['创建到发货天数'] = filtered_df.apply(calc_days, axis=1)

# 显示表格的列
display_cols = ['订单号', '业务员', '客户名称', '总金额', '已收金额', '未收金额', 
                '发出状态', '订单状态', '订单日期', '出货日期', '创建到发货天数']
existing_cols = [col for col in display_cols if col in filtered_df.columns]

st.dataframe(
    filtered_df[existing_cols],
    column_config={
        "订单号": "订单号",
        "业务员": "业务员",
        "客户名称": "客户名称",
        "总金额": st.column_config.NumberColumn("总金额", format="¥%.0f"),
        "已收金额": st.column_config.NumberColumn("已收金额", format="¥%.0f"),
        "未收金额": st.column_config.NumberColumn("未收金额", format="¥%.0f"),
        "发出状态": "发出状态",
        "订单状态": "订单状态",
        "订单日期": st.column_config.DateColumn("订单创建日期"),
        "出货日期": st.column_config.DateColumn("订单发货日期"),
        "创建到发货天数": st.column_config.NumberColumn("创建到发货天数", format="%.0f 天"),
    },
    use_container_width=True,
    hide_index=True
)

# ===== 金额合计行 =====
st.markdown("---")
st.subheader("📊 汇总统计")

col_total1, col_total2, col_total3, col_total4, col_total5 = st.columns(5)

with col_total1:
    st.metric("📊 订单总数", f"{len(filtered_df)} 单")

with col_total2:
    st.metric("💰 总金额合计", f"¥{filtered_df['总金额'].sum():,.0f}")

with col_total3:
    st.metric("✅ 已收金额合计", f"¥{filtered_df['已收金额'].sum():,.0f}")

with col_total4:
    st.metric("⏳ 未收金额合计", f"¥{filtered_df['未收金额'].sum():,.0f}")

with col_total5:
    received_sum = filtered_df['已收金额'].sum()
    total_sum = filtered_df['总金额'].sum()
    rate = (received_sum / total_sum * 100) if total_sum > 0 else 0
    st.metric("📈 收款完成率", f"{rate:.1f}%")

st.markdown("---")
st.caption("💡 数据来自 GitHub 仓库，修改订单数据.xlsx 后重新上传即可更新")
