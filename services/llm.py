from langchain.chat_models import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from langchain.chains import LLMChain
from langchain.output_parsers import StructuredOutputParser, ResponseSchema

from core.config import settings


def setup_llm_chain():
    response_schemas = [
        ResponseSchema(name="title", description="Title of the listing"),
        ResponseSchema(name="price", description="Price of the listing"),
        ResponseSchema(name="location", description="Location of the listing"),
        ResponseSchema(
            name="item_number", description="Item number of the listing"
        ),
    ]

    output_parser = StructuredOutputParser.from_response_schemas(
        response_schemas
    )
    format_instructions = output_parser.get_format_instructions()

    prompt = ChatPromptTemplate.from_template(
        "Extract listing data from HTML:\n\n{html}\n\n{format_instructions}"
    )

    llm = ChatOpenAI(
        model="gpt-4",
        openai_api_key=settings.OPENAI_API_KEY,
        temperature=0,
    )

    chain = LLMChain(llm=llm, prompt=prompt, output_parser=output_parser)
    return chain


def get_single_post_data_using_llm(soup_single_post):
    chain = setup_llm_chain()
    html = soup_single_post.prettify()
    format_instructions = chain.prompt.output_parser.get_format_instructions()

    response = chain.run(
        {"html": html, "format_instructions": format_instructions}
    )
    return response
