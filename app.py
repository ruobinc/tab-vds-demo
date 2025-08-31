import json
import streamlit as st
import datetime
import uuid
import jwt
import requests
import os
from dotenv import load_dotenv
import streamlit.components.v1 as components

load_dotenv()

SAMPLE_QUERY_1 = {
    "fields": [{"fieldCaption": "売上", "function": "SUM", "maxDecimalPlaces": 2}]
}

SAMPLE_QUERY_2 = {
    "fields": [{"fieldCaption": "売上", "function": "SUM", "maxDecimalPlaces": 2}],
    "filters": [
        {
            "field": {"fieldCaption": "オーダー日"},
            "filterType": "QUANTITATIVE_DATE",
            "quantitativeFilterType": "RANGE",
            "minDate": "2024-01-01",
            "maxDate": "2024-12-31",
        }
    ],
}

SAMPLE_QUERY_3 = {
    "fields": [
      { "fieldCaption": "カテゴリ", "sortPriority": 1 },
      { "fieldCaption": "売上", "function": "SUM", "fieldAlias": "Sales" },
      { "fieldCaption": "利益", "function": "SUM", "fieldAlias": "Profit" },
      {
        "fieldCaption": "Profit Margin",
        "calculation": "SUM([利益]) / SUM([売上])",
        "maxDecimalPlaces": 4,
        "sortPriority": 2,
        "sortDirection": "DESC"
      }
    ],
    "filters": [
      {
        "filterType": "DATE",
        "field": { "fieldCaption": "オーダー日" },
        "periodType": "MONTHS",
        "dateRangeType": "NEXTN",
        "rangeN": 12,
        "anchorDate": "2024-04-01"
      }
    ]
  }

def generate_jwt_token(secret_id, secret_value, client_id, username, token_expiry_minutes=1):
    """
    Generate JWT token for Tableau Connected App authentication
    """
    scopes = [
        "tableau:views:embed",
        "tableau:views:embed_authoring",
        "tableau:insights:embed",
        "tableau:viz_data_service:read",
    ]
    
    exp = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(minutes=token_expiry_minutes)
    
    payload = {
        "iss": client_id,
        "exp": exp,
        "jti": str(uuid.uuid4()),
        "aud": "tableau",
        "sub": username,
        "scp": scopes,
    }
    
    token = jwt.encode(
        payload,
        secret_value,
        algorithm="HS256",
        headers={
            "kid": secret_id,
            "iss": client_id,
        },
    )
    
    return token

def signin_with_jwt(server, jwt_token, site_content_url, api_version="3.26"):
    url = f"{server}/api/{api_version}/auth/signin"
    headers = {"Content-Type": "application/xml", "Accept": "application/json"}
    body = f"""
<tsRequest>
<credentials jwt="{jwt_token}">
    <site contentUrl="{site_content_url}"/>
</credentials>
</tsRequest>
""".strip()
    r = requests.post(url, headers=headers, data=body)
    r.raise_for_status()
    return r.json()["credentials"]["token"]

def extract_server_url(embed_url):
    """
    Embed URLからServer URLを抽出
    例: https://prod-apnortheast-a.online.tableau.com/t/xxx/... 
    → https://prod-apnortheast-a.online.tableau.com
    """
    if "/t/" in embed_url:
        return embed_url.split("/t/")[0]
    else:
        # /t/ がない場合はドメイン部分まで抽出
        from urllib.parse import urlparse
        parsed = urlparse(embed_url)
        return f"{parsed.scheme}://{parsed.netloc}"

def execute_vizql_query(server_url, jwt_token, datasource_luid, query):
    """
    Execute VizQL query against Tableau VizQL Data Service
    """
    try:

        
        vizql_url = f"{server_url}/api/v1/vizql-data-service/query-datasource"
        
        headers = {
            "X-Tableau-Auth": jwt_token,
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        
        # VizQLクエリのペイロード
        payload = {
            "datasource": { "datasourceLuid": datasource_luid },
            "query": query
        }
        
        response = requests.post(vizql_url, headers=headers, json=payload, timeout=30)
        
        if response.status_code == 200:
            return {"success": True, "data": response.json()}
        else:
            return {
                "success": False, 
                "error": f"HTTP {response.status_code}: {response.text}"
            }
            
    except requests.RequestException as e:
        return {"success": False, "error": f"接続エラー: {str(e)}"}
    except Exception as e:
        return {"success": False, "error": f"実行エラー: {str(e)}"}

def main():
    st.set_page_config(
        page_title="Tableau Web Authoring & VizQL Data Service Demo",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    st.title("Tableau Web Authoring & VizQL Data Service Demo")
    
    # サイドバー：認証設定
    with st.sidebar:
        st.header("認証設定")
        
        # 認証情報入力フォーム
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
            
            if submit_auth and all([secret_id, secret_value, client_id, username, embed_url, site_name, datasource_luid]):
                try:
                    token = generate_jwt_token(secret_id, secret_value, client_id, username)
                    st.session_state.jwt_token = token
                    st.session_state.embed_url = embed_url
                    st.session_state.server_url = extract_server_url(embed_url)
                    st.session_state.site_name = site_name
                    st.session_state.datasource_luid = datasource_luid
                    st.session_state.credentials_token = signin_with_jwt(st.session_state.server_url, token, site_name)
                    st.success("✅ 認証情報が設定されました！")
                except Exception as e:
                    st.error(f"❌ JWT生成エラー: {str(e)}")
    
    # メインコンテンツをタブで分割
    tab1, tab2 = st.tabs(["Tableau Web Authoring", "VizQL Data Service"])
    
    with tab1:
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
    
    with tab2:
        st.header("VizQL Data Service")
        
        if "jwt_token" in st.session_state:
            # 左右分割でクエリ入力と結果を配置
            col1, col2 = st.columns([1, 1])
            
            with col1:
                st.subheader("クエリ入力")
                # サンプルクエリ選択
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
                            # queryがstring形式の場合はdictに変換
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
            
            with col2:
                st.subheader("実行結果")
                
                if "vizql_result" in st.session_state:
                    result = st.session_state.vizql_result
                    
                    if result["success"]:
                        data = result["data"]
                        
                        # 結果の概要を表示
                        if "queryResult" in data and "data" in data["queryResult"]:
                            rows = data["queryResult"]["data"]
                            st.info(f"📊 取得件数: {len(rows)}件")
                        
                        # JSONの表示
                        with st.expander("📄 JSON結果（生データ）", expanded=False):
                            st.json(data)
                        
                        # 表形式での表示（可能な場合）
                        if "queryResult" in data and "data" in data["queryResult"]:
                            st.subheader("📊 結果データ")
                            try:
                                import pandas as pd
                                df = pd.DataFrame(data["queryResult"]["data"])
                                st.dataframe(df, use_container_width=True)
                            except Exception:
                                st.json(data["queryResult"]["data"])
                    else:
                        st.error(f"❌ 実行エラー: {result['error']}")
                else:
                    st.info("🔍 VizQLクエリを実行すると結果がここに表示されます")
        else:
            st.info("🔐 まずサイドバーで認証情報を設定してください")

if __name__ == "__main__":
    main()