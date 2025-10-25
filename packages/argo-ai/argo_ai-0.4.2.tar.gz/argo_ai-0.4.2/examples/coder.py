from argo import ChatAgent, LLM, Message, Context
import dotenv
import os
import rich
from argo.cli import loop


dotenv.load_dotenv()


agent = ChatAgent(
    name="Coder",
    description="A helpful assistant that can write and run Python code.",
    llm=LLM(model=os.getenv("MODEL")),
)


@agent.skill
async def code(ctx: Context):
    """Use Python to compute math operations.

    Use this skill when you need to compute some math operations.
    """
    result = await ctx.invoke(interpreter)
    await ctx.reply(f"Result={result}.\n\nReply to the user.")


@agent.tool
async def interpreter(code: str):
    """Run Python code and returns a final value.

    The code should compute and store the result
    in a variable called `result`.

    You can import built-in modules, define intermediate
    functions, classes, and variables.

    The final statement should be assigning `result`.

    Do not print anything to the console or use
    non-standard libraries.
    """
    rich.print(f"```python\n{code}\n```")

    env = {}
    exec(code, env, env)
    return env.get("result")


loop(agent)
