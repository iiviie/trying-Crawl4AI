import asyncio
import sys
from urllib.parse import urlparse
from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig, CacheMode


async def scrape_to_markdown(url: str, output_file: str = None):
    """Scrape any website and return its content as markdown."""

    # Browser configuration
    browser_config = BrowserConfig(
        headless=True,
        verbose=False
    )

    # Crawler run configuration - simple, no LLM extraction
    run_config = CrawlerRunConfig(
        cache_mode=CacheMode.BYPASS,
        wait_until="networkidle",
        delay_before_return_html=2.0,
    )

    async with AsyncWebCrawler(config=browser_config) as crawler:
        print(f"Scraping: {url}")

        result = await crawler.arun(url=url, config=run_config)

        if result.success:
            markdown_content = result.markdown or ""

            # Determine output filename
            if not output_file:
                domain = urlparse(url).netloc.replace(".", "_")
                output_file = f"{domain}.md"

            # Save to file
            with open(output_file, "w", encoding="utf-8") as f:
                f.write(markdown_content)

            print(f"Success! Saved to {output_file}")
            print(f"Content length: {len(markdown_content)} characters")

            return markdown_content
        else:
            print(f"Failed: {result.error_message}")
            return None


def main():
    if len(sys.argv) < 2:
        print("Usage: python scrape.py <url> [output_file]")
        print("Example: python scrape.py https://example.com")
        print("Example: python scrape.py https://example.com output.md")
        sys.exit(1)

    url = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) > 2 else None

    asyncio.run(scrape_to_markdown(url, output_file))


if __name__ == "__main__":
    main()
