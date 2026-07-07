import pandas as pd
import numpy as np
from datetime import datetime, timedelta

np.random.seed(42)


def generate_demo_data(days=30):
	"""Генерирует тестовые данные для дашборда"""

	dates = [datetime.now() - timedelta(days=i) for i in range(days)]
	dates.reverse()

	articles = [
		("A123-BLK", "Куртка чёрная", 1000, 500),
		("B456-RED", "Платье красное", 850, 400),
		("C789-BLU", "Джинсы синие", 900, 450),
		("D012-WHT", "Рубашка белая", 800, 350),
		("E345-GRN", "Свитер зелёный", 800, 400),
		("F678-YLW", "Юбка жёлтая", 800, 380),
		("G901-PNK", "Топ розовый", 700, 300),
		("H234-GRY", "Кардиган серый", 800, 450),
		("I567-BRN", "Пальто коричневое", 1000, 600),
		("J890-BLK", "Ботинки чёрные", 800, 550),
		("K111-BLU", "Шапка синяя", 500, 250),
		("L222-RED", "Шарф красный", 400, 200),
	]

	daily_data = []
	for date in dates:
		orders_count = np.random.randint(80, 180)
		sales_count = int(orders_count * np.random.uniform(0.6, 0.85))
		returns_count = np.random.randint(0, 3)

		avg_price = np.random.randint(600, 900)
		orders_sum = orders_count * avg_price
		sales_sum = sales_count * avg_price
		returns_sum = returns_count * avg_price

		commission = int(sales_sum * 0.22)
		acquiring = int(sales_sum * 0.015)
		logistics = int(sales_sum * 0.12)
		storage = np.random.randint(400, 600)
		acceptance = np.random.randint(80, 200)
		deductions = np.random.randint(0, 500)
		advertising = np.random.randint(8000, 12000)

		cost_price = int(sales_sum * 0.35)

		to_pay = sales_sum - commission - acquiring - logistics - storage - acceptance - deductions
		profit = to_pay - cost_price - advertising

		daily_data.append({
			"date": date.strftime("%d.%m.%Y"),
			"date_obj": date,
			"orders_count": orders_count,
			"orders_sum": orders_sum,
			"sales_count": sales_count,
			"sales_sum": sales_sum,
			"returns_count": returns_count,
			"returns_sum": returns_sum,
			"total_sum": sales_sum - returns_sum,
			"commission": commission,
			"acquiring": acquiring,
			"to_pay": to_pay,
			"storage": storage,
			"logistics": logistics,
			"acceptance": acceptance,
			"deductions": deductions,
			"cost_price": cost_price,
			"advertising": advertising,
			"profit": profit,
		})

	df_daily = pd.DataFrame(daily_data)

	products_data = []
	for art, name, price, cost in articles:
		sold = np.random.randint(5, 60)
		revenue = sold * price
		commission_prod = int(revenue * 0.22)
		logistics_prod = int(revenue * 0.12)
		profit_prod = revenue - commission_prod - logistics_prod - (sold * cost)

		products_data.append({
			"article": art,
			"name": name,
			"sold": sold,
			"revenue": revenue,
			"cost_price_total": sold * cost,
			"profit": profit_prod,
			"stock": np.random.randint(0, 100),
		})

	df_products = pd.DataFrame(products_data)
	df_products = df_products.sort_values("profit", ascending=False).reset_index(drop=True)

	return df_daily, df_products