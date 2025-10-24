# 测试1
from pro_craft.utils import extract_
from pro_craft import logger as pro_craft_logger
from llmada.core import BianXieAdapter, ArkAdapter
from datetime import datetime
from enum import Enum
import functools
import json
import os
from pro_craft.database import Prompt, UseCase, PromptBase
from pro_craft.utils import create_session, create_async_session
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine # 异步核心
from sqlalchemy import select, delete # 导入 select, delete 用于异步操作
import inspect
from datetime import datetime
from pro_craft.utils import extract_
import asyncio
import re
from pydantic import BaseModel, ValidationError, field_validator
from sqlalchemy import select, desc
from json.decoder import JSONDecodeError
from pro_craft.database import SyncMetadata
from datetime import datetime, timedelta
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy import select, and_ # 引入 select 和 and_
from sqlalchemy.orm import class_mapper # 用于检查对象是否是持久化的


class IntellectRemoveFormatError(Exception):
    pass

class IntellectRemoveError(Exception):
    pass

BATCH_SIZE = 100
MIN_SUCCESS_RATE = 00.0 # 这里定义通过阈值, 高于该比例则通过


def slog(s, target: str = "target",logger = None):
    COLOR_GREEN = "\033[92m"
    COLOR_RESET = "\033[0m" # 重置颜色
    logger("\n"+f"{COLOR_GREEN}=={COLOR_RESET}" * 50)
    logger(target + "\n       "+"--" * 40)
    logger(type(s))
    logger(s)
    logger("\n"+f"{COLOR_GREEN}=={COLOR_RESET}" * 50)

def fix_broken_json_string(broken_json_str):
    # 移除 BOM
    broken_json_str = broken_json_str.lstrip('\ufeff')
    # 移除大部分非法 ASCII 控制字符
    broken_json_str = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f]', '', broken_json_str)

    # 尝试找到 "content": " 和它对应的结束 "
    # 这是一个挑战，因为中间有未转义的换行。
    # 我们会寻找 "content": "，然后捕获从那以后直到最后一个 " 的所有内容，并替换其中的裸换行。

    # 注意：这个正则假设 "content" 的值是最后一个键值对，并且直到字符串末尾的 " 才结束
    # 并且假设其他字段都是合法的单行字符串
    fixed_json_str = re.sub(
        r'("content":\s*")(.+?)"\s*}',  # 匹配 "content": "，然后捕获所有内容直到最后一个 " }
        lambda m: m.group(1) + m.group(2).replace('\n', '\\n').replace('\r', '\\r') + '"\n}',
        broken_json_str,
        flags=re.DOTALL # 允许 . 匹配换行
    )

    # 修正可能的最后一行丢失的 }
    if not fixed_json_str.strip().endswith('}'):
        fixed_json_str += '\n}' # 补上结束的 }

    return fixed_json_str


# def get_last_sync_time(target_session) -> datetime:
#     """从目标数据库获取上次同步时间"""
#     metadata_entry = target_session.query(SyncMetadata).filter_by(table_name="sync_metadata").first()
#     if metadata_entry:
#         return metadata_entry.last_sync_time
#     return datetime(1970, 1, 1) # 默认一个很早的时间

# def update_last_sync_time(target_session, new_sync_time: datetime):
#     """更新目标数据库的上次同步时间"""
#     metadata_entry = target_session.query(SyncMetadata).filter_by(table_name="sync_metadata").first()
#     if metadata_entry:
#         metadata_entry.last_sync_time = new_sync_time
#     else:
#         # 如果不存在，则创建
#         new_metadata = SyncMetadata(table_name="sync_metadata", last_sync_time=new_sync_time)
#         target_session.add(new_metadata)
#     target_session.commit()
#     print(f"Updated last sync time to: {new_sync_time}")


async def get_last_sync_time(target_session: AsyncSession) -> datetime:
    """从目标数据库获取上次同步时间"""
    # 修正点：使用 select() 和 execute()
    result = await target_session.execute(
        select(SyncMetadata).filter_by(table_name="ai_sync_metadata")
    )
    metadata_entry = result.scalar_one_or_none() # 获取单个对象或 None

    if metadata_entry:
        return metadata_entry.last_sync_time
    return datetime(1970, 1, 1) # 默认一个很早的时间


# from your_module import SyncMetadata # 假设 SyncMetadata 已导入
# from sqlalchemy import select # 确保引入 select

