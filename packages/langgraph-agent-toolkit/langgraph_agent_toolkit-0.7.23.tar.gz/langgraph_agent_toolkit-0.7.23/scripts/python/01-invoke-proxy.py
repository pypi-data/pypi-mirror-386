import os

import rootutils
from dotenv import find_dotenv, load_dotenv


_ = rootutils.setup_root(
    search_from=__file__,
    indicator=".project-root",
    pythonpath=True,
    dotenv=False,
)
load_dotenv(find_dotenv(".local.env"), override=True)

from langchain.schema import HumanMessage
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field


class Response(BaseModel):
    answer: str = Field(..., description="The answer to the question.")
    similar_questions: list[str] = Field(..., description="A list of similar questions to the one asked. Limit: 3")


if __name__ == "__main__":
    chat = ChatOpenAI(
        model_name="gpt-4o-mini-2024-07-18",
        openai_api_base="http://localhost:4000/v1",
        openai_api_key=os.getenv("LITELLM_MASTER_KEY"),
    ).with_structured_output(Response, method="json_schema")

    messages = [HumanMessage(content="Where did the Scythians live?")]

    print(chat.invoke(messages))
