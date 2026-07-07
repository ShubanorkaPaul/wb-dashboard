import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import io
from demo_data import generate_demo_data
from wb_api import load_wb_data


st.set_page_config(
	page_title="WB Дашборд",
	page_icon="📊",
	layout="wide",
	initial_sidebar_state="expanded"
)

st.markdown("""
<style>
	.main {padding-top: 1rem;}
	.stMetric {
		background-color: #f0f2f6;
		padding: 15px;
		border-radius: 10px;
		border-left: 4px solid #4CAF50;
	}
	h1 {color: #1f2937;}
	h2 {color: #374151; border-bottom: 2px solid #e5e7eb; padding-bottom: 8px;}
</style>
""", unsafe_allow_html=True)


with st.sidebar:
	st.title("⚙️ Настройки")

	data_source = st.radio(
		"Источник данных",
		["🔌 WB API", "📊 Демо данные"],
		index=0
	)

	st.markdown("---")

	period = st.selectbox(
		"📅 Период",
		["7 дней", "14 дней", "30 дней", "60 дней", "90 дней"],
		index=2
	)
	days = int(period.split()[0])

	st.markdown("---")

	api_key = ""
	if data_source == "🔌 WB API":
		api_key = st.text_input(
			"🔑 API ключ WB",
			type="password",
			help="Токен из личного кабинета WB"
		)

		if api_key:
			st.success("✅ Ключ введён")
		else:
			st.warning("⚠️ Введи API ключ")

	st.markdown("---")
	st.caption("🔄 Обновлено: " + datetime.now().strftime("%H:%M:%S"))

	if st.button("🔄 Обновить данные", use_container_width=True):
		st.cache_data.clear()
		st.rerun()


st.title("📊 WB Аналитика")
st.caption(f"Период: последние {days} дней")


if data_source == "📊 Демо данные":
	df_daily, df_products = generate_demo_data(days)
	st.info("📌 Показаны демо-данные. Переключись на WB API в настройках для реальных данных.")

elif data_source == "🔌 WB API":
	if not api_key:
		st.warning("👈 Введи API ключ в боковой панели чтобы загрузить данные")
		st.stop()

	try:
		df_daily, df_products = load_wb_data(api_key, days)

		if df_daily.empty or df_daily["sales_sum"].sum() == 0:
			st.warning("⚠️ Нет данных за выбранный период. Попробуй увеличить период.")
			st.stop()

	except Exception as e:
		st.error(f"❌ Ошибка загрузки данных: {e}")
		st.stop()


current_period = df_daily.tail(days)
prev_period = df_daily.head(len(df_daily) - days) if len(df_daily) > days else df_daily

total_revenue = current_period["sales_sum"].sum()
total_orders = current_period["orders_count"].sum()
total_profit = current_period["profit"].sum()
total_ads = current_period["advertising"].sum()
total_returns = current_period["returns_count"].sum()
total_sales = current_period["sales_count"].sum()

buyout_rate = (total_sales / total_orders * 100) if total_orders > 0 else 0
avg_check = (total_revenue / total_sales) if total_sales > 0 else 0
return_rate = (total_returns / total_sales * 100) if total_sales > 0 else 0
roi_ads = (total_profit / total_ads * 100) if total_ads > 0 else 0


def calc_delta(current, previous):
	if previous == 0:
		return 0
	return round((current - previous) / previous * 100, 1)


if len(prev_period) > 0:
	prev_revenue = prev_period["sales_sum"].mean() * days
	prev_orders = prev_period["orders_count"].mean() * days
	prev_profit = prev_period["profit"].mean() * days
else:
	prev_revenue = total_revenue
	prev_orders = total_orders
	prev_profit = total_profit


st.subheader("💎 Ключевые показатели")

col1, col2, col3, col4 = st.columns(4)

with col1:
	st.metric(
		"💰 Выручка",
		f"{total_revenue:,.0f} ₽".replace(",", " "),
		f"{calc_delta(total_revenue, prev_revenue)}%" if prev_revenue > 0 else None
	)

with col2:
	st.metric(
		"📦 Заказов",
		f"{total_orders:,} шт".replace(",", " "),
		f"{calc_delta(total_orders, prev_orders)}%" if prev_orders > 0 else None
	)

with col3:
	st.metric(
		"💵 Прибыль",
		f"{total_profit:,.0f} ₽".replace(",", " "),
		f"{calc_delta(total_profit, prev_profit)}%" if prev_profit > 0 else None
	)

with col4:
	st.metric(
		"📈 ROI рекламы",
		f"{roi_ads:.0f}%" if total_ads > 0 else "—",
		None
	)


col5, col6, col7, col8 = st.columns(4)

with col5:
	st.metric("🎯 % выкупа", f"{buyout_rate:.1f}%")

with col6:
	st.metric("💸 Реклама", f"{total_ads:,.0f} ₽".replace(",", " "))

with col7:
	st.metric("📊 Средний чек", f"{avg_check:,.0f} ₽".replace(",", " "))

with col8:
	st.metric("↩️ % возвратов", f"{return_rate:.1f}%")


st.markdown("---")


st.subheader("📈 Динамика продаж")

fig = go.Figure()

fig.add_trace(go.Scatter(
	x=current_period["date"],
	y=current_period["sales_sum"],
	mode="lines+markers",
	name="Продажи, ₽",
	line=dict(color="#3B82F6", width=3),
	marker=dict(size=8)
))

fig.add_trace(go.Scatter(
	x=current_period["date"],
	y=current_period["profit"],
	mode="lines+markers",
	name="Прибыль, ₽",
	line=dict(color="#10B981", width=3),
	marker=dict(size=8)
))

