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

# 添加刷新按钮行
col_title, col_refresh = st.columns([4, 1])
with col_title:
    st.markdown(f"**更新时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}**")
with col_refresh:
    if st.button("🔄 刷新数据", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

st.markdown("---")

# 加载数据（从 GitHub 读取）
@st.cache_data(ttl=0)
def load_data():
    try:
        # 使用英文文件名
        url = "https://raw.githubusercontent.com/Chloe211101/noah/main/orders.xlsx"
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
        st.info("请确保 GitHub 仓库中有 orders.xlsx 文件")
        return pd.DataFrame()

df = load_data()

if df.empty:
    st.warning("⚠️ 请将 orders.xlsx 文件上传到 GitHub 仓库")
    st.stop()

# 显示加载成功信息
st.success(f"✅ 成功加载 {len(df)} 条订单数据")

# 显示数据概览（帮助排查）
with st.expander("📊 数据概览（点击展开）"):
    st.write(f"订单日期范围：{df['订单日期'].min()} 至 {df['订单日期'].max()}")
    st.write(f"出货日期范围：{df['出货日期'].min()} 至 {df['出货日期'].max()}")
    st.write(f"发出状态分布：{dict(df['发出状态'].value_counts())}")
    st.write("前5行数据预览：")
    st.dataframe(df.head(), use_container_width=True)

st.markdown("---")

# 获取当前年月
current_year = datetime.now().year
current_month = datetime.now().month

# ===== 顶部KPI卡片 =====
col1, col2, col3, col4 = st.columns(4)

with col1:
    total_contract = df['总金额'].sum()
    st.metric("📝 订单签订总额", f"¥{total_contract:,.0f}", help="所有订单总金额")

with col2:
    shipped_total = df[df['发出状态'] == '已发出']['总金额'].sum()
    st.metric("🚚 已出货订单总额", f"¥{shipped_total:,.0f}", help="已发货订单的总金额")

with col3:
    monthly_contract = df[
        (df['订单日期'].dt.year == current_year) & 
        (df['订单日期'].dt.month == current_month)
    ]['总金额'].sum()
    st.metric("📅 本月签订订单总额", f"¥{monthly_contract:,.0f}", help=f"{current_year}年{current_month}月签订的订单总金额")

with col4:
    monthly_shipped = df[
        (df['出货日期'].dt.year == current_year) & 
        (df['出货日期'].dt.month == current_month) &
        (df['发出状态'] == '已发出')
    ]['总金额'].sum()
    st.metric("📦 本月出货订单总额", f"¥{monthly_shipped:,.0f}", help=f"{current_year}年{current_month}月发货的订单总金额")

st.markdown("---")

# ===== 业务员业绩分析 =====
st.subheader("👔 业务员业绩分析")

if '业务员' in df.columns and df['业务员'].notna().any():
    salesperson_summary = df.groupby('业务员').agg({
        '总金额': 'sum',
        '已收金额': 'sum',
        '未收金额': 'sum'
    }).reset_index()
    salesperson_summary.columns = ['业务员', '签订总额', '已收总额', '未收总额']

    shipped_by_seller = df[df['发出状态'] == '已发出'].groupby('业务员')['总金额'].sum().reset_index()
    shipped_by_seller.columns = ['业务员', '出货总额']
    salesperson_summary = salesperson_summary.merge(shipped_by_seller, on='业务员', how='left').fillna(0)

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
    fig_seller_payment.update_layout(
        barmode='stack', 
        height=400, 
        xaxis_title="业务员", 
        yaxis_title="金额 (¥)",
        legend_title=""
    )
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

# 筛选器 - 第一行（下拉筛选）
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

# 筛选器 - 第二行（日期范围筛选）
st.markdown("---")
col_date1, col_date2 = st.columns(2)

with col_date1:
    st.write("**📅 订单创建日期筛选**")
    use_order_date_filter = st.checkbox("启用订单创建日期筛选", key="use_order_date")
    
    if use_order_date_filter:
        min_order_date = df['订单日期'].min()
        max_order_date = df['订单日期'].max()
        
        if pd.notna(min_order_date) and pd.notna(max_order_date):
            date_range_order = st.date_input(
                "选择订单创建日期范围",
                value=[min_order_date, max_order_date],
                min_value=min_order_date,
                max_value=max_order_date,
                key="order_date_filter"
            )
        else:
            date_range_order = None
            st.warning("暂无订单日期数据")
    else:
        date_range_order = None
        st.info("✅ 不筛选（显示全部）")

with col_date2:
    st.write("**📅 订单发货日期筛选**")
    use_ship_date_filter = st.checkbox("启用订单发货日期筛选", key="use_ship_date")
    
    if use_ship_date_filter:
        valid_ship_dates = df['出货日期'].dropna()
        if len(valid_ship_dates) > 0:
            min_ship_date = valid_ship_dates.min()
            max_ship_date = valid_ship_dates.max()
            date_range_ship = st.date_input(
                "选择订单发货日期范围",
                value=[min_ship_date, max_ship_date],
                min_value=min_ship_date,
                max_value=max_ship_date,
                key="ship_date_filter"
            )
        else:
            date_range_ship = None
            st.info("暂无发货日期数据（未发货订单）")
    else:
        date_range_ship = None
        st.info("✅ 不筛选（显示全部）")

st.markdown("---")

# 应用筛选
filtered_df = df.copy()

if "全部" not in seller_filter:
    filtered_df = filtered_df[filtered_df['业务员'].isin(seller_filter)]
if "全部" not in ship_filter:
    filtered_df = filtered_df[filtered_df['发出状态'].isin(ship_filter)]
if "全部" not in status_filter:
    filtered_df = filtered_df[filtered_df['订单状态'].isin(status_filter)]

if use_order_date_filter and date_range_order and len(date_range_order) == 2:
    start_date = pd.to_datetime(date_range_order[0])
    end_date = pd.to_datetime(date_range_order[1])
    filtered_df = filtered_df[(filtered_df['订单日期'] >= start_date) & (filtered_df['订单日期'] <= end_date)]

if use_ship_date_filter and date_range_ship and len(date_range_ship) == 2:
    start_ship = pd.to_datetime(date_range_ship[0])
    end_ship = pd.to_datetime(date_range_ship[1])
    filtered_df = filtered_df[(filtered_df['出货日期'] >= start_ship) & (filtered_df['出货日期'] <= end_ship)]

# 计算创建到发货的天数
def calc_days(row):
    if pd.notna(row['订单日期']) and pd.notna(row['出货日期']):
        days = (row['出货日期'] - row['订单日期']).days
        return days if days >= 0 else None
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
    order_count = len(filtered_df)
    st.metric("📊 订单总数", f"{order_count} 单")

with col_total2:
    total_amount = filtered_df['总金额'].sum()
    st.metric("💰 总金额合计", f"¥{total_amount:,.0f}")

with col_total3:
    received_amount = filtered_df['已收金额'].sum()
    st.metric("✅ 已收金额合计", f"¥{received_amount:,.0f}")

with col_total4:
    unpaid_amount = filtered_df['未收金额'].sum()
    st.metric("⏳ 未收金额合计", f"¥{unpaid_amount:,.0f}")

with col_total5:
    collection_rate = (received_amount / total_amount * 100) if total_amount > 0 else 0
    st.metric("📈 收款完成率", f"{collection_rate:.1f}%")

# 显示各状态金额分布
st.markdown("---")
col_status1, col_status2, col_status3 = st.columns(3)

with col_status1:
    if len(filtered_df) > 0:
        ship_summary = filtered_df.groupby('发出状态')['总金额'].sum().reset_index()
        ship_summary.columns = ['发出状态', '金额']
        st.write("**按发出状态统计**")
        for _, row in ship_summary.iterrows():
            st.write(f"{row['发出状态']}: ¥{row['金额']:,.0f}")
    else:
        st.write("**按发出状态统计**")
        st.write("暂无数据")

with col_status2:
    if len(filtered_df) > 0:
        status_summary = filtered_df.groupby('订单状态')['总金额'].sum().reset_index()
        status_summary.columns = ['订单状态', '金额']
        st.write("**按订单状态统计**")
        for _, row in status_summary.iterrows():
            st.write(f"{row['订单状态']}: ¥{row['金额']:,.0f}")
    else:
        st.write("**按订单状态统计**")
        st.write("暂无数据")

with col_status3:
    if len(filtered_df) > 0:
        seller_summary = filtered_df.groupby('业务员')['总金额'].sum().reset_index()
        seller_summary.columns = ['业务员', '金额']
        st.write("**按业务员统计**")
        for _, row in seller_summary.iterrows():
            st.write(f"{row['业务员']}: ¥{row['金额']:,.0f}")
    else:
        st.write("**按业务员统计**")
        st.write("暂无数据")

st.markdown("---")
st.caption("💡 修改 orders.xlsx 后上传到 GitHub，然后点击右上角的【刷新数据】按钮即可更新看板 | 所有筛选器可以组合使用，汇总统计会自动更新")