async def update_last_sync_time(target_session: AsyncSession, new_sync_time: datetime):
    """更新目标数据库的上次同步时间"""
    # 修正点：使用 select() 和 execute()
    result = await target_session.execute(
        select(SyncMetadata).filter_by(table_name="ai_sync_metadata")
    )
    metadata_entry = result.scalar_one_or_none()

    if metadata_entry:
        metadata_entry.last_sync_time = new_sync_time
    else:
        # 如果不存在，则创建
        new_metadata = SyncMetadata(table_name="ai_sync_metadata", last_sync_time=new_sync_time)
        target_session.add(new_metadata)
    
    # 异步提交事务
    await target_session.commit() # TODO
    print(f"Updated last sync time to: {new_sync_time}")






class IntellectType(Enum):
    train = "train"
    inference = "inference"
    summary = "summary"

class AsyncIntel():
    def __init__(self,
                 database_url = "",
                 model_name = "",
                 logger = None,
                ):
        database_url = database_url or os.getenv("database_url")
        self.logger = logger or pro_craft_logger
        try:
            assert database_url
            assert 'aio' in database_url
        except AssertionError as e:
            slog(database_url,'database_url',logger=self.logger.warning)
            raise IntellectRemoveFormatError(f"异步服务url必须提供, 且必须是aiomysql配置") from e

        self.engine = create_async_engine(database_url, echo=False,
                                    pool_size=10,        # 连接池中保持的连接数
                                    max_overflow=20,     # 当pool_size不够时，允许临时创建的额外连接数
                                    pool_recycle=3600,   # 每小时回收一次连接
                                    pool_pre_ping=True,  # 使用前检查连接活性
                                    pool_timeout=30      # 等待连接池中连接的最长时间（秒）
                                           )
        self.create_specific_database(self.engine,["ai_prompts","ai_usecase"])

        if model_name in ["gemini-2.5-flash-preview-05-20-nothinking",]:
            self.llm = BianXieAdapter(model_name = model_name)
        elif model_name in ["doubao-1-5-pro-256k-250115",]:
            self.llm = ArkAdapter(model_name = model_name)
        else:
            print('Use BianXieAdapter')
            self.llm = BianXieAdapter()
            
    async def create_specific_database(self,engine, tables_to_create_names: list[str]):
        async with engine.begin() as conn:
            # 从 metadata 中获取对应的 Table 对象
            specific_database_objects = []
            for table_name in tables_to_create_names:
                if table_name in PromptBase.metadata.tables:
                    specific_database_objects.append(PromptBase.metadata.tables[table_name])
                else:
                    print(f"Warning: Table '{table_name}' not found in metadata.")

            if specific_database_objects:
                await conn.run_sync(PromptBase.metadata.create_all, tables=specific_database_objects)
            else:
                print("No specific tables to create.")

    async def create_database(self,engine):
        async with engine.begin() as conn:
            await conn.run_sync(PromptBase.metadata.create_all)
            
    async def _get_latest_prompt_version(self,target_prompt_id,session):
        """
        获取指定 prompt_id 的最新版本数据，通过创建时间判断。
        """
        stmt = select(Prompt).filter(
            Prompt.prompt_id == target_prompt_id
        ).order_by(
            desc(Prompt.timestamp), # 使用 sqlalchemy.desc() 来指定降序
            desc(Prompt.version)    # 使用 sqlalchemy.desc() 来指定降序
        )
        
        result = await session.execute(stmt)
        # 3. 从 Result 对象中获取第一个模型实例
        # .scalars() 用于从结果行中获取第一个列的值（这里是Prompt对象本身）
        # .first() 获取第一个结果
        result = result.scalars().first()

        return result

    async def _get_specific_prompt_version(self,target_prompt_id, target_version,session):
        """
        获取指定 prompt_id 和特定版本的数据。

        Args:
            target_prompt_id (str): 目标提示词的唯一标识符。
            target_version (int): 目标提示词的版本号。
            table_name (str): 存储提示词数据的数据库表名。
            db_manager (DBManager): 数据库管理器的实例，用于执行查询。

        Returns:
            dict or None: 如果找到，返回包含 id, prompt_id, version, timestamp, prompt 字段的字典；
                        否则返回 None。
        """
        stmt = select(Prompt).filter(
        Prompt.prompt_id == target_prompt_id,
        Prompt.version == target_version
        )
        result = await session.execute(stmt)

        specific_prompt = result.scalars().one_or_none()

        return specific_prompt

    async def sync_prompt_data_to_database(self,database_url:str):
        target_engine = create_async_engine(database_url, echo=False)
        await self.create_database(target_engine) 
        async with create_async_session(self.engine) as source_session:
            async with create_async_session(target_engine) as target_session:
            
                last_sync_time = await get_last_sync_time(target_session)
                print(f"Starting sync for sync_metadata from: {last_sync_time}")


                processed_count = 0
                #2 next_sync_watermark = last_sync_time
                current_batch_max_updated_at = last_sync_time

                while True:
                    source_results = await source_session.execute(
                        select(Prompt)
                        .filter(Prompt.timestamp > last_sync_time)
                        .order_by(Prompt.timestamp.asc(), Prompt.id.asc())
                        .limit(BATCH_SIZE)
                    )
                    records_to_sync = source_results.scalars().all()
                    if not records_to_sync:
                        break # 没有更多记录了

                    #2 max_timestamp_in_batch = datetime(1970, 1, 1) # 初始化为最早时间

                    # 准备要插入或更新到目标数据库的数据
                    for record in records_to_sync:
                        # 查找目标数据库中是否存在该ID的记录
                        # 这里的 `User` 模型会对应到 target_db.users
                        target_prompt_result = await target_session.execute(
                            select(Prompt).filter_by(id=record.id) # 假设 prompt_id 是唯一标识符
                        )
                        target_prompt = target_prompt_result.scalar_one_or_none()
                        
                        if target_prompt:
                            # 如果存在，则更新
                            target_prompt.prompt_id = record.prompt_id
                            target_prompt.version = record.version
                            target_prompt.timestamp = record.timestamp
                            target_prompt.prompt = record.prompt
                            target_prompt.use_case = record.use_case
                            target_prompt.action_type = record.action_type
                            target_prompt.demand = record.demand
                            target_prompt.score = record.score
                            target_prompt.is_deleted = record.is_deleted
                        else:
                            # 如果不存在，则添加新记录
                            # 注意：这里需要创建一个新的User实例，而不是直接添加源数据库的record对象
                            new_prompt = Prompt(
                                prompt_id=record.prompt_id, 
                                version=record.version,
                                timestamp=record.timestamp,
                                prompt = record.prompt,
                                use_case = record.use_case,
                                action_type = record.action_type,
                                demand = record.demand,
                                score = record.score,
                                is_deleted = record.is_deleted
                                )
                            target_session.add(new_prompt)
                        
                        # 记录当前批次最大的 updated_at
                        #2 
                        # if record.timestamp > max_timestamp_in_batch:
                        #     max_timestamp_in_batch = record.timestamp
                        if record.timestamp > current_batch_max_updated_at:
                            current_batch_max_updated_at = record.timestamp


                    await target_session.commit() 
                    processed_count += len(records_to_sync)
                    print(f"Processed {len(records_to_sync)} records. Total processed: {processed_count}")

                    #2 next_sync_watermark = max_timestamp_in_batch + timedelta(microseconds=1)
                    last_sync_time = current_batch_max_updated_at + timedelta(microseconds=1) 

                    
                    if len(records_to_sync) < BATCH_SIZE: # 如果查询到的记录数小于批次大小，说明已经处理完所有符合条件的记录
                        break

                if processed_count > 0:
                    # 最终更新last_sync_time到数据库，确保记录的是所有已处理记录中最新的一个
                    await update_last_sync_time(target_session, current_batch_max_updated_at + timedelta(microseconds=1))

                    #2 await update_last_sync_time(target_session, next_sync_watermark)

                    await target_session.commit() # 确保最终的 metadata 更新也被提交
                else:
                    print("No new records to sync.")


    async def get_prompts_from_sql(self,
                             prompt_id: str,
                             version = None,
                             session = None) -> Prompt:
        """
        从sql获取提示词
        """
        # 查看是否已经存在
        if version:
            prompts_obj = await self._get_specific_prompt_version(prompt_id,version,session=session)
            if not prompts_obj:
                prompts_obj = await self._get_latest_prompt_version(prompt_id,session = session)
        else:
            prompts_obj = await self._get_latest_prompt_version(prompt_id,session = session)     
        return prompts_obj
        
            
    async def save_prompt_increment_version(self,
                           prompt_id: str,
                           new_prompt: str,
                           use_case:str = "",
                           action_type = "inference",
                           demand = "",
                           score = 60,
                           session = None):
        """
        从sql保存提示词
        input_data 指的是输入用例, 可以为空
        """
        # 查看是否已经存在
        prompts_obj = await self.get_prompts_from_sql(prompt_id=prompt_id,session=session)

        if prompts_obj:
            # 如果存在版本加1
            version_ori = prompts_obj.version
            _, version = version_ori.split(".")
            version = int(version)
            version += 1
            version_ = f"1.{version}"

        else:
            # 如果不存在版本为1.0
            version_ = '1.0'
        
        prompt1 = Prompt(prompt_id=prompt_id, 
                        version=version_,
                        timestamp=datetime.now(),
                        prompt = new_prompt,
                        use_case = use_case,
                        action_type = action_type,
                        demand = demand,
                        score = score
                        )

        session.add(prompt1)
        await session.commit() # 提交事务，将数据写入数据库

    async def get_use_case_by_sql(self,
                             target_prompt_id: str,
                             session = None
                            ):
        """
        从sql保存提示词
        """
        stmt = select(UseCase).filter(UseCase.is_deleted == 0,
                                      UseCase.prompt_id == target_prompt_id)
        
        result = await session.execute(stmt)
        # use_case = result.scalars().one_or_none()
        use_case = result.scalars().all()
        return use_case

    async def save_use_case_by_sql(self,
                             prompt_id: str,
                             use_case:str = "",
                             output = "",
                             solution: str = "",
                             session = None
                            ):
        """
        从sql保存提示词
        """
        #TODO 存之前保证数据库中相同的prompt_id中没有重复的use_case

        use_case = UseCase(prompt_id=prompt_id, 
                        use_case = use_case,
                        output = output,
                        solution = solution,
                        )

        session.add(use_case)
        await session.commit() # 提交事务，将数据写入数据库

    async def summary_to_sql(
            self,
            prompt_id:str,
            version = None,
            prompt = "",
            session = None
        ):
        """
        让大模型微调已经存在的 system_prompt
        """
        system_prompt_created_prompt = """        
很棒, 我们已经达成了某种默契, 我们之间合作无间, 但是, 可悲的是, 当我关闭这个窗口的时候, 你就会忘记我们之间经历的种种磨合, 这是可惜且心痛的, 所以你能否将目前这一套处理流程结晶成一个优质的prompt 这样, 我们下一次只要将prompt输入, 你就能想起我们今天的磨合过程,
对了,我提示一点, 这个prompt的主角是你, 也就是说, 你在和未来的你对话, 你要教会未来的你今天这件事, 是否让我看懂到时其次

只要输出提示词内容即可, 不需要任何的说明和解释
"""
        system_result = await self.llm.aproduct(prompt + system_prompt_created_prompt)

        s_prompt = extract_(system_result,pattern_key=r"prompt")
        chat_history = s_prompt or system_result
        await self.save_prompt_increment_version(prompt_id,
                                new_prompt = chat_history,
                                use_case = "",
                                score = 60,
                                session = session)
        
    async def prompt_finetune_to_sql(
            self,
            prompt_id:str,
            version = None,
            demand: str = "",
            session = None,
        ):
        """
        让大模型微调已经存在的 system_prompt
        """
        change_by_opinion_prompt = """
你是一个资深AI提示词工程师，具备卓越的Prompt设计与优化能力。
我将为你提供一段现有System Prompt。你的核心任务是基于这段Prompt进行修改，以实现我提出的特定目标和功能需求。
请你绝对严格地遵循以下原则：
 极端最小化修改原则（核心）：
 在满足所有功能需求的前提下，只进行我明确要求的修改。
 即使你认为有更“优化”、“清晰”或“简洁”的表达方式，只要我没有明确要求，也绝不允许进行任何未经指令的修改。
 目的就是尽可能地保留原有Prompt的字符和结构不变，除非我的功能要求必须改变。
 例如，如果我只要求你修改一个词，你就不应该修改整句话的结构。
 严格遵循我的指令：
 你必须精确地执行我提出的所有具体任务和要求。
 绝不允许自行添加任何超出指令范围的说明、角色扮演、约束条件或任何非我指令要求的内容。
 保持原有Prompt的风格和语调：
 尽可能地与现有Prompt的语言风格、正式程度和语调保持一致。
 不要改变不相关的句子或其表达方式。
 只提供修改后的Prompt：
 直接输出修改后的完整System Prompt文本。
 不要包含任何解释、说明或额外对话。
 在你开始之前，请务必确认你已理解并能绝对严格地遵守这些原则。任何未经明确指令的改动都将视为未能完成任务。

现有System Prompt:
{old_system_prompt}

功能需求:
{opinion}
"""

        prompt_ = await self.get_prompts_from_sql(prompt_id = prompt_id,version = version,
                                                    session=session)
        if demand:
            new_prompt = await self.llm.aproduct(
                change_by_opinion_prompt.format(old_system_prompt=prompt_.prompt, opinion=demand)
            )
        else:
            new_prompt = prompt_
        await self.save_prompt_increment_version(prompt_id = prompt_id,
                            new_prompt = new_prompt,
                            use_case = "",
                            score = 60,
                            session = session)


    async def push_action_order(self,demand : str,prompt_id: str,
                         action_type = 'train'):

        """
        从sql保存提示词
        推一个train 状态到指定的位置

        将打算修改的状态推上数据库 # 1
        """
        # 查看是否已经存在
        async with create_async_session(self.engine) as session:

            latest_prompt = await self.get_prompts_from_sql(prompt_id=prompt_id,session=session)
            if latest_prompt:
                await self.save_prompt_increment_version(prompt_id=latest_prompt.prompt_id,
                                    new_prompt = latest_prompt.prompt,
                                    use_case = latest_prompt.use_case,
                                    action_type=action_type,
                                    demand=demand,
                                    score=latest_prompt.score,
                                    session=session
                                    )
                return "success"
            else:
                await self.save_prompt_increment_version(prompt_id=prompt_id,
                                    new_prompt = demand,
                                    use_case = "init",
                                    action_type="inference",
                                    demand=demand,
                                    score=60,
                                    session=session
                                    )
                return "init"



    async def intellect_remove(self,
                    input_data: dict | str,
                    output_format: str,
                    prompt_id: str,
                    version: str = None,
                    inference_save_case = True,
                    change_case = False,
                    ):
        if isinstance(input_data,dict):
            input_ = json.dumps(input_data,ensure_ascii=False)
        elif isinstance(input_data,str):
            input_ = input_data
        
        # 查数据库, 获取最新提示词对象
        async with create_async_session(self.engine) as session:
            result_obj = await self.get_prompts_from_sql(prompt_id=prompt_id,session=session)
            if result_obj is None:
                raise IntellectRemoveError("不存在的prompt_id")

            prompt = result_obj.prompt
            if result_obj.action_type == "inference":
                # 直接推理即可
                ai_result = await self.llm.aproduct(prompt + output_format + "\nuser:" +  input_)
                if inference_save_case:
                    await self.save_use_case_by_sql(prompt_id,
                                        use_case = input_,
                                        output = ai_result,
                                        solution = "备注/理想回复",
                                        session = session,
                                        )
                    
            elif result_obj.action_type == "train":
                assert result_obj.demand # 如果type = train 且 demand 是空 则报错
                # 则训练推广

                # 新版本 默人修改会 inference 状态
                chat_history = prompt
                before_input = result_obj.use_case
                demand = result_obj.demand
            

                # assert demand
                # # 注意, 这里的调整要求使用最初的那个输入, 最好一口气调整好
                # chat_history = prompt
                # if input_ == before_input: # 输入没变, 说明还是针对同一个输入进行讨论
                #     # input_prompt = chat_history + "\nuser:" + demand
                #     input_prompt = chat_history + "\nuser:" + demand + output_format 
                # else:
                #     # input_prompt = chat_history + "\nuser:" + demand + "\n-----input----\n" + input_
                #     input_prompt = chat_history + "\nuser:" + demand + output_format  + "\n-----input----\n" + input_
            
                # ai_result = await self.llm.aproduct(input_prompt)
                # chat_history = input_prompt + "\nassistant:\n" + ai_result # 用聊天记录作为完整提示词
                # await self.save_prompt_increment_version(prompt_id, chat_history,
                #                         use_case = input_,
                #                         score = 60,
                #                         session = session)


                # version 2

                # if input_ == before_input:
                #     new_prompt = prompt + "\nuser:" + demand
                # else:
                #     new_prompt = prompt + "\nuser:" + input_

                # ai_result = await self.llm.aproduct(new_prompt + output_format)

                # save_new_prompt = new_prompt + "\nassistant:\n" + ai_result


                # await self.save_prompt_increment_version(
                #     prompt_id, 
                #     new_prompt=save_new_prompt,
                #     use_case = input_,
                #     action_type = "inference",
                #     score = 60,
                #     session = session)
                
                if before_input == "" or change_case is True:
                    result_obj.use_case = input_
                    await session.commit()
                    # 查询上一条, 将before_input 更新位input_
                    prompt += input_

                # 使用更新后的数据进行后续步骤
                new_prompt = prompt + "\nuser:" + demand

                ai_result = await self.llm.aproduct(new_prompt + output_format)

                save_new_prompt = new_prompt + "\nassistant:\n" + ai_result


                await self.save_prompt_increment_version(
                    prompt_id, 
                    new_prompt=save_new_prompt,
                    use_case = input_,
                    action_type = "inference",
                    score = 60,
                    session = session)
    
            elif result_obj.action_type == "summary":

                await self.summary_to_sql(prompt_id = prompt_id,
                            prompt = prompt,
                            session = session
                            )
                ai_result = await self.llm.aproduct(prompt + output_format + "\nuser:" +  input_)

            elif result_obj.action_type == "finetune":
                demand = result_obj.demand
            
                assert demand
                await self.prompt_finetune_to_sql(prompt_id = prompt_id,
                                            demand = demand,
                                            session = session
                                            )
                ai_result = await self.llm.aproduct(prompt + output_format + "\nuser:" +  input_)
            elif result_obj.action_type == "patch":
                demand = result_obj.demand
                assert demand
                chat_history = prompt + demand
                ai_result = await self.llm.aproduct(chat_history + output_format + "\nuser:" +  input_)
                self.save_prompt_increment_version(prompt_id, 
                                                   chat_history,
                                                    use_case = input_,
                                                    score = 60,
                                                    session = session)

            else:
                raise

        return ai_result
    
    async def intellect_stream_remove(self,
                    input_data: dict | str,
                    output_format: str,
                    prompt_id: str,
                    version: str = None,
                    inference_save_case = True,
                    push_patch = False,
                    ):
        if isinstance(input_data,dict):
            input_ = json.dumps(input_data,ensure_ascii=False)
        elif isinstance(input_data,str):
            input_ = input_data

        
        # 查数据库, 获取最新提示词对象
        with create_session(self.engine) as session:
            result_obj = await self.get_prompts_from_sql(prompt_id=prompt_id,session=session)

            '''
                        if result_obj is None:
                            await self.save_prompt_increment_version(
                                prompt_id = prompt_id,
                                new_prompt = "做一些处理",
                                use_case = input_,
                                session = session
                            )
                            ai_result = await self.intellect_stream_remove(input_data = input_data,
                                                output_format = output_format,
                                                prompt_id = prompt_id,
                                                version = version,
                                                inference_save_case = inference_save_case
                                                )
                            return ai_result'''

            prompt = result_obj.prompt
            if result_obj.action_type == "inference":
                # 直接推理即可
                
                ai_generate_result = self.llm.aproduct_stream(prompt + output_format +  "\n-----input----\n" +  input_)
                ai_result = ""
                async for word in ai_generate_result:
                    ai_result += word
                    yield word
                if inference_save_case:
                    await self.save_use_case_by_sql(prompt_id,
                                        use_case = input_,
                                        output = ai_result,
                                        solution = "备注/理想回复",
                                        session = session,
                                        )
                    
            elif result_obj.action_type == "train":
                assert result_obj.demand # 如果type = train 且 demand 是空 则报错
                # 则训练推广

                # 新版本 默人修改会 inference 状态
                chat_history = prompt
                before_input = result_obj.use_case
                demand = result_obj.demand
            

                assert demand
                # 注意, 这里的调整要求使用最初的那个输入, 最好一口气调整好
                chat_history = prompt
                if input_ == before_input: # 输入没变, 说明还是针对同一个输入进行讨论
                    # input_prompt = chat_history + "\nuser:" + demand
                    input_prompt = chat_history + "\nuser:" + demand + output_format 
                else:
                    # input_prompt = chat_history + "\nuser:" + demand + "\n-----input----\n" + input_
                    input_prompt = chat_history + "\nuser:" + demand + output_format  + "\n-----input----\n" + input_
            
                ai_generate_result = self.llm.aproduct_stream(input_prompt)
                ai_result = ""
                async for word in ai_generate_result:
                    ai_result += word
                    yield word

                chat_history = input_prompt + "\nassistant:\n" + ai_result # 用聊天记录作为完整提示词
                await self.save_prompt_increment_version(prompt_id, chat_history,
                                        use_case = input_,
                                        score = 60,
                                        session = session)

    
            elif result_obj.action_type == "summary":

                await self.summary_to_sql(prompt_id = prompt_id,
                            prompt = prompt,
                            session = session
                            )
                input_prompt = prompt + output_format + "\n-----input----\n" +  input_
                ai_generate_result = self.llm.aproduct_stream(input_prompt)
                ai_result = ""
                async for word in ai_generate_result:
                    ai_result += word
                    yield word
                
            elif result_obj.action_type == "finetune":
                demand = result_obj.demand
            
                assert demand
                await self.prompt_finetune_to_sql(prompt_id = prompt_id,
                                            demand = demand,
                                            session = session
                                            )
                input_prompt = prompt + output_format + "\n-----input----\n" +  input_
                ai_generate_result = self.llm.aproduct_stream(input_prompt)
                ai_result = ""
                async for word in ai_generate_result:
                    ai_result += word
                    yield word

            elif result_obj.action_type == "patch":
                
                demand = result_obj.demand
                assert demand

                chat_history = prompt + demand
                ai_generate_result = self.llm.aproduct_stream(chat_history + output_format + "\n-----input----\n" +  input_)
                ai_result = ""
                async for word in ai_generate_result:
                    ai_result += word
                    yield word
                if push_patch:
                    self.save_prompt_increment_version(prompt_id, chat_history,
                                            use_case = input_,
                                            score = 60,
                                            session = session)
            else:
                raise

    async def intellect_remove_format(self,
                    input_data: dict | str,
                    OutputFormat: object,
                    prompt_id: str,
                    ExtraFormats: list[object] = [],
                    version: str = None,
                    inference_save_case = True,
                    ):
                
        base_format_prompt = """
按照一定格式输出, 以便可以通过如下校验

使用以下正则检出
"```json([\s\S]*?)```"
使用以下方式验证
"""
        output_format = base_format_prompt + "\n".join([inspect.getsource(outputformat) for outputformat in ExtraFormats]) + inspect.getsource(OutputFormat)

        ai_result = await self.intellect_remove(
                    input_data=input_data,
                    output_format=output_format,
                    prompt_id=prompt_id,
                    version=version,
                    inference_save_case=inference_save_case,
                )

        try:
            json_str = extract_(ai_result,r'json')
            # json_str = fix_broken_json_string(json_str)
            ai_result = json.loads(json_str)
            OutputFormat(**ai_result)

        except JSONDecodeError as e:
            slog(ai_result,logger=self.logger.error)
            try:
                self.logger.error(f"尝试补救")
                json_str = fix_broken_json_string(json_str)
                ai_result = json.loads(json_str)
                OutputFormat(**ai_result)

            except JSONDecodeError as e:
                raise IntellectRemoveFormatError(f"prompt_id: {prompt_id} 生成的内容为无法被Json解析 {e}") from e
        
        except ValidationError as e:
            err_info = e.errors()[0]
            raise IntellectRemoveFormatError(f"{err_info["type"]}: 属性:{err_info['loc']}, 发生了如下错误: {err_info['msg']}, 格式校验失败, 当前输入为: {err_info['input']} 请检查") from e

        except Exception as e:
            raise Exception(f"Error {prompt_id} : {e}") from e

        return ai_result
    
    async def intellect_remove_formats(self,
                    input_datas: list[dict | str],
                    OutputFormat: object,
                    prompt_id: str,
                    ExtraFormats: list[object] = [],
                    version: str = None,
                    inference_save_case = True,
                    ):
                
        async with create_async_session(self.engine) as session:
            prompt_result = await self.get_prompts_from_sql(prompt_id=prompt_id,
                                                                   session=session)
            if prompt_result is None:
                raise IntellectRemoveError("不存在的prompt_id")
        if prompt_result.action_type != "inference":
            input_datas = input_datas[:1]
        tasks = []
        for input_data in input_datas:
            tasks.append(
                self.intellect_remove_format(
                    input_data = input_data,
                    prompt_id = prompt_id,
                    OutputFormat = OutputFormat,
                    ExtraFormats = ExtraFormats,
                    version = version,
                    inference_save_case = inference_save_case,
                )
            )
        results = await asyncio.gather(*tasks, return_exceptions=False)
        return results
    
    def intellect_remove_warp(self,prompt_id: str):
        def outer_packing(func):
            @functools.wraps(func)
            async def wrapper(*args, **kwargs):
                # 修改逻辑
                assert kwargs.get('input_data') # 要求一定要有data入参
                input_data = kwargs.get('input_data')
                assert kwargs.get('OutputFormat') # 要求一定要有data入参
                OutputFormat = kwargs.get('OutputFormat')

                if isinstance(input_data,dict):
                    input_ = output_ = json.dumps(input_data,ensure_ascii=False)
                elif isinstance(input_data,str):
                    input_ = output_ = input_data

                output_ = await self.intellect_remove_format(
                        input_data = input_data,
                        prompt_id = prompt_id,
                        OutputFormat = OutputFormat,
                )

                #######
                kwargs.update({"input_data":output_})
                result = await func(*args, **kwargs)
                return result
            return wrapper
        return outer_packing

    async def intellect_remove_format_eval(self,
                    OutputFormat: object,
                    prompt_id: str,
                    ExtraFormats: list[object] = [],
                    version: str = None,
                    ):
        
        async with create_async_session(self.engine) as session:
            use_cases = await self.get_use_case_by_sql(target_prompt_id=prompt_id,session=session)
            prompt_result = await self.get_prompts_from_sql(prompt_id=prompt_id,
                                                                   session=session)
            if prompt_result is None:
                raise IntellectRemoveError("不存在的prompt_id")
            if prompt_result.action_type != "inference":
                raise IntellectRemoveError("请在inference模式下使用次类")
            

            total_assertions = len(use_cases)
            result_cases = []

            async def evals_func(use_case,prompt_id,OutputFormat,ExtraFormats,version):
                try:
                    # 这里将参数传入
                    await self.intellect_remove_format(
                        input_data = use_case.use_case,
                        prompt_id = prompt_id,
                        OutputFormat = OutputFormat,
                        ExtraFormats = ExtraFormats,
                        version = version,
                        inference_save_case = False,
                    )
                    # TODO base_eval
                    # TODO 人类评价 eval
                    # TODO llm 评价 eval
                    result_cases.append({"type":"Successful","case":use_case.use_case,"reply":f"pass"})
                    use_case.output = "Successful"
                except IntellectRemoveFormatError as e:
                    result_cases.append({"type":"FAILED","case":use_case.use_case,"reply":f"{e}"})
                    use_case.output = f"{"FAILED"}-{e}"
                except Exception as e: # 捕获其他可能的错误
                    result_cases.append({"type":"FAILED","case":use_case.use_case,"reply":f"Exp {e}"})
                    use_case.output = f"{"FAILED"}-{e}"
                    await session.commit()

            tasks = []
            for use_case in use_cases:
                tasks.append(
                    evals_func(
                        use_case = use_case,
                        prompt_id = prompt_id,
                        OutputFormat = OutputFormat,
                        ExtraFormats = ExtraFormats,
                        version = version
                    )
                )
            await asyncio.gather(*tasks, return_exceptions=False)


            successful_assertions = 0
            bad_case = []
            for i in result_cases:
                if i['type'] == "Successful":
                    successful_assertions += 1
                else:
                    bad_case.append(i)

            success_rate = (successful_assertions / total_assertions) * 100
            print(f"\n--- Aggregated Results ---")
            print(f"Total test cases: {total_assertions}")
            print(f"Successful cases: {successful_assertions}")
            print(f"Success Rate: {success_rate:.2f}%")

            # if success_rate >= MIN_SUCCESS_RATE:
            #     return "通过", json.dumps(result_cases,ensure_ascii=False)
            # else:
            #     return "未通过",json.dumps(result_cases,ensure_ascii=False)

            print(bad_case)

            
            # return results




# 整体测试d, 测试未通过d, 大模型调整再测试, 依旧不通过, 大模型裂变, 仍不通过, 互换人力
