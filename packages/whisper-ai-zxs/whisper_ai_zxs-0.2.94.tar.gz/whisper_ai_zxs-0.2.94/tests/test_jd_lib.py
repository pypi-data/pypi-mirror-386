from whisper_ai_zxs.jd_lib.jd_auth_client import JDAuthClient
from whisper_ai_zxs.jd_lib.jd_store_client import JDStoreClient

def test_get_access_token():
    client = JDAuthClient("B33F6D750B74FA81078EAEF88D8869BF", "4d38de2a68d14b41916b5e65de536831")
    # client.fetch_token_with_auth_code("your_auth_code")
    token = client.get_access_token()
    assert isinstance(token, str) and len(token) > 0, "Access token should be a non-empty string"
    print(f"Access Token: {token}")

def test_get_order_info():
    client = JDStoreClient()
    order_id = "1234567890"  # 替换为实际的订单ID
    try:
        order_info = client.getOrderInfo(order_id)
        assert isinstance(order_info, dict), "Order info should be a dictionary"
        print(f"Order Info: {order_info}")
    except Exception as e:
        print(f"Failed to get order info: {e}")

def test_getOrderNote():
    client = JDStoreClient()
    order_id = "340075181217"  # 替换为实际的订单ID
    try:
        order_notes = client.getOrderNote(order_id)
        assert isinstance(order_notes, dict), "Order notes should be a list"
        print(f"Order Notes: {order_notes}")
    except Exception as e:
        print(f"Failed to get order notes: {e}")

def test_addOrderNote():
    client = JDStoreClient()
    order_id = "340075181217"  # 替换为实际的订单ID
    note = "This is a test note2."
    try:
        response = client.addOrderNote(order_id, note)
        assert response.get("success") is True, "Adding order note should be successful"
        print(f"Add Order Note Response: {response}")
    except Exception as e:
        print(f"Failed to add order note: {e}")
        