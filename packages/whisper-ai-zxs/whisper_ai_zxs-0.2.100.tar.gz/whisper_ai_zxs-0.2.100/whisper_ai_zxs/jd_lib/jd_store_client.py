import requests
import logging
from datetime import datetime
import time
import json
import hashlib
from .jd_auth_client import JDAuthClient
from ..whisper_db import WhisperDB

class JDStoreClient:
    """
    京东开放平台客户端（轻量实现）
    说明：
    - 按照京东开放平台文档，使用 routerjson 接口，签名为 MD5(appSecret + key+value... + appSecret).upper()
    - 业务参数放到 360buy_param_json 字段（标准 JSON 字符串）
    - 如需 access_token，可传入 auth_client（需实现 get_access_token()）
    """

    COMMAND_URL = "https://api.jd.com/routerjson"
    #COMMAND_URL = "https://api-dev.jd.com/routerjson"

    def __init__(self):
        self.app_key = "B33F6D750B74FA81078EAEF88D8869BF"
        self.app_secret = "4d38de2a68d14b41916b5e65de536831"
        self.auth = JDAuthClient(self.app_key, self.app_secret)

    def _generate_sign(self, params: dict) -> str:
        """
        京东签名：把所有参数按 key 升序排列后拼接 key+value（value 使用原始字符串），
        最后在前后拼接 app_secret，MD5 后转大写
        """
        items = sorted(params.items(), key=lambda x: x[0])
        concat = "".join([f"{k}{v}" for k, v in items])
        raw = f"{self.app_secret}{concat}{self.app_secret}"
        return hashlib.md5(raw.encode("utf-8")).hexdigest().upper()

    def _post_request(self, method: str, method_params: dict = None, timeout: int = 10, retries: int = 2) -> dict:
        """
        统一构建京东请求并发送（POST form 表单）
        - method: 京东接口名，如 jingdong.pop.order.search
        - method_params: 业务参数 dict，会被 JSON 序列化到 360buy_param_json
        """
        if not method:
            raise RuntimeError("_post_request requires 'method' argument")

        # timestamp 格式 yyyy-MM-dd HH:mm:ss
        ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        sys_params = {
            "method": method,
            "app_key": self.app_key,
            "timestamp": ts,
            "v": "2.0",
            "format": "json",
        }

        # 如果有 auth 并返回 access_token，则包含
        if self.auth:
            try:
                access_token = self.auth.get_access_token()
            except Exception:
                access_token = None
            if access_token:
                sys_params["access_token"] = access_token

        # 业务参数放 360buy_param_json（要求为标准 JSON 字符串）
        if method_params:
            # 使用 separators 以避免不必要空白，value 不进行 urlencode
            biz = json.dumps(method_params, ensure_ascii=False, separators=(",", ":"))
            sys_params["360buy_param_json"] = biz

        # 计算签名，签名前参数均为原始 key/value（value 为字符串表示）
        sign = self._generate_sign({k: (v if isinstance(v, str) else str(v)) for k, v in sys_params.items()})
        sys_params["sign"] = sign

        headers = {"Content-Type": "application/x-www-form-urlencoded; charset=UTF-8"}

        attempt = 0
        backoff = 1
        while attempt <= retries:
            try:
                attempt += 1
                resp = requests.post(self.COMMAND_URL, data=sys_params, headers=headers, timeout=timeout)
                resp.raise_for_status()
                try:
                    return resp.json()
                except ValueError:
                    logging.error("Invalid JSON response: %s", resp.text)
                    return {"error": "invalid_json", "raw": resp.text}
            except requests.exceptions.RequestException as exc:
                logging.warning("POST attempt %d failed: %s", attempt, exc)
                if attempt <= retries:
                    time.sleep(backoff)
                    backoff *= 2
                    continue
                logging.error("All POST attempts failed: %s", exc)
                return {"error": "request_failed", "detail": str(exc)}

    def getOrderInfo(self, order_id: str) -> dict:
        """
        使用 jingdong.pop.order.search 按条件检索订单并返回简化结构。
        - 优先通过 orderId 精确匹配，兼容 tradeOrderId / parentOrderId 等候选字段。
        - 对返回字段做容错处理，适配 jingdong_pop_order_search_responce.searchorderinfo_result.orderInfoList 结构。
        """
        method = "jingdong.pop.order.search"
        # 推荐返回的字段（按文档示例与常用字段）
        optional_fields = "itemInfoList,orderId,pin,orderStartTime,scDT,orderState,consigneeInfo,sellerRemark"
        method_params = {
            "page": 1,
            "page_size": 50,
            "optional_fields": optional_fields,
            # 可以传入其它过滤条件，如 start_date/end_date/order_state 等
            # 如果仅查单个订单，传 orderId 作为筛选字段
            "orderId": order_id
        }

        logging.info("JD getOrderInfo (search) method=%s order_id=%s", method, order_id)
        body = self._post_request(method=method, method_params=method_params)
        if not body:
            return {"success": False, "message": "empty_response", "raw": body}

        # 通用错误判断
        if "error_response" in body:
            logging.error("JD API error: %s", body.get("error_response"))
            return {"success": False, "message": body.get("error_response")}

        # 尝试定位 order list（优先兼容官方示例结构）
        orders = []
        # 常见嵌套路径
        try:
            orders = (
                body.get("jingdong_pop_order_search_responce", {})
                    .get("searchorderinfo_result", {})
                    .get("orderInfoList", [])
            ) or orders
        except Exception:
            pass

        # 退化尝试：常见字段名
        if not orders:
            for key in ("orderInfoList", "order_list", "orders", "result", "data"):
                v = body.get(key)
                if isinstance(v, list):
                    orders = v
                    break
                # 有时 result -> { orderInfoList: [...] }
                if isinstance(v, dict):
                    for sub in ("orderInfoList", "orderList", "orderInfo"):
                        if sub in v and isinstance(v[sub], list):
                            orders = v[sub]
                            break
                    if orders:
                        break

        if not orders:
            # 如果响应本身就是单个订单对象
            if isinstance(body, dict) and any(k in body for k in ("orderId", "order_id", "orderState")):
                orders = [body]
            else:
                return {"success": False, "message": "order_not_found", "raw": body}

        # 在列表中查找匹配的订单
        matched = None
        for o in orders:
            # 支持多种 id 字段
            candidates = [
                str(o.get("orderId") or o.get("order_id") or o.get("orderIdStr") or ""),
                str(o.get("tradeOrderId") or ""),
                str(o.get("parentOrderId") or ""),
            ]
            if order_id in candidates or any(c == order_id for c in candidates):
                matched = o
                break
        # 如果没有精确匹配，尝试取第一条
        if not matched:
            matched = orders[0]

        order_info = matched if isinstance(matched, dict) else {}

        # 辅助：解析时间字段，兼容时间戳/字符串
        def _normalize_time(val):
            if not val:
                return None
            try:
                s = str(val)
                if s.isdigit():
                    # 支持秒或毫秒
                    ts = int(s)
                    if len(s) > 10:
                        ts = int(s[:10])
                    return datetime.fromtimestamp(ts).strftime("%Y-%m-%d %H:%M:%S")
                # 假设已经是格式化字符串
                return s
            except Exception:
                return val

        created_time = _normalize_time(order_info.get("orderStartTime") or order_info.get("created") or order_info.get("createdTime") or order_info.get("orderStartTime"))
        modified_time = _normalize_time(order_info.get("modified") or order_info.get("modifiedTime") or order_info.get("scDT"))

        # 状态映射（可扩展）
        status_map = {
            "WAIT_SELLER_STOCK_OUT": "待发货",
            "NOT_PAY": "未付款",
            "WAIT_GOODS_RECEIVE_CONFIRM": "待确认收货",
            "FINISHED_L": "已完成",
            "TRADE_CANCELED": "已关闭",
            "LOCKED": "已锁定",
            "PAUSE": "暂停",
            "DELIVERY_RETURN": "配送退货"
        }
        status_code = str(order_info.get("orderState") or order_info.get("order_state") or order_info.get("orderStateCode") or "")
        status_cn = status_map.get(status_code, status_code)

        # 解析收货人信息
        consignee = order_info.get("consigneeInfo") or order_info.get("consignee") or order_info.get("originalConsigneeInfo") or {}
        receiverCountryName = consignee.get("country") or consignee.get("countryName")
        receiverProvinceName = consignee.get("province") or consignee.get("provinceName")
        receiverCityName = consignee.get("city") or consignee.get("cityName")
        receiverDistrictName = consignee.get("county") or consignee.get("countyName")
        receiver_full = consignee.get("fullAddress") or consignee.get("address") or ""

        # 解析 sku 列表：优先 itemInfoList，其次 partialLogisticsInfoModel->skus 等
        raw_sku_list = order_info.get("itemInfoList") or order_info.get("itemInfo") or order_info.get("itemList") or []
        sku_items = []
        if isinstance(raw_sku_list, list) and raw_sku_list:
            for sku in raw_sku_list:
                if not isinstance(sku, dict):
                    continue
                sku_items.append({
                    "skuId": sku.get("skuId") or sku.get("sku_id") or sku.get("wareId") or sku.get("outerSkuId"),
                    "skuName": sku.get("skuName") or sku.get("sku_name") or sku.get("productName") or sku.get("title"),
                    "skuQuantity": sku.get("itemTotal") or sku.get("num") or sku.get("quantity") or sku.get("skuQuantity"),
                    "totalPaidAmount": sku.get("jdPrice") or sku.get("price") or sku.get("totalPaidAmount")
                })
        else:
            # 从 partialLogisticsInfoModel -> skus 提取
            pl = order_info.get("partialLogisticsInfoModel") or order_info.get("partialLogisticInfo") or []
            if isinstance(pl, list):
                for part in pl:
                    skus = part.get("skus") or []
                    for sku in skus:
                        sku_items.append({
                            "skuId": sku.get("skuId") or sku.get("sku_id") or sku.get("skuUuid"),
                            "skuName": sku.get("skuName") or sku.get("sku_name") or sku.get("skuTitle"),
                            "skuQuantity": sku.get("num") or sku.get("quantity"),
                            "totalPaidAmount": sku.get("price") or sku.get("totalPaidAmount")
                        })

        new_order_info = {
            "order_id": order_info.get("orderId") or order_info.get("order_id") or order_info.get("tradeOrderId") or "",
            "status": status_cn,
            "status_code": status_code,
            "created_time": created_time,
            "modified_time": modified_time,
            "receiverCountryName": receiverCountryName,
            "receiverProvinceName": receiverProvinceName,
            "receiverCityName": receiverCityName,
            "receiverDistrictName": receiverDistrictName,
            "receiver_full_address": receiver_full,
            "customerRemark": order_info.get("orderRemark") or order_info.get("customerRemark") or "",
            "sellerRemark": order_info.get("sellerRemark") or order_info.get("seller_remark") or "",
            "skuList": sku_items,
            "raw": order_info  # 保留原始订单对象以备进一步处理
        }

        return new_order_info

    def getOrderNote(self, order_id: str) -> dict:
        """
        查询订单备注（参考京东 vender_remark 查询接口返回结构）
        返回结构示例：
        {
            "success": True/False,
            "remark": "备注文本或None",
            "flag": "1",
            "created": "2023-11-23 00:00:00",
            "modified": "2023-11-23 00:00:00",
            "order_id": "6000300009",
            "raw": {...}  # 原始响应
        }
        """
        method = "jingdong.order.venderRemark.queryByOrderId"  # 按京东文档的接口名（示例）
        # 京东接口有时使用 order_id、orderId 等字段，这里使用下划线形式
        method_params = {"order_id": order_id}

        logging.info("JD getOrderNote method=%s order_id=%s", method, order_id)
        body = self._post_request(method=method, method_params=method_params)
        if not body:
            return {"success": False, "message": "empty_response", "raw": body}

        # 顶层错误结构判断
        if "error_response" in body:
            logging.error("JD API error: %s", body.get("error_response"))
            return {"success": False, "message": body.get("error_response"), "raw": body}
        if isinstance(body, dict) and body.get("code"):
            # 示例异常结构： { "code": "10100002", "errorMessage": "订单号不正确", ... }
            return {"success": False, "message": body.get("errorMessage") or body.get("message"), "code": body.get("code"), "raw": body}

        # 兼容官方示例结构：
        # jingdong_order_venderRemark_queryByOrderId_responce -> venderRemarkQueryResult -> vender_remark
        try:
            top = body.get("jingdong_order_venderRemark_queryByOrderId_responce", body)
            vrq = None
            if isinstance(top, dict):
                vrq = top.get("venderRemarkQueryResult") or top.get("vender_remark") or top
            else:
                vrq = body

            vender = None
            if isinstance(vrq, dict):
                # 优先取明确的 vender_remark 字段
                if "vender_remark" in vrq and isinstance(vrq["vender_remark"], dict):
                    vender = vrq["vender_remark"]
                else:
                    # 有时 vender_remark 在更深一层
                    possible = vrq.get("vender_remark") or vrq.get("venderRemark") or vrq.get("venderRemarkQueryResult")
                    if isinstance(possible, dict) and "remark" in possible:
                        vender = possible
                    else:
                        # 再尝试从 api_jos_result 外层搜索
                        for key in ("vender_remark", "venderRemark", "venderRemarkQueryResult"):
                            val = vrq.get(key)
                            if isinstance(val, dict) and "remark" in val:
                                vender = val
                                break

            # 如果没有找到具体字段，尝试在整个响应中搜索 vender_remark
            if vender is None:
                if isinstance(body, dict) and "vender_remark" in body and isinstance(body["vender_remark"], dict):
                    vender = body["vender_remark"]

            # 最终返回解析结果
            if isinstance(vender, dict):
                return {
                    "success": True,
                    "remark": vender.get("remark"),
                    "flag": vender.get("flag"),
                    "created": vender.get("created"),
                    "modified": vender.get("modified"),
                    "order_id": vender.get("order_id"),
                    "raw": body
                }

            # 如果响应中明确存在但为 null / 空，则返回成功但 remark 为 None
            # 例如：vender_remark 为 null 时，说明没有备注
            # 检查路径是否存在但为 None
            # 先尝试判断示例路径存在于响应
            if "jingdong_order_venderRemark_queryByOrderId_responce" in body:
                inner = body["jingdong_order_venderRemark_queryByOrderId_responce"].get("venderRemarkQueryResult", {})
                if "vender_remark" in inner and inner["vender_remark"] is None:
                    return {"success": True, "remark": None, "raw": body}

            # 未能解析到备注字段，返回原始响应以便诊断
            return {"success": False, "message": "remark_not_found", "raw": body}
        except Exception as e:
            logging.exception("Failed to parse vender_remark for order_id=%s: %s", order_id, e)
            return {"success": False, "message": "parse_error", "detail": str(e), "raw": body}

    def addOrderNote(self, order_id: str, note: str, flag: int = 1) -> dict:
        """
        使用 jingdong.pop.order.modifyVenderRemark 添加/修改/删除商家备注
        - 在添加备注时先读取原有备注，追加新备注并带上时间戳
        - order_id: 京东订单号（可传字符串或数字）
        - note: 备注文本，传空字符串则尝试删除已有备注（根据京东文档）
        - flag: 颜色标识枚举 0..5，默认 0（GRAY）
        返回：{"success": bool, ... , "raw": body}
        """
        # 参数校验
        try:
            oid = int(order_id)
            if oid <= 0:
                return {"success": False, "message": "invalid_order_id"}
        except Exception:
            return {"success": False, "message": "invalid_order_id"}

        try:
            flag = int(flag)
        except Exception:
            return {"success": False, "message": "invalid_flag"}
        if flag not in (0, 1, 2, 3, 4, 5):
            return {"success": False, "message": "invalid_flag", "code": "10100040"}

        if note is None:
            note = ""

        # 不支持删除备注；仅追加非空备注
        if note == "":
            return {"success": False, "message": "empty_note_not_allowed"}

        # 限制单次新备注长度（京东提示不超过500字符），但最终组合也需 <=500
        if len(note) > 500:
            return {"success": False, "message": "remark_too_long", "code": "10100039"}

        # 先尝试读取原有备注
        try:
            existing_resp = self.getOrderNote(str(order_id))
            existing_remark = None
            if isinstance(existing_resp, dict) and existing_resp.get("success"):
                existing_remark = existing_resp.get("remark")
            # 如果 getOrderNote 返回成功但 remark 字段缺失， treat as None
        except Exception as e:
            logging.warning("Failed to fetch existing remark for order_id=%s: %s", order_id, e)
            existing_remark = None

        # 组装带时间戳的新备注
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        stamp = f"[{now}] "
        if existing_remark:
            combined = f"{existing_remark}\n{stamp}{note}"
        else:
            combined = f"{stamp}{note}"

        # 如果合并后超长，尝试截断 existing_remark 以保留最新内容
        if len(combined) > 500:
            # 可用给 existing 留下的长度（考虑换行符）
            extra = len(stamp) + len(note) + (1 if existing_remark else 0)
            max_existing = 500 - extra
            if max_existing < 0:
                # 新增 note 本身太长（已经在上面检查过），但为保险起见返回错误
                return {"success": False, "message": "combined_remark_too_long", "code": "10100039"}
            trimmed_existing = (existing_remark or "")[:max_existing]
            if trimmed_existing:
                combined = f"{trimmed_existing}\n{stamp}{note}"
            else:
                combined = f"{stamp}{note}"
            # 最终仍确保长度不超
            combined = combined[:500]

        method = "jingdong.pop.order.modifyVenderRemark"
        method_params = {
            "order_id": oid,
            "flag": flag,
            "remark": combined
        }

        logging.info("JD modifyVenderRemark method=%s order_id=%s flag=%s len_combined=%d", method, oid, flag, len(combined))
        body = self._post_request(method=method, method_params=method_params)
        if not body:
            return {"success": False, "message": "empty_response", "raw": body}

        # 顶层错误判断
        if "error_response" in body:
            logging.error("JD API error: %s", body.get("error_response"))
            return {"success": False, "message": body.get("error_response"), "raw": body}
        if isinstance(body, dict) and body.get("code"):
            return {"success": False, "message": body.get("errorMessage") or body.get("message"), "code": body.get("code"), "raw": body}

        # 解析响应结构：jingdong_pop_order_modifyVenderRemark_responce -> modifyvenderremark_result
        try:
            top = body.get("jingdong_pop_order_modifyVenderRemark_responce", body)
            result = None
            if isinstance(top, dict):
                result = top.get("modifyvenderremark_result") or top.get("modifyVenderRemarkResult") or top
            else:
                result = body

            if isinstance(result, dict):
                success_val = result.get("success")
                success = False
                if isinstance(success_val, bool):
                    success = success_val
                elif success_val is not None:
                    success = str(success_val).lower() == "true"

                return {
                    "success": bool(success),
                    "chinese_err_code": result.get("chinese_err_code"),
                    "error_code": result.get("error_code"),
                    "english_err_code": result.get("english_err_code"),
                    "out_batch_id": result.get("out_batch_id"),
                    "sendbatch_id": result.get("sendbatch_id"),
                    "raw": body
                }

            return {"success": False, "message": "unexpected_response_format", "raw": body}
        except Exception as e:
            logging.exception("Failed to parse modifyVenderRemark response for order_id=%s: %s", order_id, e)
            return {"success": False, "message": "parse_error", "detail": str(e), "raw": body}

    def collectSellingProduct(self, shop_name: str):
        """
        获取商品并写入本地数据库（示例）
        说明：JD 商品查询接口与参数名与小红书不同，这里示例化为调用 _getProductList 并写库
        """
        product_list = self._getProductList()
        grouped_products = {}
        for product in product_list:
            item = product.get("item") or product.get("product") or product
            product_id = item.get("id") or item.get("skuId") or item.get("product_id")
            product_name = item.get("name") or item.get("title")
            sku = product.get("sku") or item.get("sku") or {}
            sku_name = sku.get("name") or sku.get("sku_name") or ""
            stock = sku.get("stock") or sku.get("quantity") or 0

            key = (product_id, product_name)
            if key not in grouped_products:
                grouped_products[key] = {"product_id": product_id, "product_name": product_name, "sell": [], "unsell": []}
            if stock and int(stock) > 0:
                grouped_products[key]["sell"].append(sku_name)
            else:
                grouped_products[key]["unsell"].append(sku_name)

        new_product_list = list(grouped_products.values())

        sql_use = "USE zxs_order;"
        sql_del = f"DELETE FROM `tm_selling_product` WHERE `shop_name` =%s"

        with WhisperDB() as myDB:
            myDB.query(sql_use)
            myDB.query(sql_del, (shop_name,))
            for product in new_product_list:
                product_id = product["product_id"]
                product_name = product["product_name"]
                sell_json = json.dumps(product["sell"], ensure_ascii=False)
                unsell_json = json.dumps(product["unsell"], ensure_ascii=False)
                sql_insert = (
                    "INSERT INTO tm_selling_product "
                    "(product_code, product_name, on_sale_sku, off_sale_sku, shop_name, discount_plan, purchase_link) "
                    "VALUES (%s, %s, %s, %s, %s, '', '')"
                )
                myDB.query(sql_insert, (product_name, product_name, sell_json, unsell_json, shop_name))
            myDB.commit()

    def _getProductList(self) -> list:
        """
        获取商品列表（示例使用 jingdong.pop.product.search 占位）
        返回格式尽量与之前保持兼容：列表中包含 item/sku 子结构
        """
        method = "jingdong.pop.product.search"  # 占位，按真实接口修改
        method_params = {
            "page": 1,
            "page_size": 100
        }

        all_products = []
        while True:
            logging.info("Fetching JD products page %s", method_params.get("page"))
            body = self._post_request(method=method, method_params=method_params)
            if not body:
                logging.error("Empty response when fetching products")
                break
            if "error_response" in body:
                logging.error("JD API error when fetching products: %s", body.get("error_response"))
                break

            # 常见返回结构尝试解析
            datas = None
            for key in ("queryResult", "result", "products", "data"):
                if key in body:
                    datas = body[key]
                    break
            if datas is None:
                # 退回至 body 本体，如果是 list 则直接使用
                if isinstance(body, list):
                    datas = body
                else:
                    datas = []

            # 如果 datas 是 dict 包含 list 列表字段（如 items）
            if isinstance(datas, dict):
                for candidate in ("items", "itemList", "data"):
                    if candidate in datas and isinstance(datas[candidate], list):
                        page_list = datas[candidate]
                        break
                else:
                    # 找不到具体列表，尝试将 dict 转为单元素列表
                    page_list = [datas]
            else:
                page_list = datas

            all_products.extend(page_list)

            # 翻页判断：尝试读取 total 或使用 page_size 长度
            total = None
            if isinstance(datas, dict):
                total = datas.get("total") or datas.get("total_count")
            page_size = method_params.get("page_size", 100)
            if not page_list or (total is not None and len(all_products) >= int(total)):
                break
            method_params["page"] = method_params.get("page", 1) + 1

        logging.info("Total products fetched: %d", len(all_products))
        return all_products
