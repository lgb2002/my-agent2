import math

import requests
import streamlit as st

st.title("환율 계산기")

amount_text = st.text_input("금액", value="100")

# 버튼을 각각 먼저 생성해야 어느 버튼을 눌러도 둘 다 화면에 남습니다.
krw_to_usd = st.button("원화 → 달러")
usd_to_krw = st.button("달러 → 원화")

if krw_to_usd or usd_to_krw:
    try:
        amount = float(amount_text.replace(",", "").strip())
        if not math.isfinite(amount) or amount < 0:
            raise ValueError("금액은 0 이상의 숫자여야 합니다.")
    except ValueError:
        st.error("금액에 0 이상의 숫자를 입력해 주세요.")
    else:
        base, quote = ("KRW", "USD") if krw_to_usd else ("USD", "KRW")
        try:
            response = requests.get(
                f"https://api.frankfurter.dev/v2/rate/{base}/{quote}",
                timeout=10,
            )
            response.raise_for_status()
            data = response.json()
            rate = float(data["rate"])
            if not math.isfinite(rate) or rate <= 0:
                raise ValueError("유효하지 않은 환율")
            converted = amount * rate
            decimals = 2 if quote == "USD" else 0

            st.write(f"{amount:,.2f} {base} = {converted:,.{decimals}f} {quote}")
        except (requests.RequestException, KeyError, TypeError, ValueError, OverflowError):
            st.error("환율을 불러오지 못했습니다. 다시 시도해 주세요.")
