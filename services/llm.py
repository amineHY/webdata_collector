from typing import Optional

from langchain.prompts import ChatPromptTemplate
from langchain_community.llms import Ollama
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field

from core.config import settings
from core.logging import logger


def get_model(llm_choice_param, model_name_param):
    if llm_choice_param.lower() == "ollama":
        llm_model = Ollama(model=model_name_param)
        return llm_model
    elif llm_choice_param.lower() == "openai":
        llm_model = ChatOpenAI(
            api_key=settings.OPENAI_API_KEY,
            model=model_name_param,
            temperature=0,
        )
        return llm_model
    else:
        raise ValueError(
            f"{model_name_param} is not a supported model name in {llm_choice_param}."
        )


def setup_llm_chain(llm_choice_param="OpenAI", model_name_param="gpt-4"):
    class Post(BaseModel):
        """https://python.langchain.com/v0.1/docs/use_cases/extraction/quickstart/"""

        title: Optional[str] = Field(
            description="Title of the post",
            default="None",
        )
        location: Optional[str] = Field(
            description="Location of the product",
            default="None",
        )
        price: Optional[str] = Field(
            description="Price of the product",
            default="None",
        )
        item_number: Optional[str] = Field(
            description="Marketplace item number",
            default="None",
        )

    logger.info(f"Loading LLM prompt")
    llm_prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                "You are an expert extraction algorithm. "
                "Only extract relevant information from the text. "
                "If you do not know the value of an attribute asked to extract, "
                "return null for the attribute's value."
                "Find and extract text of title, location, price, and item_number from HTML code of a Facebook marketplace post.",
            ),
            ("human", "{HTML}"),
        ]
    )

    logger.info(
        f"Loading LLM Model : {llm_choice_param.lower()}, {model_name_param}"
    )
    llm_model = get_model(llm_choice_param, model_name_param)
    chain = llm_prompt | llm_model.with_structured_output(schema=Post)

    return chain


def get_single_post_data_using_llm(html, llm_choice_param, model_name_param):
    """
    Get data from a single post using a Language Model (LLM).

    Parameters:
    - html (str): The HTML code of a Facebook marketplace post.
    - llm_choice_param (str): The choice of LLM to use (e.g. "OpenAI").
    - model_name_param (str): The name of the LLM model to use (e.g. "gpt-4").

    Returns:
    - dict: Extracted data from the post including title, location, price, and item number.

    """
    logger.info("Setup LLM")
    chain = setup_llm_chain(llm_choice_param, model_name_param)

    logger.info("Invoke LLM")
    response = chain.invoke({"HTML": html})
    return response
