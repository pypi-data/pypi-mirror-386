from agno.db.sqlite import SqliteDb
import os

# from agno.models.google import Gemini
from agno.models.deepseek import DeepSeek

model = DeepSeek("deepseek-chat", api_key=os.getenv("DEEPSEEK_API_KEY"))
model_pro = DeepSeek("deepseek-chat", api_key=os.getenv("DEEPSEEK_API_KEY"))
db = SqliteDb(db_file="tmp/test.db")
