import json
import os
from collections import namedtuple
from hashlib import sha256

import requests
import streamlit as st

ClassItem = namedtuple("ClassItem", ["id", "name"])

st.set_page_config("议见 Opinia", page_icon="⚙️", initial_sidebar_state="collapsed")
st.title("💬 议见 | Opinia")


@st.cache_data
def load_data(year: int = 2019):
    """
    Load data from the given year
    """
    assert 2019 <= year <= 2022, "Year must be between 2019 and 2022"
    data: list[ClassItem] = [
        ClassItem(e["id"], e["name"]) for e in json.load(open(f"static/{year}.json"))
    ]
    return data


if st.secrets["interviewee"]["require_auth"] and "login" not in st.session_state:

    def get_uuid(addr: str):
        uuid = addr
        for s in sorted(st.secrets["interviewee"]["salt"]):
            uuid = sha256((uuid + s).encode()).hexdigest()
        return uuid

    with st.expander("为什么需要验证您的身份？"):
        st.caption(
            "为了保证受访者的隐私，我们会对您的身份信息进行单向加密；但是出于分析的需要，我们仍需要分辨不同同学提交的结果。为了防止混淆和被冒名顶替，我们需要您进行身份验证。我们承诺所有身份信息将不会泄漏，并且不会用于其他目的，请您放心填写剩余部分问卷。如您有任何顾虑，请直接联系黄楠（huang_nan_2019@pku.edu.cn）"
        )
    with st.form("登陆"):
        uid = st.text_input("学号", help="IAAA账户")
        passwd = st.text_input("密码", type="password", help="IAAA账户密码")
        if st.form_submit_button("登陆"):
            if uid in st.secrets["interviewee"]["UID"]:
                response = requests.post(
                    "https://treehole.pku.edu.cn/api/login/",
                    data={"uid": uid, "password": passwd},
                )
                if response.status_code == 200 and response.json()["success"]:
                    st.session_state["login"] = True
                    st.session_state["token"] = response.json()["data"]["jwt"]
                    st.experimental_rerun()
            else:
                st.error("账户或密码错误")
    # Make sure the page is not run until authentication is complete
    st.stop()

st.caption(f"Your UUID: {st.session_state['uuid']}")
if "classlist" not in st.session_state:
    response = requests.get(
        "https://treehole.pku.edu.cn/api/course/score",
        headers={"authorization": f"Bearer {st.session_state['token']}"},
    )
    if response.status_code == 200 and response.json()["success"]:
        st.session_state["classlist"] = [
            c["kcmc"] for c in response.json()["data"]["score"]["cjxx"]
        ]

st.write(st.session_state["classlist"])
