import asyncio
import os
import json
from dotenv import load_dotenv
from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig, CacheMode, LLMConfig
from crawl4ai.extraction_strategy import LLMExtractionStrategy
from pydantic import BaseModel
from typing import List, Optional

load_dotenv()

# Define the schema for Reddit posts
class RedditPost(BaseModel):
    title: str
    author: str
    upvotes: Optional[str] = None
    comments_count: Optional[str] = None
    post_url: Optional[str] = None
    content_preview: Optional[str] = None
    time_posted: Optional[str] = None

class RedditPosts(BaseModel):
    posts: List[RedditPost]

async def scrape_reddit_internship():
    """Scrape r/internship subreddit using crawl4ai with Gemini API."""

    gemini_api_key = os.getenv("GEMINI_API_KEY")
    if not gemini_api_key:
        raise ValueError("GEMINI_API_KEY not found in environment variables. Please set it in .env file.")

    # Browser configuration
    browser_config = BrowserConfig(
        headless=False,  # Show browser window for debugging
        verbose=True
    )

    # LLM configuration for Gemini
    llm_config = LLMConfig(
        provider="gemini/gemini-2.5-flash",
        api_token=gemini_api_key,
    )

    # LLM extraction strategy using Gemini
    extraction_strategy = LLMExtractionStrategy(
        llm_config=llm_config,
        schema=RedditPosts.model_json_schema(),
        extraction_type="schema",
        instruction="""
        Extract all Reddit posts visible on this page. For each post, extract:
        - title: The title of the post
        - author: The username of the post author (without u/ prefix)
        - upvotes: The upvote count (can be a number or text like "Vote")
        - comments_count: Number of comments
        - post_url: The relative URL to the post (starts with /r/internship/comments/...)
        - content_preview: Any preview text shown for the post
        - time_posted: When the post was made (e.g., "2 hours ago", "1 day ago")

        Return all posts you can find on the page.
        """
    )

    # JavaScript to scroll page and trigger dynamic content loading
    js_code = """
    // Scroll to top first to ensure we see newest posts
    window.scrollTo(0, 0);
    await new Promise(r => setTimeout(r, 1000));

    // Scroll down slowly to trigger lazy loading
    for (let i = 0; i < 3; i++) {
        window.scrollBy(0, 500);
        await new Promise(r => setTimeout(r, 1000));
    }

    // Scroll back to top
    window.scrollTo(0, 0);
    await new Promise(r => setTimeout(r, 500));
    """

    # Crawler run configuration
    run_config = CrawlerRunConfig(
        extraction_strategy=extraction_strategy,
        cache_mode=CacheMode.BYPASS,
        wait_until="networkidle",
        delay_before_return_html=5.0,  # Wait longer for dynamic content
        js_code=js_code,
    )

    async with AsyncWebCrawler(config=browser_config) as crawler:
        print("Crawling r/internships...")

        result = await crawler.arun(
            url="https://www.reddit.com/r/internships/new/",
            config=run_config
        )

        if result.success:
            print("\nCrawl successful!")
            print(f"Status code: {result.status_code}")

            if result.extracted_content:
                try:
                    data = json.loads(result.extracted_content)

                    # Handle both list and dict formats
                    if isinstance(data, list):
                        posts = data
                    else:
                        posts = data.get("posts", [])

                    print(f"\nExtracted {len(posts)} posts:\n")

                    for i, post in enumerate(posts, 1):
                        print(f"--- Post {i} ---")
                        print(f"Title: {post.get('title', 'N/A')}")
                        print(f"Author: {post.get('author', 'N/A')}")
                        print(f"Upvotes: {post.get('upvotes', 'N/A')}")
                        print(f"Comments: {post.get('comments_count', 'N/A')}")
                        print(f"Posted: {post.get('time_posted', 'N/A')}")
                        if post.get('content_preview'):
                            print(f"Preview: {post.get('content_preview')[:100]}...")
                        print()

                    # Save to JSON file
                    with open("reddit_posts.json", "w") as f:
                        json.dump({"posts": posts}, f, indent=2)
                    print("Data saved to reddit_posts.json")

                except json.JSONDecodeError as e:
                    print(f"Error parsing extracted content: {e}")
                    print(f"Raw content: {result.extracted_content[:500]}")
            else:
                print("No content extracted by LLM")
                print(f"Raw markdown (first 1000 chars):\n{result.markdown[:1000] if result.markdown else 'No markdown'}")
        else:
            print(f"Crawl failed: {result.error_message}")

if __name__ == "__main__":
    asyncio.run(scrape_reddit_internship())
