from langchain_core.tools import BaseTool
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
import requests
import json
import hashlib
import time
import os
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

class GoodsQueryInput(BaseModel):
    keyword: str = Field(
        ...,
        description="衣物搜索关键词，如：连衣裙、男士衬衫、运动鞋等"
    )
    page_index: Optional[int] = Field(
        default=1,
        description="页码，默认第1页"
    )
    page_size: Optional[int] = Field(
        default=5,
        description="返回商品数量，默认5条"
    )
    max_price: Optional[float] = Field(
        default=None,
        description="最高价格限制"
    )
    min_price: Optional[float] = Field(
        default=None,
        description="最低价格限制"
    )
    sort_by: Optional[str] = Field(
        default="inOrderCount30Days",
        description="排序方式: price(价格), commissionShare(佣金比例), inOrderCount30Days(销量)"
    )
    sort_order: Optional[str] = Field(
        default="desc",
        description="排序方向: asc(升序), desc(降序)"
    )
    has_coupon: Optional[bool] = Field(
        default=False,
        description="是否只显示有优惠券的商品"
    )

class JdUnionGoodsQueryTool(BaseTool):
    name: Optional[str] = "jd_clothing_search"
    description:Optional[str] = "搜索京东衣物商品及优惠券信息，用于服装推荐"
    args_schema: Optional[type] = GoodsQueryInput 
    
    url: str = "https://api.jd.com/routerjson"
    app_key: Optional[str] = None
    app_secret: Optional[str] = None
    
    
    def __init__(self):
        super().__init__()
        self.app_key = os.getenv("JD_APP_KEY")
        self.app_secret = os.getenv("JD_APP_SECRET")
        
        if not self.app_key or not self.app_secret:
            raise ValueError("请设置JD_APP_KEY和JD_APP_SECRET环境变量")

    # def _generate_sign(self, params: Dict[str, str]) -> str:
    #     """生成API签名"""
    #     sorted_params = sorted(params.items(), key=lambda x: x[0])
    #     concatenated = self.app_secret + ''.join(
    #         f"{k}{v}" for k, v in sorted_params
    #     ) + self.app_secret
    #     return hashlib.md5(concatenated.encode('utf-8')).hexdigest().upper()
    def _generate_sign(self, params: Dict[str, str]) -> str:
        """
        生成API签名 - 按照京东联盟要求
        签名规则:
        1. 将所有参数按字母顺序排序
        2. 将参数名和参数值直接拼接(不加等号等连接符)
        3. 在拼接后的字符串两端加上app_secret
        4. 对最终字符串进行MD5加密并转为大写
        """
       
        
        # 按字母顺序排序参数
        sorted_params = sorted(params.items(), key=lambda x: x[0])
        
        # 直接拼接参数名和参数值(不含连接符)
        param_str = ''.join(f"{k}{v}" for k, v in sorted_params)
        
        # 在两端加上app_secret
        sign_str = f"{self.app_secret}{param_str}{self.app_secret}"
        
        # MD5加密并转为大写
        return hashlib.md5(sign_str.encode('utf-8')).hexdigest().upper()

    def _run(self, keyword: str, **kwargs: Any) -> Dict[str, Any]:
        """执行商品查询"""
        # 设置默认值
        page_index = kwargs.get("page_index", 1)
        page_size = kwargs.get("page_size", 2)
        has_coupon = 1 if kwargs.get("has_coupon", True) else 0
        sort_by = kwargs.get("sort_by", "inOrderCount30Days")
        sort_order = kwargs.get("sort_order", "desc")
        
        # 构建业务参数
        goods_req = {
            "keyword": keyword,
            "pageIndex": page_index,
            "pageSize": page_size,
            "isCoupon": has_coupon,
            "sortName": sort_by,
            "sort": sort_order
        }
        
        # 添加价格筛选
        if kwargs.get("min_price") is not None:
            goods_req["pricefrom"] = kwargs["min_price"]
        if kwargs.get("max_price") is not None:
            goods_req["priceto"] = kwargs["max_price"]
        
        # 公共参数
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        public_params = {
            "method": "jd.union.open.goods.query",
            "app_key": self.app_key,
            "timestamp": timestamp,
            "format": "json",
            "v": "1.0",
            "sign_method": "md5",
            "360buy_param_json": json.dumps({"goodsReqDTO": goods_req})
        }
        
        # 生成签名
        sign = self._generate_sign(public_params)
        public_params["sign"] = sign
        
        # 发送请求
        try:
            response = requests.get(self.url, params=public_params)
            response.raise_for_status()
            result = response.json()
            
            
            if "error_response" in result:
                error_msg = result["error_response"].get("zh_desc", "未知错误")
                return {"error": f"京东API错误: {error_msg}"}
            
            # 提取商品列表
            response_key = "jd_union_open_goods_query_responce"  
            if response_key not in result:
                response_key = "jd_union_open_goods_query_response" 
                
            goods_data = result.get(response_key, {})
            query_result = goods_data.get("queryResult", "")
            
          
            try:
                query_result_json = json.loads(query_result)
                goods_list = query_result_json.get("data", [])
            except:
                return {"error": "解析商品数据失败"}
            
          
            simplified_goods = []
            for item in goods_list:
               
                good_item = {
                    "name": item.get("skuName", ""),
                    "price": item.get("priceInfo", {}).get("price", 0),
                    "coupon_price": item.get("priceInfo", {}).get("lowestCouponPrice", 0),
                    "good_comments_share": item.get("goodCommentsShare", 0),
                    "image": item.get("imageInfo", {}).get("imageList", [{}])[0].get("url", ""),
                    "shop_name": item.get("shopInfo", {}).get("shopName", ""),
                    "description": item.get("document", ""), 
                    "stock_state": item.get("stockState", ""),  
                 
                    "material_url": item.get("materialUrl", ""),  
                    "item_url": f"https://item.jd.com/{item.get('skuId', '')}.html" if item.get('skuId') else "",
                    "sales": item.get("inOrderCount30Days", 0)
                }
                simplified_goods.append(good_item)
            
            return {"goods": simplified_goods}
        except Exception as e:
            return {"error": f"请求失败: {str(e)}"}

# 使用示例
if __name__ == "__main__":
    os.getcwd
    os.chdir("d:/desktop/giteeclone/fashion-agent")
    print("当前工作目录:", os.getcwd())
    # 设置环境变量
    os.environ["JD_APP_KEY"] = os.getenv("JD_APP_KEY")
    os.environ["JD_APP_SECRET"] = os.getenv("JD_APP_SECRET")

    tool = JdUnionGoodsQueryTool()
    tool_input = {
        "keyword": "连衣裙",
        "max_price": 200,
        "page_size": 2,
    }
    
    result = tool.run(tool_input)
    print(json.dumps(result, indent=2, ensure_ascii=False))