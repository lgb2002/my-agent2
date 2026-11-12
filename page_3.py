import math
import re
import uuid

import requests
import streamlit as st
from langchain.chat_models import init_chat_model
from dotenv import load_dotenv
from langchain.agents import create_agent
from langchain.tools import tool
from langchain.messages import HumanMessage
from langgraph.checkpoint.memory import InMemorySaver


@tool
def get_exchange_rate(base_currency: str, quote_currency: str, amount: float = 1.0) -> str:
    """Frankfurter API에서 최신 공개 환율을 조회하고 금액을 환산합니다.

    base_currency: 환전할 통화의 영문 3자리 코드 (예: USD, KRW, EUR).
    quote_currency: 결과 통화의 영문 3자리 코드 (예: KRW, USD, JPY).
    amount: 환전할 금액 (기본값 1).
    """
    base = base_currency.strip().upper()
    quote = quote_currency.strip().upper()

    if not re.fullmatch(r"[A-Z]{3}", base) or not re.fullmatch(r"[A-Z]{3}", quote):
        return "통화는 USD, KRW처럼 영문 세 글자 코드로 입력해 주세요."
    if not math.isfinite(amount) or amount < 0:
        return "금액은 0 이상의 유한한 숫자로 입력해 주세요."
    if base == quote:
        return f"{amount:,.2f} {base} = {amount:,.2f} {quote} (같은 통화이므로 환율 조회 불필요)"

    try:
        response = requests.get(
            f"https://api.frankfurter.dev/v2/rate/{base}/{quote}",
            timeout=10,
        )
        response.raise_for_status()
        data = response.json()
        rate = float(data["rate"])
        rate_date = data["date"]
        converted = amount * rate

        decimals = 0 if quote == "KRW" else 2
        return (
            f"{amount:,.2f} {base} = {converted:,.{decimals}f} {quote}\n"
            f"환율: 1 {base} = {rate:,.6f} {quote}\n"
            f"환율 기준일: {rate_date}\n"
            "출처: Frankfurter API (최신 공개 참조 환율, 실시간 매매 시세 아님)"
        )
    except (requests.RequestException, KeyError, TypeError, ValueError, OverflowError):
        return "환율 조회에 실패했습니다. 잠시 후 다시 질문해 주세요. 조회에 실패한 환율은 추측하지 마세요."


load_dotenv()

model = init_chat_model("gpt-5.5")

if "fx_agent" not in st.session_state:
    st.session_state.fx_agent = create_agent(
        model,
        tools=[get_exchange_rate],
        checkpointer=InMemorySaver(),
        system_prompt=(
            "당신은 환율 조회를 돕는 한국어 AI 챗봇입니다. "
            "사용자가 환율이나 통화 환산을 묻는다면 반드시 get_exchange_rate 도구를 호출하세요. "
            "원화는 KRW, 미국 달러는 USD, 일본 엔화는 JPY, 유로는 EUR입니다. "
            "도구가 알려준 환율과 기준일만 이용하고 숫자나 날짜를 만들어내지 마세요. "
            "Frankfurter는 최신 공개 참조 환율이지 초단위 실시간 거래 시세가 아님을 명확히 설명하세요. "
            "API 조회 실패 시 환율을 추측하지 마세요. "
            "간결하고 이해하기 쉽게 답변하세요."
        ),
    )

if "fx_messages" not in st.session_state:
    st.session_state.fx_messages = []

if "fx_thread_id" not in st.session_state:
    st.session_state.fx_thread_id = str(uuid.uuid4())

st.title("환율 챗봇")

prompt = st.chat_input("환율에 대해 질문해 보세요")
if prompt:
    st.session_state.fx_messages.append({"role": "user", "content": prompt})
    try:
        response = st.session_state.fx_agent.invoke(
            {"messages": [HumanMessage(prompt)]},
            {"configurable": {"thread_id": st.session_state.fx_thread_id}},
        )
        answer = response["messages"][-1].content
        st.session_state.fx_messages.append({"role": "assistant", "content": answer})
    except Exception:
        st.session_state.fx_messages.append({
            "role": "assistant",
            "content": "응답을 가져오지 못했습니다. API 키와 네트워크 연결을 확인해 주세요.",
        })

for message in st.session_state.fx_messages:
    with st.chat_message(message["role"]):
        st.write(message["content"])
