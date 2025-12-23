from agno.agent import Agent, RunOutput  # noqa
from agno.models.deepseek import DeepSeek
from dotenv import load_dotenv
from agno.db.sqlite import SqliteDb

load_dotenv()
agent = Agent(
	model=DeepSeek(id="deepseek-chat"),
	db=SqliteDb(db_file="./local.db"),
	enable_user_memories=True,
	markdown=True,
	reasoning=True,
	debug_mode=True,
	debug_level=2,
)

# # Get the response in a variable
# run: RunOutput = agent.run("Share a 2 sentence horror story")
# print(run.content)

# Print the response in the terminal
#
agent.cli_app(
	stream=True,
	show_full_reasoning=True,
)
