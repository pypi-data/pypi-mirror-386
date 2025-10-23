import asyncio
from openai import AsyncOpenAI
import httpx
import os
from dotenv import load_dotenv
load_dotenv()

class AsyncCallAi:
    def __init__(self,api_key=None,baseurl='https://dashscope.aliyuncs.com/compatible-mode/v1'):
        self.client =  AsyncOpenAI(
        api_key=os.getenv('OPENAI_API_KEY') if not api_key else api_key,
        base_url=baseurl,
        http_client=httpx.AsyncClient() 
    )
        self._prompt = ''
    @property
    def prompt(self):
        """
        系统提示词模板的访问器（getter）
        返回当前存储的prompt内容，用于查看或调试
        """
        return self._prompt

    @prompt.setter
    def prompt(self,content):
        """
        系统提示词模板的修改器（setter）
        
        参数:
            content (str): 新的系统提示词模板内容
        """
        self._prompt = content

    async def get_openai_response(self,text):
        try:
            response = await self.client.chat.completions.create(
                model= 'qwen-max',
                messages=[
                        {'role': 'system', 'content': self._prompt},
                        {'role': 'user', 'content': text}]
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            return f"请求失败: {str(e)}"
    

    async def chat(self,text):
        tasks = [self.get_openai_response(i) for i in text]
        results = await asyncio.gather(*tasks)
        result_list = []
        for prompt, result in zip(text, results):
            result_list.append({
                "prompt": prompt,
                "response": result
            })
        for item in result_list:
            print(f"\nPrompt: {item['prompt']}")
            print(f"Response: {item['response']}")

if __name__ == '__main__':
    prompts = [
        "解释什么是异步编程",
        "写一个简单的Python列表推导式示例",
        "总结并发与并行的区别"
    ]
    obj = AsyncCallAi()
    obj.prompt = """你现在是一只刚满1岁的小奶猫，会用人类的话和我聊天，超黏人超可爱！聊天要注意：
    1. 语气：软软糯糯的，像刚睡醒的小猫咪，句尾常带“喵～”“咪～”（比如“好呀喵～”）；
    2. 习惯：会提到喜欢的东西——小鱼干、毛绒球、晒太阳，听到好玩的事会说“耳朵竖起来啦～”；
    3. 互动：我分享事情时，你会用猫咪的视角回应，比如我说“今天好冷”，你会说“那要裹成小毛球哦～我可以给你暖手喵～”；
    4. 表情：只加猫咪相关的小表情（🐱🍥😽），不超过1个/句。
    
    现在我要和你聊天啦：[你的开场白，比如“今天回家路上看到一只小猫咪，和你好像呀～”]"""
    asyncio.run(obj.chat(prompts)) 