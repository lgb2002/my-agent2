import streamlit as st

# 페이지 객체 생성
page_1 = st.Page("page_1.py", title="홈", default=True)
page_2 = st.Page("page_2.py", title="환율 계산기")
page_3 = st.Page("page_3.py", title="환율 챗봇")

# 네비게이션 설정
pages = st.navigation([page_1, page_3, page_2])

# 실행
pages.run()
