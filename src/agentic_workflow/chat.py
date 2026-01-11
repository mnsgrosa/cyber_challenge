import httpx
import streamlit as st

if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

if "credentials" not in st.session_state:
    st.session_state.credentials = {}

if "chat_history" not in st.session_state:
    st.session_state["chat_history"] = []


def validate_credentials(username, password):
    credentials = {"username": username, "password": password}

    try:
        with httpx.Client() as client:
            response = client.post("http://backend:8000/auth", json=credentials)
        if response.status_code == 401:
            st.error("Unauthorized user")
            return None
        data = response.json()
        return str(data["token"])
    except Exception as e:
        st.error(f"Erro: {e}")
        return None


def login_page():
    st.title("Login page")

    with st.form("login_form"):
        username = st.text_input("Username/email")
        password = st.text_input("Password")
        submit = st.form_submit_button("Login")

        if submit:
            if username and password:
                token = validate_credentials(username, password)
                if token:
                    st.session_state.authenticated = True
                    st.session_state.credentials = {
                        "username": username,
                        "password": password,
                        "token": token,
                    }
                st.rerun()
            else:
                st.error("Invalid username or password")
        else:
            st.warning("Enter username/email and password")

    st.info("Chat login page")


def chat_page():
    with st.sidebar:
        st.markdown(f"Logged as {st.session_state.credentials['username']}")

    for message in st.session_state.chat_history[-5:]:
        with st.chat_message(message["role"]):
            if message["data"]:
                st.line_chart(message["data"])
            else:
                st.markdown(message["content"])

    if prompt := st.chat_input("Vulnerabilities chat"):
        answer = None
        st.session_state.chat_history.append(
            {"role": "user", "content": prompt, "data": None}
        )
        with st.chat_message("user"):
            st.markdown(prompt)

        with httpx.Client(timeout=30.0) as client:
            response = client.post(
                "http://backend:8000/prompt",
                json={"prompt": prompt},
                headers={"Auth": f"Bearer {st.session_state.credentials['token']}"},
            )

        if response.status_code != 200:
            st.error(f"Error: {response.status_code}")
        else:
            answer = response.json().get("content", "")

        if answer:
            st.session_state.chat_history.append(
                {"role": "assistant", "content": answer, "data": None}
            )
            with st.chat_message("assistant"):
                st.markdown(answer)


def main():
    st.set_page_config(page_title="AI chat", layout="centered")

    if st.session_state.authenticated:
        chat_page()
    else:
        login_page()


if __name__ == "__main__":
    main()
