import io
import os
import zipfile

import numpy as np
import streamlit as st

st.set_page_config("后台管理", page_icon="⚙️", initial_sidebar_state="collapsed")
st.title("⚙️后台管理")

if "admin" not in st.session_state:

    def get_pin(addr: str):
        pin = addr
        for s in sorted(st.secrets["interviewee"]["salt"]):
            pin = str(hash(pin + s))
        return pin[-6:]

    with st.form("登陆"):
        addr = st.text_input("邮箱")
        pin = st.text_input("验证码", type="password")
        if st.form_submit_button("登陆"):
            if addr in st.secrets["interviewer"]["admins"] and pin == get_pin(addr):
                st.session_state["admin"] = True
                st.experimental_rerun()
            else:
                st.error("账户或验证码错误，如果您忘记 PIN 码，或 PIN 码已过期，请点击“获取 PIN 码”重新获取")
    # Make sure the page is not run until authentication is complete
    st.stop()
