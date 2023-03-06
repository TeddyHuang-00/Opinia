import json
import smtplib
from collections import namedtuple
from email.mime.text import MIMEText
from hashlib import sha256
import os

import numpy as np
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

    def get_pin(addr: str):
        pin = addr
        for s in sorted(st.secrets["interviewee"]["salt"]):
            pin = str(hash(pin + s))
        return pin[-6:]

    def get_uuid(addr: str):
        uuid = addr
        for s in sorted(st.secrets["interviewee"]["salt"]):
            uuid = sha256((uuid + s).encode()).hexdigest()
        return uuid

    def send_pin_code(recipients, pincode):
        sender = st.secrets["interviewer"]["account"]
        password = st.secrets["interviewer"]["passwd"]
        body = (
            f"Your temporary pin code is:\n\n"
            f"{pincode}\n\n"
            f"DO NOT TELL ANYONE ABOUT YOUR PIN CODE."
        )
        msg = MIMEText(body)
        msg["Subject"] = "Your temporary pin code"
        msg["From"] = f"NO REPLY <{sender}>"
        msg["To"] = recipients
        smtp_server = smtplib.SMTP_SSL("smtp.gmail.com", 465)
        smtp_server.login(sender, password)
        smtp_server.sendmail(sender, recipients, msg.as_string())
        smtp_server.quit()

    with st.expander("为什么需要验证您的身份？"):
        st.caption(
            "为了保证受访者的隐私，我们会对您的身份信息进行单向加密；但是出于分析的需要，我们仍需要分辨不同同学提交的结果。为了防止混淆和被冒名顶替，我们需要您进行身份验证。我们承诺所有身份信息将不会泄漏，并且不会用于其他目的，请您放心填写剩余部分问卷。如您有任何顾虑，请直接联系黄楠（huang_nan_2019@pku.edu.cn）"
        )
    returning, firsttime = st.tabs(["登陆", "获取 PIN 码"])
    with returning:
        with st.form("登陆"):
            addr = st.text_input("邮箱", help="必须为 @pku.edu.cn 结尾的**学号**邮箱")
            pin = st.text_input(
                "验证码", type="password", help="如果您第一次登陆，请先点击“获取 PIN 码”获取验证码，验证码当月有效"
            )
            if st.form_submit_button("登陆"):
                if addr in st.secrets["interviewee"]["address"] and pin == get_pin(
                    addr
                ):
                    st.session_state["uuid"] = get_uuid(addr)
                    st.session_state["login"] = True
                    st.experimental_rerun()
                else:
                    st.error("账户或验证码错误，如果您忘记 PIN 码，或 PIN 码已过期，请点击“获取 PIN 码”重新获取")
    with firsttime:
        with st.form("获取PIN码"):
            addr = st.text_input("邮箱", help="必须为 @pku.edu.cn 结尾的**学号**邮箱")
            if st.form_submit_button("发送 PIN 码"):
                if addr in st.secrets["interviewee"]["address"]:
                    st.info("邮件正在发送中，请耐心等候")
                    send_pin_code(addr, get_pin(addr))
                    st.success("邮件已发送！请您注意查收邮箱")
                else:
                    st.error("您不在受访范围内！")
    # Make sure the page is not run until authentication is complete
    st.stop()

st.caption(f"Your UUID: {st.session_state['uuid']}")


def get_user_info(uuid: str) -> dict[str, str]:
    if not os.path.exists(f"data/{uuid}.json"):
        with open(f"data/{uuid}.json", "w") as f:
            json.dump({}, f)
        return {}
    else:
        return json.load(open(f"data/{uuid}.json"))


def update_user_info(uuid: str, grade: int, blacklist: list[str], whitelist: list[str]):
    data = {"blacklist": blacklist, "whitelist": whitelist, "grade": grade}
    with open(f"data/{uuid}.json", "w") as f:
        json.dump(data, f)


if "grade" not in st.session_state:
    user_info = get_user_info(st.session_state["uuid"])
    if "grade" not in user_info:
        with st.form("基本信息"):
            grade = st.selectbox("您所用的培养方案", options=range(2019, 2023)) or 2019
            if st.form_submit_button("确认"):
                st.session_state["grade"] = grade
                update_user_info(st.session_state["uuid"], grade, [], [])
                st.experimental_rerun()
        st.stop()
    else:
        st.session_state["grade"] = user_info["grade"]
        st.session_state["blacklist"] = user_info["blacklist"]
        st.session_state["whitelist"] = user_info["whitelist"]

if "greylist" not in st.session_state:
    st.session_state["greylist"] = np.unique(
        [
            e.name
            for e in load_data(st.session_state["grade"])
            if e.name not in st.session_state["blacklist"]
            and e.name not in st.session_state["whitelist"]
        ]
    ).tolist()

KEY_NEUTRAL = "不好判断"
VOTE, SUGGEST = st.tabs(["投票", "建议"])
with VOTE:
    if (
        len(st.session_state["greylist"]) > 1
        and np.random.uniform()
        < len(st.session_state["greylist"])
        / (len(st.session_state["greylist"]) + len(st.session_state["whitelist"]))
        + 0.1
    ):
        # E-greedy sample
        course_A, course_B = np.random.choice(
            st.session_state["greylist"], 2, replace=False
        )
        st.session_state["greylist"].remove(course_A)
        st.session_state["greylist"].remove(course_B)
        with st.form(f"{course_A} - {course_B}"):
            unavailable = st.multiselect(
                "如果您因不了解部分课程而无法评价，请选择课名并直接提交", options=[course_A, course_B]
            )
            options = [course_A, KEY_NEUTRAL, course_B]
            useful = st.radio("哪个课程更有用？", options, horizontal=True)
            relatable = st.radio("哪个课程与本专业更相关？", options, horizontal=True)
            if st.form_submit_button("确认，转到下一组"):
                for c in [course_A, course_B]:
                    if c in unavailable:
                        st.session_state["blacklist"].append(c)
                    else:
                        st.session_state["whitelist"].append(c)
                if len(unavailable) == 0:
                    with open(f"data/{st.session_state['uuid']}.data", "a") as f:
                        f.write(
                            f"{course_A}\t{course_B}\t{options.index(useful)-1}\t{options.index(relatable)-1}\n"
                        )
                update_user_info(
                    st.session_state["uuid"],
                    st.session_state["grade"],
                    st.session_state["blacklist"],
                    st.session_state["whitelist"],
                )
                st.experimental_rerun()

    else:
        course_A, course_B = np.random.choice(
            st.session_state["whitelist"], 2, replace=False
        )
        with st.form(f"{course_A} - {course_B}"):
            options = [course_A, KEY_NEUTRAL, course_B]
            useful = st.radio("哪个课程更有用？", options, horizontal=True)
            relatable = st.radio("哪个课程与本专业更相关？", options, horizontal=True)
            if st.form_submit_button("确认，转到下一组"):
                with open(f"data/{st.session_state['uuid']}.data", "a") as f:
                    f.write(
                        f"{course_A}\t{course_B}\t{options.index(useful)-1}\t{options.index(relatable)-1}\n"
                    )
                st.experimental_rerun()
