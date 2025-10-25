# 1 日志不打在server中 不打在工具中, 只打在core 中

import math
import asyncio
from pro_craft import AsyncIntel
from digital_life.utils import memoryCards2str
from digital_life.models import MemoryCardGenerate,MemoryCardGenerateEasy, MemoryCard2, MemoryCard, MemoryCardScore, MemoryCards, Document, Chapter, MemoryCardGenerate2
from digital_life import super_log
from pro_craft.utils import create_async_session
import pandas as pd

class MemoryCardManager:
    def __init__(self,inference_save_case = False,model_name = "doubao-1-5-pro-256k-250115"):
        self.inters = AsyncIntel(model_name = model_name)
        self.inference_save_case = inference_save_case

    @staticmethod
    def get_score_overall(
        S: list[int], total_score: int = 0, epsilon: float = 0.001, K: float = 0.8
    ) -> float:
        """
        计算 y = sqrt(1/600 * x) 的值。
        计算人生总进度
        """
        x = sum(S)
        
        S_r = [math.sqrt((1/101) * i)/6 for i in S]
        return sum(S_r)

        # return math.sqrt((1/601) * x)  * 100

    @staticmethod
    def get_score(
        S: list[int], total_score: int = 0, epsilon: float = 0.001, K: float = 0.01
    ) -> float:
        # 人生主题分值计算
        # 一个根据 列表分数 计算总分数的方法 如[1,4,5,7,1,5] 其中元素是 1-10 的整数

        # 一个非常小的正数，确保0分也有微弱贡献，100分也不是完美1
        # 调整系数，0 < K <= 1。K越大，总分增长越快。

        for score in S:
            # 1. 标准化每个分数到 (0, 1) 区间
            normalized_score = (score + epsilon) / (10 + epsilon)

            # 2. 更新总分
            # 每次增加的是“距离满分的剩余空间”的一个比例
            total_score = total_score + (100 - total_score) * normalized_score * K

            # 确保不会因为浮点数精度问题略微超过100，虽然理论上不会
            if total_score >= 100 - 1e-9:  # 留一点点余地，避免浮点数误差导致判断为100
                total_score = 100 - 1e-9  # 强制设置一个非常接近100但不等于100的值
                break  # 如果已经非常接近100，可以提前终止

        return total_score

    async def ascore_from_memory_card(self, memory_cards: list[str]) -> list[int]:
        # 正式运行
        tasks = []
        for memory_card in memory_cards:
            tasks.append(
                self.inters.intellect_remove_format(
                    input_data=memory_card,
                    prompt_id = "0088",
                    version = None,
                    inference_save_case=self.inference_save_case,
                    OutputFormat = MemoryCardScore,
                )
            )
        result_1 = await asyncio.gather(*tasks, return_exceptions=False)
        return result_1

    async def amemory_card_merge(self, memory_cards: list[str]):
        memoryCards_str, memoryCards_time_str = memoryCards2str(memory_cards)
        result_1 = await self.inters.intellect_remove_format(
            input_data=memoryCards_str + "\n 各记忆卡片的时间" + memoryCards_time_str,
            prompt_id = "0089",
            version = None,
            inference_save_case=self.inference_save_case,
            OutputFormat = MemoryCard2,
        )
        return result_1

    async def amemory_card_polish(self, memory_card: dict) -> dict:
        result_1 = await self.inters.intellect_remove_format(
            input_data="\n记忆卡片标题: "+ memory_card["title"]+ "\n记忆卡片内容: " + memory_card["content"] + "\n记忆卡片发生时间: " + memory_card["time"],
            prompt_id = "0090",
            version = None,
            inference_save_case=self.inference_save_case,
            OutputFormat = MemoryCard,
        )
        result_1.update({"time": ""})
        return result_1

    async def agenerate_memory_card_by_text(self, chat_history_str: str, weight: int = 1000):
        """
        # 0091 上传文件生成记忆卡片-memory_card_system_prompt
        # 0092 上传文件生成记忆卡片-time_prompt
        0093 聊天历史生成记忆卡片-memory_card_system_prompt
        0094 聊天历史生成记忆卡片-time_prompt
        """
        number_ = len(chat_history_str) // weight + 1
        result_dict = await self.inters.intellect_remove_format(
            input_data = f"建议输出卡片数量:  {number_} 个记忆卡片" + chat_history_str,
            prompt_id = "0093",
            version = None,
            inference_save_case=self.inference_save_case,
            OutputFormat = Document,
            ExtraFormats=[Chapter],
        )

        chapters = result_dict["chapters"]

        time_dicts = await self.inters.intellect_remove_formats(
            input_datas=[f"# chat_history: {chat_history_str} # chapter:" + chapter.get("content") for chapter in chapters],
            prompt_id = "0094",
            version = None,
            inference_save_case=self.inference_save_case,
            OutputFormat = MemoryCardGenerate2,
        )
        super_log(time_dicts,"time_dicts_before_111")

        doc = {"稚龄":"0到10岁",
        "少年":"11到20岁",
        "弱冠":"21到30岁",
        "而立":"31到40岁",
        "不惑":"41到50岁",
        "知天命":"51到60岁",
        "耳顺":"61到70岁",
        "古稀":"71到80岁",
        "耄耋":"81到90岁",
        "鲐背":"91到100岁",
        "期颐":"101到110岁"}

        time_dicts_time = [time_dict.get('time') for time_dict in time_dicts]
        for i,time_dict in enumerate(time_dicts):
            print()
            print(time_dicts_time[i],'time_dicts_timei')
            xx = doc.get(time_dicts_time[i],time_dicts_time[i])
            print(xx,'xxxx')
            time_dict.update({"time":xx})

        super_log(time_dicts,"time_dicts")
        if not len(time_dicts) == len([f"# chat_history: {chat_history_str} # chapter:" + chapter.get("content") for chapter in chapters]):
            chapters = chapters[:1]
        for i,chapter in enumerate(chapters):
            chapter.update(time_dicts[i])

        return chapters
    

    async def agenerate_memory_card(self, chat_history_str: str, weight: int = 1000):
        """
        0093 聊天历史生成记忆卡片-memory_card_system_prompt
        0094 聊天历史生成记忆卡片-time_prompt
        """
        number_ = len(chat_history_str) // weight + 1
        result_dict = await self.inters.intellect_remove_format(
            input_data = f"建议输出卡片数量:  {number_} 个记忆卡片" + chat_history_str,
            prompt_id = "0093",
            version = None,
            inference_save_case=self.inference_save_case,
            OutputFormat = Document,
            ExtraFormats=[Chapter],
        )

        chapters = result_dict["chapters"]

        time_dicts = await self.inters.intellect_remove_formats(
            input_datas=[f"# chat_history: {chat_history_str} # chapter:" + chapter.get("content") for chapter in chapters],
            prompt_id = "0094",
            version = None,
            inference_save_case=self.inference_save_case,
            OutputFormat = MemoryCardGenerate2,
        )
        super_log(time_dicts,"time_dicts_before_111")

        doc = {"稚龄":"0到10岁",
        "少年":"11到20岁",
        "弱冠":"21到30岁",
        "而立":"31到40岁",
        "不惑":"41到50岁",
        "知天命":"51到60岁",
        "耳顺":"61到70岁",
        "古稀":"71到80岁",
        "耄耋":"81到90岁",
        "鲐背":"91到100岁",
        "期颐":"101到110岁"}

        time_dicts_time = [time_dict.get('time') for time_dict in time_dicts]
        for i,time_dict in enumerate(time_dicts):
            print()
            print(time_dicts_time[i],'time_dicts_timei')
            xx = doc.get(time_dicts_time[i],time_dicts_time[i])
            print(xx,'xxxx')
            time_dict.update({"time":xx})

        super_log(time_dicts,"time_dicts")
        if not len(time_dicts) == len([f"# chat_history: {chat_history_str} # chapter:" + chapter.get("content") for chapter in chapters]):
            chapters = chapters[:1]
        for i,chapter in enumerate(chapters):
            chapter.update(time_dicts[i])

        return chapters

    async def evals(self):
        df = pd.DataFrame({'status':[],"score":[],"bad_case":[],"total":[]})
        # status,score, bad_case, total = await self.inters.intellect_remove_format_eval(
        #     prompt_id="0078",
        #     OutputFormat = MemoryCardGenerate,
        #     ExtraFormats = [],
        #     version = None,
        # )
        # df.loc['0078'] = [status,score, bad_case, total]
        status,score, bad_case, total = await self.inters.intellect_remove_format_eval(
            prompt_id="0094",
            OutputFormat = MemoryCardGenerateEasy,
            ExtraFormats = [],
            version = None,
        )
        df.loc['0094'] = [status,score, bad_case, total]
        df.to_csv('hh.csv')
        # self.inters.intellect_remove_format_eval(
        #     prompt_id="0093",
        #     OutputFormat = Document,
        #     ExtraFormats = [Chapter],
        #     version = None,
        # )

        # self.inters.intellect_remove_format_eval(
        #     prompt_id="0091",
        #     OutputFormat = Document,
        #     ExtraFormats = [Chapter],
        #     version = None,
        # )
