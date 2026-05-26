#This file handles extracting data from Wikipedia given the wiki links:

from typing import Generator
from bs4 import BeautifulSoup
from tqdm import tqdm

from langchain_community.document_loaders import WebBaseLoader, WikipediaLoader, AsyncHtmlLoader
from langchain_core.documents import Document

from models import TopicsExtract, Topics, TopicsFactory
from parser import *

import nest_asyncio
nest_asyncio.apply()

def get_extractor(topics: list[TopicsExtract]) -> Generator[list[Topics, list[Document]], None, None]:
    """Extract documents for a list of topics, yielding one at a time.

    Args:
        topics: A list of Topics objects containing topic information.

    Yields:
        List[Topics, list[Document]]: A list containing the topic object and a list of
            documents extracted for that topic.

    Note: "Topic" here means concepts on which AgeT can interview the user. Example: Logistic Regression, Clustering etc
    """

    progress_bar = tqdm(
        topics,
        desc="Extracting docs",
        unit="topic",
        bar_format="{desc}: {percentage:3.0f}%|{bar}| {n_fmt}/{total_fmt} [{elapsed}<{remaining}, {rate_fmt}] {postfix}",
        ncols=100,
        position=0,
        leave=True,
    )

    topic_factory = TopicsFactory()
    for topic in progress_bar:
        topic_obj = topic_factory.get_topic(topic.id)

        progress_bar.set_postfix_str(f"Topic: {topic_obj.name}")

        topic_docs = extract_docs(topic_obj, topic.urls)

        return [topic_obj, topic_docs]
    


def extract_docs(topic : Topics, extract_urls : list[str]) -> list[Document]:
    """Extract documents for a single topic from all sources and deduplicate them.

    Args:
        topic: Topics object containing topic information.
        extract_urls: List of URLs to extract content from.

    Returns:
        list[Document]: List of documents extracted for the topic.
    """

    print("Information Extraction Stage Started ...!")

    print(f"Fetching raw html from : {extract_urls}")
    loader = WebBaseLoader(extract_urls,
                             header_template={
                                 "User-Agent": (
                                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                                "AppleWebKit/537.36 (KHTML, like Gecko) "
                                "Chrome/124.0.0.0 Safari/537.36"
                                )
                            })
    docs = loader.load()

    transformed_docs = []

    for doc in docs:
        soup = BeautifulSoup(doc.page_content, "lxml")
        
        for tag in soup(["script", "style", "sup"]):
            tag.decompose()
        
        for cls in ["toc", "navbox", "reference", "reflist", "mw-editsection", "sidebar", "metadata"]:
            for tag in soup.select(f".{cls}"):
                tag.decompose()

        math_elements = soup.select('annotation[encoding="application/x-tex"]')

        for elem in math_elements:

                latex = elem.get_text(strip=True)

                math_tag = elem.find_parent("math")

                if math_tag:
                    math_tag.replace_with(f"\n$$ {latex} $$\n")

        content = (
                        soup.select_one(".mw-parser-output")
                        or soup.select_one(".mw-body-content")
                        or soup.select_one("#mw-content-text")
                        or soup.body
                    )

        if content is None:
            continue
        
        clean_text = content.get_text(" ", strip=True)
        clean_text = replace_displaystyle(clean_text)
        clean_text = normalize_whitespace(clean_text)

        doc.page_content = clean_text
        doc.metadata['topic_id'] = topic.id
        doc.metadata['topic_name'] = topic.name
        transformed_docs.append(doc)
        
    print("Information Extraction Stage Completed ...!")
    return transformed_docs


if __name__ == "__main__":
    log_reg = TopicsFactory().get_topic("logistic_regression")
    docs = extract_docs(
        log_reg,
        [
            "https://en.wikipedia.org/wiki/Logistic_regression"
        ],
    )
    print(docs)

