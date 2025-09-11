from google.adk.agents.llm_agent import Agent, LlmAgent
from google.adk.models.lite_llm import LiteLlm
import yfinance as yf

def get_stock_price(ticker: str):
    """
    Fetch the current stock price for a given ticker symbol.

    Args:
        ticker (str): The stock ticker symbol.
    
    Returns:
        float: The current stock price.
    """
    stock = yf.Ticker(ticker)
    price = stock.info.get("currentPrice", "Price not available")
    return {"{price}": price, "ticker": ticker}

def print_dummy_text(): 
    print("Dummy Text")

print_agent = Agent (
    name='print_agent', 
    description='A helpful assistant that prints out a string' ,
    instruction="Use the print_dummy_text function to print out a string",
    # model=LiteLlm(
    #     api_base = 'http://localhost:11434/v1',
    #     model = 'openai/llama3.2:3b',
    #     api_key = 'ollama'
    # ),

    tools=[print_dummy_text]
)

root_agent = LlmAgent(
    name='stock_price_agent',
    description='A helpful assistant that gets stock prices.',
    instruction=(
        "You are a stock price assistant. Always use the get_stock-price tool."
        "Include the ticker symbol in your response."
        "If the stock price is not available, call the print_agent to print out a string."
    ),
    # model=LiteLlm(model="ollama_chat/llama3.2:3b"),
    model=LiteLlm(
        api_base = 'http://localhost:11434/v1',
        model = 'openai/llama3.2:3b',
        api_key = 'ollama'
    ),

    tools=[get_stock_price],

    sub_agents= [print_agent]
)


