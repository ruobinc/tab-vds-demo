import requests

def execute_vizql_query(server_url, jwt_token, datasource_luid, query):
    try:
        vizql_url = f"{server_url}/api/v1/vizql-data-service/query-datasource"
        
        headers = {
            "X-Tableau-Auth": jwt_token,
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        
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