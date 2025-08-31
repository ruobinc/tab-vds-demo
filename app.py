import streamlit as st
from dotenv import load_dotenv

from auth import generate_jwt_token, signin_with_jwt, extract_server_url
from ui_components import render_auth_sidebar, render_tableau_web_authoring, render_vizql_query_interface

load_dotenv()

def handle_auth_submit(auth_data):
    if all(auth_data.values()):
        try:
            token = generate_jwt_token(
                auth_data['secret_id'], 
                auth_data['secret_value'], 
                auth_data['client_id'], 
                auth_data['username']
            )
            st.session_state.jwt_token = token
            st.session_state.embed_url = auth_data['embed_url']
            st.session_state.server_url = extract_server_url(auth_data['embed_url'])
            st.session_state.site_name = auth_data['site_name']
            st.session_state.datasource_luid = auth_data['datasource_luid']
            st.session_state.credentials_token = signin_with_jwt(
                st.session_state.server_url, token, auth_data['site_name']
            )
            
            for key, value in auth_data.items():
                st.session_state[key] = value
                
            st.success("✅ 認証情報が設定されました！")
        except Exception as e:
            st.error(f"❌ JWT生成エラー: {str(e)}")

def main():
    st.set_page_config(
        page_title="VizQL Data Service Demo",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    st.title("VizQL Data Service Demo")
    
    render_auth_sidebar(handle_auth_submit)
    
    tab1, tab2 = st.tabs(["Tableau Web Authoring", "VizQL Data Service"])
    
    with tab1:
        render_tableau_web_authoring()
    
    with tab2:
        render_vizql_query_interface()

if __name__ == "__main__":
    main()