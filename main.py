import json
import os
from collections import namedtuple
from hashlib import md5

import numpy as np
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


def update_comparison():
    """
    Update the comparison of the uuid
    """
    with open(f"data/{st.session_state['uuid']}.data", "w") as f:
        f.writelines(st.session_state["comparison"])


def update_proposal():
    """
    Update the proposal of the uuid
    """
    with open(f"data/{st.session_state['uuid']}.list", "w") as f:
        f.writelines(st.session_state["proposal"])


if "login" not in st.session_state:

    def get_uuid(addr: str):
        uuid = addr
        for s in sorted(st.secrets["safety"]["salt"]):
            uuid = md5((uuid + s).encode()).hexdigest()
        return uuid

    with st.expander("❓ 为什么需要验证您的身份？"):
        st.caption(
            "为了保证受访者的隐私，我们会对您的身份信息进行单向加密；但是出于分析的需要，我们仍需要分辨不同同学提交的结果。为了防止混淆和被冒名顶替，我们需要您进行身份验证。另外，您的身份信息也将会一并用于获取已选修课表，方便您填写问卷。如您继续填写，则表明您接受如上所述对于您信息的使用。"
        )
    with st.expander("⚠️ 我的数据将如何处理？"):
        st.caption(
            "我们承诺您的:red[所有身份信息]不会被泄漏，并且:red[不会用于其他目的]，所用验证方式为树洞同级别一次性验证，不会在服务器上保留任何身份验证信息。经过验证后，您的身份信息将在关闭浏览器标签页时全部清除，我们只会永久保留您将要填写的问卷内容。"
        )
    with st.expander("🚫 我还是不信任你们怎么办？"):
        st.caption(
            "这个调查不是强制的，您可以：1) 查看本项目源代码；或者 2) 立刻停止受访并关闭本页。如您还有任何顾虑，请直接联系黄楠（huang_nan_2019@pku.edu.cn）"
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
                    st.session_state["token"] = response.json()["data"]["jwt"]
                    st.session_state["uuid"] = get_uuid(uid)
                    st.session_state["login"] = True
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

if "grade" not in st.session_state:
    with st.form("选择培养方案"):
        grade = st.selectbox("您目前适用的培养方案年级为：", range(2019, 2023)) or 2019
        if st.form_submit_button("确认"):
            st.session_state["grade"] = grade
            available_class = {c.name for c in load_data(grade)}
            st.session_state["classlist"] = [
                c for c in st.session_state["classlist"] if c in available_class
            ]
            st.experimental_rerun()
    st.stop()

if "comparison" not in st.session_state:
    if not os.path.exists(f"data/{st.session_state['uuid']}.data"):
        st.session_state["comparison"] = []
    else:
        with open(f"data/{st.session_state['uuid']}.data", "r") as f:
            st.session_state["comparison"] = f.readlines()

if "proposal" not in st.session_state:
    if not os.path.exists(f"data/{st.session_state['uuid']}.list"):
        st.session_state["proposal"] = []
    else:
        with open(f"data/{st.session_state['uuid']}.list", "r") as f:
            st.session_state["proposal"] = f.readlines()

KEY_NEUTRAL = "不好判断"
VOTE, SUGGEST = st.tabs(["投票", "建议"])
with VOTE:
    course_A, course_B = np.random.choice(
        st.session_state["classlist"], 2, replace=False
    )
    with st.form(f"课程比较"):
        options: list[str] = [course_A, KEY_NEUTRAL, course_B]
        useful = (
            options.index(st.select_slider("哪个课程更有用？", options, value=KEY_NEUTRAL)) - 1
        )
        relatable = (
            options.index(st.select_slider("哪个课程与本专业更相关？", options, value=KEY_NEUTRAL))
            - 1
        )
        if st.form_submit_button("确认，转到下一组"):
            with open(f"data/{st.session_state['uuid']}.data", "a+") as f:
                f.write(f"{course_A}\t{course_B}\t{useful}\t{relatable}\n")
            # st.experimental_rerun()

with SUGGEST:
    with st.form("建议新课程"):
        suggestion = st.text_input("您认为应当加入培养方案的课程名称：")
        if st.form_submit_button("提交"):
            if suggestion not in st.session_state["proposal"]:
                st.session_state["proposal"].append(suggestion)
                update_proposal()
    st.subheader("您建议的课程")
    for course in st.session_state["proposal"]:
        cols = st.columns([5, 1])
        with cols[0]:
            st.write(course)
        with cols[1]:
            if st.button("删除", key=course + "del"):
                st.session_state["proposal"].remove(course)
                update_proposal()
                st.experimental_rerun()
