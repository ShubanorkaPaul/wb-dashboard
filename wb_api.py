import requests
import pandas as pd
from datetime import datetime, timedelta
import streamlit as st
import time


BASE_STATISTICS = "https://statistics-api.wildberries.ru"
BASE_ADVERT = "https://advert-api.wildberries.ru"


def get_headers(api_key):
    return {"Authorization": api_key}


def make_request_with_retry(url, headers, params=None, max_retries=3, initial_delay=5):
    """Делает запрос с повторными попытками при 429 ошибке"""

    for attempt in range(max_retries):
        try:
            response = requests.get(url, headers=headers, params=params, timeout=90)

            if response.status_code == 200:
                return response, None

            if response.status_code == 429:
                wait_time = initial_delay * (attempt + 1) * 12
                if attempt < max_retries - 1:
                    with st.spinner(f"⏳ WB просит подождать... ({wait_time} сек)"):
                        time.sleep(wait_time)
                    continue
                else:
                    return None, "429"

            if response.status_code == 401:
                return None, "401"

            return None, f"HTTP {response.status_code}"

        except requests.exceptions.Timeout:
            if attempt < max_retries - 1:
                time.sleep(5)
                continue
            return None, "timeout"
        except Exception as e:
            return None, str(e)

    return None, "max_retries"


@st.cache_data(ttl=1800, show_spinner=False)
def get_orders(api_key, date_from):
    """Получить заказы с указанной даты"""
    url = f"{BASE_STATISTICS}/api/v1/supplier/orders"
    params = {"dateFrom": date_from}

    response, error = make_request_with_retry(url, get_headers(api_key), params)

    if error:
        if error == "401":
            st.error("❌ Неверный API ключ")
        elif error == "429":
            st.warning("⚠️ WB ограничил запросы. Данные заказов не загружены. Подожди 1-2 минуты и обнови.")
        else:
            st.error(f"❌ Ошибка получения заказов: {error}")
        return pd.DataFrame()

    try:
        data = response.json()
        if not data:
            return pd.DataFrame()

        df = pd.DataFrame(data)
        df["date"] = pd.to_datetime(df["date"])
        df["date_only"] = df["date"].dt.date
        return df
    except Exception as e:
        st.error(f"❌ Ошибка обработки заказов: {e}")
        return pd.DataFrame()


@st.cache_data(ttl=1800, show_spinner=False)
def get_sales(api_key, date_from):
    """Получить продажи с указанной даты"""
    time.sleep(3)  # Задержка между запросами

    url = f"{BASE_STATISTICS}/api/v1/supplier/sales"
    params = {"dateFrom": date_from}

    response, error = make_request_with_retry(url, get_headers(api_key), params)

    if error:
        if error == "401":
            st.error("❌ Неверный API ключ")
        elif error == "429":
            st.warning("⚠️ WB ограничил запросы. Данные продаж не загружены. Подожди 1-2 минуты и обнови.")
        else:
            st.error(f"❌ Ошибка получения продаж: {error}")
        return pd.DataFrame()

    try:
        data = response.json()
        if not data:
            return pd.DataFrame()

        df = pd.DataFrame(data)
        df["date"] = pd.to_datetime(df["date"])
        df["date_only"] = df["date"].dt.date
        df["is_return"] = df["saleID"].str.startswith("R", na=False)
        return df
    except Exception as e:
        st.error(f"❌ Ошибка обработки продаж: {e}")
        return pd.DataFrame()


@st.cache_data(ttl=3600, show_spinner=False)
def get_stocks(api_key, date_from):
    """Получить остатки (ограничение WB: 1 запрос в минуту)"""
    time.sleep(5)  # Пауза перед запросом остатков

    url = f"{BASE_STATISTICS}/api/v1/supplier/stocks"
    params = {"dateFrom": date_from}

    response, error = make_request_with_retry(
        url, get_headers(api_key), params,
        max_retries=2, initial_delay=10
    )

    if error:
        if error == "429":
            st.info("ℹ️ Остатки временно недоступны (WB ограничивает 1 запрос в минуту). Попробуй через 1-2 минуты.")
        else:
            st.warning(f"⚠️ Не удалось загрузить остатки: {error}")
        return pd.DataFrame()

    try:
        data = response.json()
        if not data:
            return pd.DataFrame()
        return pd.DataFrame(data)
    except Exception as e:
        st.warning(f"⚠️ Ошибка обработки остатков: {e}")
        return pd.DataFrame()


@st.cache_data(ttl=1800, show_spinner=False)
def get_advert_costs(api_key, date_from, date_to):
    """Получить расходы на рекламу по дням"""
    time.sleep(2)

    url = f"{BASE_ADVERT}/adv/v1/upd"

    try:
        response = requests.get(url, headers=get_headers(api_key), timeout=60)

        if response.status_code != 200:
            return pd.DataFrame()

        data = response.json()

        if not data:
            return pd.DataFrame()

        df = pd.DataFrame(data)
        if "updTime" in df.columns:
            df["date"] = pd.to_datetime(df["updTime"]).dt.date
            df_grouped = df.groupby("date")["updSum"].sum().reset_index()
            df_grouped.columns = ["date", "advertising"]
            return df_grouped

        return pd.DataFrame()

    except Exception:
        return pd.DataFrame()


