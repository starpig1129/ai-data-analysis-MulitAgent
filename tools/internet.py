import os
from langchain_core.tools import tool
from langchain_community.document_loaders import WebBaseLoader, FireCrawlLoader
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from typing import Annotated, List
from bs4 import BeautifulSoup
from logger import setup_logger
from load_cfg import FIRECRAWL_API_KEY,CHROMEDRIVER_PATH
# Set up logger
logger = setup_logger()

@tool
def google_search(query: Annotated[str, "The search query to use"]) -> str:
    """
    Perform a Google search based on the given query and return the top 5 results.

    This function uses Selenium to perform a headless Google search and BeautifulSoup to parse the results.

    Args:
    query (str): The search query to use.

    Returns:
    str: A string containing the titles, snippets, and links of the top 5 search results.

    Raises:
    Exception: If there's an error during the search process.
    """
    try:
        logger.info(f"Performing Google search for query: {query}")
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        service = Service(CHROMEDRIVER_PATH)

        with webdriver.Chrome(options=chrome_options, service=service) as driver:
            url = f"https://www.google.com/search?q={query}"
            logger.debug(f"Accessing URL: {url}")
            driver.get(url)
            html = driver.page_source

        soup = BeautifulSoup(html, 'html.parser')
        search_results = soup.select('.g') 
        search = ""
        for result in search_results[:5]:
            title_element = result.select_one('h3')
            title = title_element.text if title_element else 'No Title'
            snippet_element = result.select_one('.VwiC3b')
            snippet = snippet_element.text if snippet_element else 'No Snippet'
            link_element = result.select_one('a')
            link = link_element['href'] if link_element else 'No Link'
            search += f"{title}\n{snippet}\n{link}\n\n"

        logger.info("Google search completed successfully")
        return search
    except Exception as e:
        logger.error(f"Error during Google search: {str(e)}")
        return f'Error: {e}'
@tool
def scrape_webpages(urls: Annotated[List[str], "List of URLs to scrape"]) -> str:
    """
    Scrape the provided web pages for detailed information using WebBaseLoader.

    This function uses the WebBaseLoader to load and scrape the content of the provided URLs.

    Args:
    urls (List[str]): A list of URLs to scrape.

    Returns:
    str: A string containing the concatenated content of all scraped web pages.

    Raises:
    Exception: If there's an error during the scraping process.
    """
    try:
        logger.info(f"Scraping webpages: {urls}")
        loader = WebBaseLoader(urls)
        docs = loader.load()
        content = "\n\n".join([f'\n{doc.page_content}\n' for doc in docs])
        logger.info("Webpage scraping completed successfully")
        return content
    except Exception as e:
        logger.error(f"Error during webpage scraping: {str(e)}")
        raise  # Re-raise the exception to be caught by the calling function
@tool
def FireCrawl_scrape_webpages(urls: Annotated[List[str], "List of URLs to scrape"]) -> str:
    """
    Scrape the provided web pages for detailed information using FireCrawlLoader.

    This function uses the FireCrawlLoader to load and scrape the content of the provided URLs.

    Args:
    urls (List[str]): A list of URLs to scrape.

    Returns:
    Any: The result of the FireCrawlLoader's load operation.

    Raises:
    Exception: If there's an error during the scraping process or if the API key is not set.
    """
    if not FIRECRAWL_API_KEY:
        raise ValueError("FireCrawl API key is not set")

    try:
        logger.info(f"Scraping webpages using FireCrawl: {urls}")
        loader = FireCrawlLoader(
            api_key=FIRECRAWL_API_KEY,
            url=urls,
            mode="scrape"
        )
        result = loader.load()
        logger.info("FireCrawl scraping completed successfully")
        return result
    except Exception as e:
        logger.error(f"Error during FireCrawl scraping: {str(e)}")
        raise  # Re-raise the exception to be caught by the calling function
@tool
def scrape_webpages_with_fallback(urls: Annotated[List[str], "List of URLs to scrape"]) -> str:
    """
    Attempt to scrape webpages using FireCrawl, falling back to WebBaseLoader if unsuccessful.

    Args:
    urls (List[str]): A list of URLs to scrape.

    Returns:
    str: The scraped content from either FireCrawl or WebBaseLoader.
    """
    try:
        return FireCrawl_scrape_webpages(urls)
    except Exception as e:
        logger.warning(f"FireCrawl scraping failed: {str(e)}. Falling back to WebBaseLoader.")
        try:
            return scrape_webpages(urls)
        except Exception as e:
            logger.error(f"Both scraping methods failed. Error: {str(e)}")
            return f"Error: Unable to scrape webpages using both methods. {str(e)}"

logger.info("Web scraping tools initialized")