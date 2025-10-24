'''
Author: 823042332@qq.com 823042332@qq.com
Date: 2025-08-28 09:07:54
LastEditors: 823042332@qq.com 823042332@qq.com
LastEditTime: 2025-08-28 09:30:32
FilePath: /pro_craft/src/pro_craft/unit.py
Description: 这是默认设置,请设置`customMade`, 打开koroFileHeader查看配置 进行设置: https://github.com/OBKoro1/koro1FileHeader/wiki/%E9%85%8D%E7%BD%AE
'''
import re
import inspect
import importlib
import yaml
import zlib
from volcenginesdkarkruntime import Ark
import os

from contextlib import contextmanager
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine # 异步核心
from contextlib import asynccontextmanager # 注意这里是 asynccontextmanager


def extract_(text: str, pattern_key = r"json",multi = False):
    pattern = r"```"+ pattern_key + r"([\s\S]*?)```"
    matches = re.findall(pattern, text)
    if multi:
        [match.strip() for match in matches]
        if matches:
            return [match.strip() for match in matches]    
        else:
            return ""  # 返回空字符串或抛出异常，此处返回空字符串
    else:
        if matches:
            return matches[0].strip()  # 添加strip()去除首尾空白符
        else:
            return ""  # 返回空字符串或抛出异常，此处返回空字符串


def extract_from_loaded_objects(obj_list):
    results = []
    for obj in obj_list:
        if inspect.isclass(obj):
            class_info = {
                "type": "class",
                "name": obj.__name__,
                "docstring": inspect.getdoc(obj),
                "signature": f"class {obj.__name__}{inspect.getclasstree([obj], unique=True)[0][0].__bases__}:" if inspect.getclasstree([obj], unique=True)[0][0].__bases__ != (object,) else f"class {obj.__name__}:", # 尝试获取基类
                "methods": []
            }
            # 遍历类的方法
            for name, member in inspect.getmembers(obj, predicate=inspect.isfunction):
                if name.startswith('__') and name != '__init__': # 过滤掉大多数魔术方法，但保留 __init__
                    continue
                
                # inspect.signature 可以获取更精确的签名
                sig = inspect.signature(member)
                is_async = inspect.iscoroutinefunction(member)

                method_info = {
                    "type": "method",
                    "name": name,
                    "docstring": inspect.getdoc(member),
                    "signature": f"{'async ' if is_async else ''}def {name}{sig}:",
                    "is_async": is_async
                }
                class_info["methods"].append(method_info)
            results.append(class_info)
        elif inspect.isfunction(obj) or inspect.iscoroutinefunction(obj):
            is_async = inspect.iscoroutinefunction(obj)
            sig = inspect.signature(obj)
            results.append({
                "type": "function",
                "name": obj.__name__,
                "docstring": inspect.getdoc(obj),
                "signature": f"{'async ' if is_async else ''}def {obj.__name__}{sig}:",
                "is_async": is_async
            })
    return results


def get_adler32_hash(s):
    return zlib.adler32(s.encode('utf-8'))

def embedding_inputs(inputs:list[str],model_name = None):
    model_name = model_name or os.getenv("Ark_model_name")
    ark_client = Ark(api_key=os.getenv("Ark_api_key"))

    resp = ark_client.embeddings.create(
                model=model_name,
                input=inputs,
                encoding_format="float",
            )
    return [i.embedding for i in resp.data]

def load_inpackage_file(package_name:str, file_name:str,file_type = 'yaml'):
    """ load config """
    with importlib.resources.open_text(package_name, file_name) as f:
        if file_type == 'yaml':
            return yaml.safe_load(f)
        else:
            return f.read()


@contextmanager
def create_session(engine):
    # 5. 创建会话 (Session)
    # Session 是与数据库交互的主要接口，它管理着你的对象和数据库之间的持久化操作
    Session = sessionmaker(bind=engine)
    session = Session()
    try:
        yield session

    except Exception as e:
        print(f"An error occurred: {e}")
        session.rollback() # 发生错误时回滚事务
    finally:
        session.close() # 关闭会话，释放资源


@asynccontextmanager
async def create_async_session(async_engine):
    # 5. 创建会话 (Session)
    # Session 是与数据库交互的主要接口，它管理着你的对象和数据库之间的持久化操作
    Session = sessionmaker(bind=async_engine,
                           expire_on_commit=False, 
                           class_=AsyncSession
                           )
    session = Session()
    try:
        yield session
        # await session.commit() # 在成功的情况下自动提交事务

    except Exception as e:
        print(f"An error occurred: {e}")
        await session.rollback() # 发生错误时回滚事务
        raise # 重新抛出异常，让调用者知道操作失败
    finally:
        await session.close() # 关闭会话，释放资源

