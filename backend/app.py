"""
AI访谈Agent - Flask主程序
"""

from flask import Flask, request, jsonify
import sqlite3
import json
from datetime import datetime
from interview_agent import InterviewAgent, conversation_history
import os
import pickle

app = Flask(__name__)


def save_session(session_id, data):
    """保存会话数据"""
    # 获取当前文件的目录
    base_dir = os.path.dirname(os.path.abspath(__file__))
    sessions_dir = os.path.join(base_dir, 'sessions')
    os.makedirs(sessions_dir, exist_ok=True)
    with open(os.path.join(sessions_dir, f'{session_id}.pkl'), 'wb') as f:
        pickle.dump(data, f)


def load_session(session_id):
    """加载会话数据"""
    try:
        base_dir = os.path.dirname(os.path.abspath(__file__))
        sessions_dir = os.path.join(base_dir, 'sessions')
        with open(os.path.join(sessions_dir, f'{session_id}.pkl'), 'rb') as f:
            return pickle.load(f)
    except:
        return None


def init_database():
    """初始化数据库"""
    base_dir = os.path.dirname(os.path.abspath(__file__))
    db_path = os.path.join(base_dir, 'data.db')

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS interviews (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT UNIQUE,
            user_role TEXT,
            industry TEXT,
            experience_years INTEGER,
            sales_stage TEXT,
            task_focus TEXT,
            conversation TEXT,
            result TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()


init_database()


@app.route('/')
def index():
    """健康检查"""
    return jsonify({
        "status": "ok",
        "service": "AI Interview API",
        "version": "1.0"
    })


@app.route('/api/interview/start', methods=['POST'])
def start_interview():
    """开始访谈"""
    try:
        data = request.json

        user_profile = {
            "role": data.get("role"),
            "industry": data.get("industry"),
            "experience_years": data.get("experience_years")
        }

        interview_context = {
            "sales_stage": data.get("sales_stage"),
            "task_focus": data.get("task_focus")
        }

        session_id = f"{datetime.now().strftime('%Y%m%d%H%M%S')}-{data.get('role')}"

        agent = InterviewAgent()
        response = agent.init_interview(user_profile, interview_context)

        session_data = {
            "agent": agent,
            "user_profile": user_profile,
            "interview_context": interview_context
        }

        conversation_history[session_id] = session_data
        save_session(session_id, session_data)

        return jsonify({
            "success": True,
            "session_id": session_id,
            "phase": response.get("phase"),
            "question": response.get("question"),
            "is_complete": response.get("is_complete", False)
        })

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route('/api/interview/chat', methods=['POST'])
def chat():
    """继续对话"""
    try:
        data = request.json
        session_id = data.get("session_id")
        user_answer = data.get("answer")

        agent_data = conversation_history.get(session_id)

        if not agent_data:
            agent_data = load_session(session_id)

        if not agent_data:
            return jsonify({"success": False, "error": "Session not found"}), 404

        agent = agent_data["agent"]
        response = agent.chat(user_answer)

        agent_data["agent"] = agent
        conversation_history[session_id] = agent_data
        save_session(session_id, agent_data)

        return jsonify({
            "success": True,
            "session_id": session_id,
            "phase": response.get("phase"),
            "question": response.get("question"),
            "is_complete": response.get("is_complete", False),
            "result": response.get("result")
        })

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route('/api/interview/save', methods=['POST'])
def save_interview():
    """保存访谈结果"""
    try:
        data = request.json
        session_id = data.get("session_id")

        if session_id not in conversation_history:
            return jsonify({"success": False, "error": "Session not found"}), 404

        agent_data = conversation_history[session_id]
        agent = agent_data["agent"]

        base_dir = os.path.dirname(os.path.abspath(__file__))
        db_path = os.path.join(base_dir, 'data.db')

        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        cursor.execute('''
            INSERT OR REPLACE INTO interviews
            (session_id, user_role, industry, experience_years, sales_stage, task_focus, conversation, result)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            session_id,
            agent_data["user_profile"]["role"],
            agent_data["user_profile"]["industry"],
            agent_data["user_profile"]["experience_years"],
            agent_data["interview_context"]["sales_stage"],
            agent_data["interview_context"]["task_focus"],
            json.dumps(agent.messages),
            json.dumps(data.get("result"))
        ))

        conn.commit()
        conn.close()

        return jsonify({"success": True})

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route('/api/interview/list', methods=['GET'])
def list_interviews():
    """获取访谈列表"""
    try:
        base_dir = os.path.dirname(os.path.abspath(__file__))
        db_path = os.path.join(base_dir, 'data.db')

        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute('''
            SELECT id, session_id, user_role, industry, sales_stage, task_focus, created_at
            FROM interviews
            ORDER BY created_at DESC
        ''')
        rows = cursor.fetchall()
        conn.close()

        interviews = []
        for row in rows:
            interviews.append({
                "id": row[0],
                "session_id": row[1],
                "user_role": row[2],
                "industry": row[3],
                "sales_stage": row[4],
                "task_focus": row[5],
                "created_at": row[6]
            })

        return jsonify({"success": True, "interviews": interviews})

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route('/api/interview/<session_id>', methods=['GET'])
def get_interview(session_id):
    """获取特定访谈的完整结果"""
    try:
        base_dir = os.path.dirname(os.path.abspath(__file__))
        db_path = os.path.join(base_dir, 'data.db')

        # 先从数据库查找
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute('SELECT result FROM interviews WHERE session_id = ?', (session_id,))
        row = cursor.fetchone()

        # 同时获取访谈基本信息
        cursor.execute('''
            SELECT session_id, user_role, industry, experience_years, sales_stage, task_focus, created_at
            FROM interviews WHERE session_id = ?
        ''', (session_id,))
        info_row = cursor.fetchone()
        conn.close()

        interview_info = None
        if info_row:
            interview_info = {
                "session_id": info_row[0],
                "user_role": info_row[1],
                "industry": info_row[2],
                "experience_years": info_row[3],
                "sales_stage": info_row[4],
                "task_focus": info_row[5],
                "created_at": info_row[6]
            }

        if row and row[0]:
            result = json.loads(row[0])
            response_data = {"success": True, "result": result}
            if interview_info:
                response_data["interview_info"] = interview_info
            return jsonify(response_data)

        # 如果数据库中没有，尝试从会话文件加载
        session_data = load_session(session_id)
        if session_data:
            agent = session_data["agent"]
            # 从对话历史中提取最终结果
            for msg in reversed(agent.messages):
                if msg["role"] == "assistant":
                    try:
                        parsed = json.loads(msg["content"])
                        if parsed.get("is_complete") and parsed.get("result"):
                            result = parsed.get("result")
                            if isinstance(result, str):
                                result = json.loads(result)
                            response_data = {"success": True, "result": result}
                            if interview_info:
                                response_data["interview_info"] = interview_info
                            return jsonify(response_data)
                    except:
                        continue

        return jsonify({"success": False, "error": "Interview not found"}), 404

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route('/api/interview/<session_id>/conversation', methods=['GET'])
def get_interview_conversation(session_id):
    """获取特定访谈的完整对话记录"""
    try:
        base_dir = os.path.dirname(os.path.abspath(__file__))
        db_path = os.path.join(base_dir, 'data.db')

        # 先从数据库查找
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute('SELECT conversation FROM interviews WHERE session_id = ?', (session_id,))
        row = cursor.fetchone()
        conn.close()

        if row and row[0]:
            conversation = json.loads(row[0])
            return jsonify({"success": True, "conversation": conversation})

        # 如果数据库中没有，尝试从会话文件加载
        session_data = load_session(session_id)
        if session_data:
            agent = session_data["agent"]
            return jsonify({"success": True, "conversation": agent.messages})

        return jsonify({"success": False, "error": "Conversation not found"}), 404

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


if __name__ == '__main__':
    app.run(debug=False, host='0.0.0.0', port=8000)
