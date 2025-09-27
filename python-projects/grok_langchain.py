from langchain_openai import ChatOpenAI
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain


from dotenv import load_dotenv
import os

load_dotenv()
api_key = os.getenv("OPENROUTER_API_KEY")

# Initialize LangChain LLM with your OpenRouter key
llm = ChatOpenAI(
    model="gpt-5-codex",
    openai_api_key=api_key,
    base_url="https://openrouter.ai/api/v1" , # your OpenRouter endpoint,
    max_tokens=100,
)

# Define a template
template = PromptTemplate(
    input_variables=["topic"],  # variables that will change
    template="Write a funny poem about {topic}."
)

# Fill in the template with a topic
prompt_text = template.format(topic="fresher corporate job for software developerc")

# Simple call
response = llm.invoke(prompt_text)
print("LangChain says:---------", response.content)

chain = LLMChain(
    llm=llm,
    prompt=template
)

# Run the chain with input
result = chain.run({"topic": "one year experience in software dev"})
print("Chain output:-------------", result)