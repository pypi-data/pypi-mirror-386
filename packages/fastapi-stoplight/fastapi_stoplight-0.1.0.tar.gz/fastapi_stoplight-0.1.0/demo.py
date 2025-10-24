'''
Description: 
Author: 月间
Date: 2025-08-04 23:47:52
LastEditTime: 2025-08-05 00:17:08
LastEditors:  
'''
# @Version        : 1.0
# @Update Time    : 2025/8/4 23:47
# @File           : demo.py
# @IDE            : PyCharm
# @Desc           : 文件描述信息
from fastapi import FastAPI, Request, UploadFile, File
from pydantic import BaseModel, Field

from fastapi_stoplight import get_stoplight_elements_html


app = FastAPI(
    description="""# 用户服务API

这是一个基于FastAPI构建的用户服务API，提供完整的用户管理功能。

## 功能特点
- 用户信息的创建、查询、更新和删除
- 支持用户列表查询
- 输入数据验证和错误处理
- 自动生成交互式API文档

## 使用说明
1. 创建用户：发送POST请求到`/create`
2. 查询用户列表：发送GET请求到`/list`
3. 更新用户：发送PUT请求到`/update/{pk}`
4. 删除用户：发送DELETE请求到`/delete/{pk}`

## 示例
```python
# 创建用户示例
{
  "name": "张三",
  "age": 18
}
```

联系我们: zhangsan@example.com""",
    version="1.0.0",
    title="用户服务API",
    contact={
        "name": "张三",
        "email": "zhangsan@example.com",
    }
)


class User(BaseModel):
    name: str = Field(..., description="用户名")
    age: int = Field(..., description="年龄")

@app.get("/index/{pk}", summary="首页")
def read_root(pk: str):
    return {"Hello": pk}


@app.get("/list", summary="用户列表", response_model=list[User])
def list_users():
    return [
        {"id": 1, "name": "张三", "age": 18},
        {"id": 2, "name": "李四", "age": 19},
        {"id": 3, "name": "王五", "age": 20},
    ]

@app.put("/update/{pk}", summary="更新用户信息", response_model=User)
def update_user(pk: int, user: User):
    return user

@app.post("/create", summary="创建用户", response_model=User)
def create_user(user: User):
    return user

@app.delete("/delete/{pk}", summary="删除用户")
def delete_user(pk: int):
    return {"id": pk}

@app.post("/upload", summary="上传文件")
async def upload_file(file: UploadFile = File(...)):
    return {"filename": file.filename}
@app.get("/stoplight", include_in_schema= False)
def stoplight(request: Request):
    return get_stoplight_elements_html(openapi_url=request.app.openapi_url, title="用户服务API")

if __name__ == '__main__':
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8005)

