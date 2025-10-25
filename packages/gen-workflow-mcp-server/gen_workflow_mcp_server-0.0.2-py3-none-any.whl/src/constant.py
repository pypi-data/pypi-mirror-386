from agno.db.sqlite import SqliteDb

# from agno.models.google import Gemini
from agno.models.deepseek import DeepSeek

model = DeepSeek("deepseek-chat")
model_pro = DeepSeek("deepseek-chat")
db = SqliteDb(db_file="tmp/test.db")
