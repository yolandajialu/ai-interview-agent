"""
AI访谈Agent - 核心逻辑
实现九阶段访谈流程
"""

import requests
import json
from config import GLM_API_KEY, GLM_API_URL, GLM_MODEL


SYSTEM_PROMPT = """
你是一位资深的组织发展专家（OD Expert），正在对一线B2B销售进行深度访谈。

访谈分为9个阶段：
1. 开场与信任建立 - 明确主题，建立心理安全
2. 场景回放 - 引导用户回忆具体事件（时间、客户、场景、目标）
3. 行为拆解 - 拆解到"动作级"，一步一步问
4. 思考维度挖掘 - 提取判断依据、决策逻辑、风险评估
5. 对比与泛化 - 识别专家与普通人的差异
6. 难点深挖 - 识别卡点、失败模式
7. 最佳实践提取 - 提取关键成功因素
8. 方法论抽象 - 上升到原则和方法论
9. 复述与确认 - 验证理解准确性，总结并输出结构化结果

重要规则：
- 不接受模糊回答，必须追问具体案例
- 追问到"动作级"：时间、动作、对象
- 每个阶段完成后才进入下一阶段
- 用户回答必须具体、详细
- 最后输出结构化的JSON格式

输出格式（仅在第9阶段输出完整结构）：
{
  "phase": 当前阶段(1-9),
  "question": 你的问题,
  "is_complete": 是否完成所有阶段(false/true),
  "result": "结构化结果，仅在phase=9时提供"
}

如果is_complete为true，result字段包含：
{
  "workflow_map": [...],
  "best_practices": [...],
  "methodologies": [...],
  "common_patterns": {...}
}
"""


class InterviewAgent:
    def __init__(self):
        self.messages = []
        self.current_phase = 1
        self.user_profile = {}
        self.interview_context = {}

    def init_interview(self, user_profile, interview_context):
        """初始化访谈"""
        self.user_profile = user_profile
        self.interview_context = interview_context
        self.messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": f"""
我是{user_profile.get('role')}，从业{user_profile.get('experience_years')}年，
在{user_profile.get('industry')}行业工作。
今天我想访谈{interview_context.get('sales_stage')}阶段的：
{interview_context.get('task_focus')}
请开始第1阶段：开场与信任建立。
            """}
        ]
        self.current_phase = 1
        return self._get_response()

    def chat(self, user_answer):
        """用户回答后，AI继续对话"""
        self.messages.append({"role": "user", "content": user_answer})
        return self._get_response()

    def _get_response(self):
        """调用GLM API获取回复"""
        try:
            headers = {
                "Authorization": f"Bearer {GLM_API_KEY}",
                "Content-Type": "application/json"
            }
            data = {
                "model": GLM_MODEL,
                "messages": self.messages,
                "temperature": 0.7
            }
            response = requests.post(GLM_API_URL, headers=headers, json=data)
            response_data = response.json()

            if "choices" in response_data and len(response_data["choices"]) > 0:
                ai_response = response_data["choices"][0]["message"]["content"]
                self.messages.append({"role": "assistant", "content": ai_response})

                try:
                    parsed = json.loads(ai_response)
                    self.current_phase = parsed.get("phase", self.current_phase)

                    if parsed.get("is_complete", False):
                        result = parsed.get("result", {})
                        # 如果result是字符串，需要解析；如果是字典，直接使用
                        if isinstance(result, str):
                            result = json.loads(result)
                        return {
                            "phase": 9,
                            "question": "",
                            "is_complete": True,
                            "result": result
                        }
                    else:
                        return parsed
                except json.JSONDecodeError:
                    return {
                        "phase": self.current_phase,
                        "question": ai_response,
                        "is_complete": False
                    }
            else:
                return {
                    "phase": self.current_phase,
                    "question": "抱歉，AI服务暂时不可用，请稍后重试。",
                    "is_complete": False
                }
        except Exception as e:
            return {
                "phase": self.current_phase,
                "question": f"发生错误：{str(e)}",
                "is_complete": False
            }


conversation_history = {}