fig.add_trace(go.Scatter(
	x=current_period["date"],
	y=current_period["advertising"],
	mode="lines+markers",
	name="Реклама, ₽",
	line=dict(color="#F59E0B", width=2, dash="dot"),
	marker=dict(size=6)
))

fig.update_layout(
	height=400,
	hovermode="x unified",
	legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
	margin=dict(l=0, r=0, t=30, b=0),
	plot_bgcolor="white",
	xaxis=dict(showgrid=True, gridcolor="#f0f0f0"),
	yaxis=dict(showgrid=True, gridcolor="#f0f0f0")
)

st.plotly_chart(fig, use_container_width=True)


col_left, col_right = st.columns(2)

with col_left:
	st.subheader("🥧 Структура расходов")

	expenses = {
		"Комиссия ВБ": current_period["commission"].sum(),
		"Логистика": current_period["logistics"].sum(),
		"Реклама": current_period["advertising"].sum(),
		"Эквайринг": current_period["acquiring"].sum(),
	}

	expenses = {k: v for k, v in expenses.items() if v > 0}

	if expenses:
		fig_pie = px.pie(
			values=list(expenses.values()),
			names=list(expenses.keys()),
			hole=0.5,
			color_discrete_sequence=px.colors.qualitative.Set2
		)
		fig_pie.update_traces(textposition="outside", textinfo="percent+label")
		fig_pie.update_layout(
			height=400,
			margin=dict(l=0, r=0, t=0, b=0),
			showlegend=False
		)
		st.plotly_chart(fig_pie, use_container_width=True)
	else:
		st.info("Нет данных о расходах")


with col_right:
	st.subheader("📊 Заказы по дням")

	fig_bar = px.bar(
		current_period,
		x="date",
		y="orders_count",
		color="orders_count",
		color_continuous_scale="Blues",
		labels={"orders_count": "Заказов", "date": "Дата"}
	)
	fig_bar.update_layout(
		height=400,
		margin=dict(l=0, r=0, t=0, b=0),
		plot_bgcolor="white",
		showlegend=False,
		coloraxis_showscale=False
	)
	st.plotly_chart(fig_bar, use_container_width=True)


st.markdown("---")


st.subheader("🏆 ТОП товаров по выручке")

if not df_products.empty:
	df_top = df_products.head(10).copy()
	df_top.index = df_top.index + 1
	df_top_display = df_top[["article", "name", "sold", "revenue", "profit", "stock"]].copy()
	df_top_display.columns = ["Артикул", "Название", "Продано, шт", "Выручка, ₽", "Прибыль, ₽", "Остаток"]

	st.dataframe(df_top_display, use_container_width=True, height=400)
else:
	st.info("Нет данных о товарах")


st.markdown("---")


st.subheader("🔔 Уведомления")

col_a, col_b, col_c = st.columns(3)

with col_a:
	st.markdown("### 📦 Заканчиваются остатки")
	if not df_products.empty:
		low_stock = df_products[(df_products["stock"] > 0) & (df_products["stock"] < 10)].sort_values("stock")
		if len(low_stock) > 0:
			for _, row in low_stock.head(5).iterrows():
				st.warning(f"**{row['article']}** — {row['stock']} шт")
		else:
			st.success("Все остатки в норме ✅")
	else:
		st.info("Нет данных")

with col_b:
	st.markdown("### 🚨 Нет в остатках")
	if not df_products.empty:
		out_of_stock = df_products[df_products["stock"] == 0]
		if len(out_of_stock) > 0:
			for _, row in out_of_stock.head(5).iterrows():
				st.error(f"**{row['article']}** — закончился")
		else:
			st.success("Все товары в наличии ✅")
	else:
		st.info("Нет данных")

with col_c:
	st.markdown("### 💡 Инсайты")

	if len(current_period) > 0 and current_period["sales_sum"].sum() > 0:
		best_day = current_period.loc[current_period["sales_sum"].idxmax()]
		worst_day = current_period.loc[current_period["sales_sum"].idxmin()]

		st.info(f"📈 Лучший день: **{best_day['date']}**")
		st.info(f"📉 Худший день: **{worst_day['date']}**")

		avg_daily = current_period["sales_sum"].mean()
		st.info(f"📊 Средняя выручка: **{avg_daily:,.0f} ₽/день**".replace(",", " "))
	else:
		st.info("Нет данных для анализа")


st.markdown("---")


st.subheader("📊 Сводка по дням")

summary = current_period[[
	"date", "orders_count", "orders_sum", "sales_count", "sales_sum",
	"commission", "logistics", "advertising", "profit"
]].copy()

summary.columns = [
	"Дата", "Заказы шт", "Заказы ₽", "Продажи шт", "Продажи ₽",
	"Комиссия", "Логистика", "Реклама", "Прибыль"
]

st.dataframe(summary, use_container_width=True, height=400)


output = io.BytesIO()
with pd.ExcelWriter(output, engine="openpyxl") as writer:
	summary.to_excel(writer, sheet_name="Сводка по дням", index=False)
	if not df_products.empty:
		df_products.to_excel(writer, sheet_name="Товары", index=False)

st.download_button(
	label="📥 Скачать отчёт в Excel",
	data=output.getvalue(),
	file_name=f"wb_report_{datetime.now().strftime('%Y%m%d')}.xlsx",
	mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
	use_container_width=True
)


st.markdown("---")
st.caption("💡 Данные обновляются раз в 10 минут. Нажми 'Обновить данные' для принудительного обновления.")