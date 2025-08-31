import json
import os
import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
from config import SAMPLE_QUERY_1, SAMPLE_QUERY_2, SAMPLE_QUERY_3
from vizql import execute_vizql_query

def render_auth_sidebar(auth_callback):
    with st.sidebar:
        st.header("認証設定")
        
        with st.form("auth_form"):
            secret_id = st.text_input(
                "Secret ID", 
                value=os.getenv("TABLEAU_SECRET_ID", ""),
                type="password",
                help="シークレットID"
            )
            secret_value = st.text_input(
                "Secret Value", 
                value=os.getenv("TABLEAU_SECRET_VALUE", ""),
                type="password",
                help="シークレット値"
            )
            client_id = st.text_input(
                "Client ID",
                value=os.getenv("TABLEAU_CLIENT_ID", ""),
                help="クライアントID"
            )
            username = st.text_input(
                "Username",
                value=os.getenv("TABLEAU_USERNAME", ""),
                help="ユーザー名"
            )
            embed_url = st.text_input(
                "Embed URL", 
                value=os.getenv("TABLEAU_EMBED_URL", ""),
                help="埋め込みURL"
            )
            site_name = st.text_input(
                "サイト名", 
                value=os.getenv("TABLEAU_SITE_NAME", ""),
                help="Tableau サイト名"
            )
            datasource_luid = st.text_input(
                "データソースLUID",
                value=os.getenv("TABLEAU_DATASOURCE_LUID", ""),
                help="VDSクエリ対象のデータソースLUID"
            )
            
            submit_auth = st.form_submit_button("認証情報を設定")
            
            if submit_auth:
                auth_callback({
                    'secret_id': secret_id,
                    'secret_value': secret_value,
                    'client_id': client_id,
                    'username': username,
                    'embed_url': embed_url,
                    'site_name': site_name,
                    'datasource_luid': datasource_luid
                })

def render_tableau_web_authoring():
    st.header("Tableau Web Authoring")
    
    if "jwt_token" in st.session_state and "embed_url" in st.session_state:
        embed_html = f"""
        <script 
            type='module' src='{st.session_state.server_url}/javascripts/api/tableau.embedding.3.latest.min.js'>
        </script>
        <tableau-authoring-viz
            id='tableau-viz' 
            src='{st.session_state.embed_url}'
            token='{st.session_state.jwt_token}'
            width='100%' height='800' hide-tabs toolbar='bottom' >
        </tableau-authoring-viz>
        """
        
        components.html(embed_html, height=850)
    else:
        st.info("🔐 サイドバーで認証情報を設定するとTableau Web Authoringが表示されます")

def render_vizql_query_interface():
    st.header("VizQL Data Service")
    
    if "jwt_token" not in st.session_state:
        st.info("🔐 まずサイドバーで認証情報を設定してください")
        return
    
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.subheader("クエリ入力")
        _render_sample_queries()
        _render_query_form()
    
    with col2:
        st.subheader("実行結果")
        _render_query_results()

def _render_sample_queries():
    with st.expander("📋 サンプルクエリ", expanded=False):
        sample_options = {
            "📊 売上集計": SAMPLE_QUERY_1,
            "📅 2024年売上集計（期間フィルタ）": SAMPLE_QUERY_2,
            "📈 2024年カテゴリ別利益率集計（計算フィールド）": SAMPLE_QUERY_3
        }
        selected_sample = st.selectbox(
            "サンプルクエリを選択",
            options=list(sample_options.keys()),
            key="sample_selector"
        )
        
        col_preview, col_insert = st.columns([3, 1])
        
        with col_preview:
            if st.button("📋 プレビュー", key="preview_sample", use_container_width=True):
                st.session_state.preview_query = json.dumps(
                    sample_options[selected_sample], 
                    ensure_ascii=False, 
                    indent=2
                )
        
        with col_insert:
            if st.button("➕ 挿入", key="insert_sample", use_container_width=True):
                st.session_state.sample_query = json.dumps(
                    sample_options[selected_sample], 
                    ensure_ascii=False, 
                    indent=2
                )
                st.success("クエリを挿入しました！")
        
        if "preview_query" in st.session_state:
            st.subheader("プレビュー")
            st.code(st.session_state.preview_query, language="json")

def _render_query_form():
    with st.form("vizql_form"):
        query = st.text_area(
            "VizQLクエリ", 
            height=150, 
            placeholder="VizQLクエリを入力してください",
            value=st.session_state.get("sample_query", "")
        )
        
        submit_query = st.form_submit_button("クエリ実行")
        
        if submit_query:
            if not query.strip():
                st.warning("⚠️ クエリが空です。VizQLクエリを入力してください。")
            else:
                if isinstance(query, str):
                    try:
                        parsed_query = json.loads(query)
                        if not isinstance(parsed_query, dict):
                            st.error("❌ クエリは辞書形式である必要があります。")
                        else:
                            query = parsed_query
                    except json.JSONDecodeError as e:
                        st.error(f"❌ JSONフォーマットエラー: {str(e)}")
                    except Exception as e:
                        st.error(f"❌ クエリ解析エラー: {str(e)}")
            
            with st.spinner("VizQLクエリを実行中..."):
                result = execute_vizql_query(
                    st.session_state.server_url,
                    st.session_state.credentials_token,
                    st.session_state.datasource_luid,
                    query
                )
                
                st.session_state.vizql_result = result
                
                if result["success"]:
                    st.success("✅ クエリが正常に実行されました！")
                else:
                    st.error(f"❌ エラーが発生しました: {result['error']}")

def _render_query_results():
    if "vizql_result" not in st.session_state:
        st.info("🔍 VizQLクエリを実行すると結果がここに表示されます")
        return
    
    result = st.session_state.vizql_result
    
    if result["success"]:
        data = result["data"]
        
        if "queryResult" in data and "data" in data["queryResult"]:
            rows = data["queryResult"]["data"]
            st.info(f"📊 取得件数: {len(rows)}件")
        
        with st.expander("📄 JSON結果（生データ）", expanded=False):
            st.json(data)
        
        if "queryResult" in data and "data" in data["queryResult"]:
            st.subheader("📊 結果データ")
            try:
                df = pd.DataFrame(data["queryResult"]["data"])
                st.dataframe(df, use_container_width=True)
            except Exception:
                st.json(data["queryResult"]["data"])
    else:
        st.error(f"❌ 実行エラー: {result['error']}")