def aggregate_daily_data(orders_df, sales_df, advert_df, days):
    """Собрать данные по дням в единую таблицу"""

    end_date = datetime.now().date()
    start_date = end_date - timedelta(days=days - 1)
    date_range = pd.date_range(start=start_date, end=end_date, freq="D").date

    result = []

    for date in date_range:
        if not orders_df.empty:
            day_orders = orders_df[orders_df["date_only"] == date]
            orders_count = len(day_orders)
            orders_sum = day_orders["totalPrice"].sum() if "totalPrice" in day_orders.columns else 0
        else:
            orders_count = 0
            orders_sum = 0

        if not sales_df.empty:
            day_sales = sales_df[(sales_df["date_only"] == date) & (~sales_df["is_return"])]
            day_returns = sales_df[(sales_df["date_only"] == date) & (sales_df["is_return"])]

            sales_count = len(day_sales)
            sales_sum = day_sales["priceWithDisc"].sum() if "priceWithDisc" in day_sales.columns else 0
            returns_count = len(day_returns)
            returns_sum = day_returns["priceWithDisc"].sum() if "priceWithDisc" in day_returns.columns else 0

            for_pay = day_sales["forPay"].sum() if "forPay" in day_sales.columns else 0
            commission = sales_sum - for_pay if for_pay > 0 else 0
        else:
            sales_count = 0
            sales_sum = 0
            returns_count = 0
            returns_sum = 0
            commission = 0

        if not advert_df.empty and "date" in advert_df.columns:
            day_ads = advert_df[advert_df["date"] == date]
            advertising = day_ads["advertising"].sum() if len(day_ads) > 0 else 0
        else:
            advertising = 0

        result.append({
            "date": date.strftime("%d.%m.%Y"),
            "date_obj": date,
            "orders_count": orders_count,
            "orders_sum": float(orders_sum),
            "sales_count": sales_count,
            "sales_sum": float(sales_sum),
            "returns_count": returns_count,
            "returns_sum": float(returns_sum),
            "total_sum": float(sales_sum - returns_sum),
            "commission": float(commission),
            "acquiring": float(sales_sum * 0.015),
            "to_pay": float(sales_sum - commission),
            "storage": 0,
            "logistics": float(sales_sum * 0.12),
            "acceptance": 0,
            "deductions": 0,
            "cost_price": 0,
            "advertising": float(advertising),
            "profit": float(sales_sum - commission - (sales_sum * 0.12) - advertising),
        })

    return pd.DataFrame(result)


def aggregate_products(sales_df, stocks_df):
    """Собрать данные по товарам"""

    if sales_df.empty:
        return pd.DataFrame()

    if "is_return" in sales_df.columns:
        non_returns = sales_df[~sales_df["is_return"]].copy()
    else:
        non_returns = sales_df.copy()

    if non_returns.empty:
        return pd.DataFrame()

    agg_dict = {
        "sold": ("supplierArticle", "count"),
        "revenue": ("priceWithDisc", "sum"),
    }

    if "subject" in non_returns.columns:
        agg_dict["name"] = ("subject", "first")

    grouped = non_returns.groupby("supplierArticle").agg(**agg_dict).reset_index()
    grouped = grouped.rename(columns={"supplierArticle": "article"})

    if "name" not in grouped.columns:
        grouped["name"] = grouped["article"]

    if not stocks_df.empty and "supplierArticle" in stocks_df.columns:
        stocks_grouped = stocks_df.groupby("supplierArticle")["quantity"].sum().reset_index()
        stocks_grouped.columns = ["article", "stock"]
        grouped = grouped.merge(stocks_grouped, on="article", how="left")
        grouped["stock"] = grouped["stock"].fillna(0).astype(int)
    else:
        grouped["stock"] = 0

    grouped["cost_price_total"] = 0
    grouped["profit"] = grouped["revenue"] * 0.5

    grouped = grouped.sort_values("revenue", ascending=False).reset_index(drop=True)

    return grouped[["article", "name", "sold", "revenue", "cost_price_total", "profit", "stock"]]


def load_wb_data(api_key, days):
    """Основная функция загрузки всех данных из WB"""

    date_from = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
    date_to = datetime.now().strftime("%Y-%m-%d")

    with st.spinner("📦 Загружаем заказы..."):
        orders_df = get_orders(api_key, date_from)

    with st.spinner("💰 Загружаем продажи..."):
        sales_df = get_sales(api_key, date_from)

    with st.spinner("📊 Загружаем остатки (медленно из-за WB)..."):
        stocks_df = get_stocks(api_key, date_from)

    with st.spinner("📣 Загружаем расходы на рекламу..."):
        advert_df = get_advert_costs(api_key, date_from, date_to)

    daily = aggregate_daily_data(orders_df, sales_df, advert_df, days)
    products = aggregate_products(sales_df, stocks_df)

    return daily, products
