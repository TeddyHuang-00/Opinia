import io
import os
import zipfile

import numpy as np
import requests
import streamlit as st

st.set_page_config("后台管理", page_icon="⚙️", initial_sidebar_state="collapsed")
st.title("⚙️后台管理")

if "admin" not in st.session_state:
    with st.form("登陆"):
        uid = st.text_input("学号", help="IAAA账户")
        passwd = st.text_input("密码", type="password", help="IAAA账户密码")
        if st.form_submit_button("登陆"):
            if uid in st.secrets["interviewer"]["admins"]:
                response = requests.post(
                    "https://treehole.pku.edu.cn/api/login/",
                    data={"uid": uid, "password": passwd},
                )
                if response.status_code == 200 and response.json()["success"]:
                    st.session_state["admin"] = True
                    st.experimental_rerun()
            else:
                st.error("账户或密码错误")
    # Make sure the page is not run until authentication is complete
    st.stop()

file_names = os.listdir("data")
comp_data = [
    (f, open(os.path.join("data", f)).read()) for f in file_names if f.endswith("data")
]
sugg_data = [
    (f, open(os.path.join("data", f)).read()) for f in file_names if f.endswith("list")
]
COMP, SUGG = st.tabs(["排序数据", "课程建议"])

with COMP:
    for f, data in comp_data:
        cols = st.columns([5, 1])
        with cols[0]:
            with st.expander(f):
                st.code(data)
        with cols[1]:
            with st.expander("删除"):
                if st.button("确认删除", type="primary", key=f + "del"):
                    os.remove(os.path.join("data", f))
                    st.experimental_rerun()

with SUGG:
    for f, data in sugg_data:
        cols = st.columns([5, 1])
        with cols[0]:
            with st.expander(f):
                st.code(data)
        with cols[1]:
            with st.expander("删除"):
                if st.button("确认删除", type="primary", key=f + "del"):
                    os.remove(os.path.join("data", f))
                    st.experimental_rerun()

if st.button("刷新数据"):
    st.experimental_rerun()
