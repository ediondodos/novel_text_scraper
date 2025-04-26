import asyncio
import aiofiles
from tenacity import retry, stop_after_attempt, wait_exponential
from playwright.async_api import async_playwright
from bs4 import BeautifulSoup
import re

async def novel_scraper(novel_name):
    """Async novel scraper using Playwright"""
    formatted_name = novel_name.lower().replace(" ", "-")
    base_url = f"https://novelbin.com/b/{formatted_name}"
    
    async with async_playwright() as p:
        # Configure browser with stealth options
        browser = await p.chromium.launch(
            headless=True,
            args=[
                "--disable-blink-features=AutomationControlled",
                "--disable-dev-shm-usage",
                "--no-sandbox"
            ]
        )
        
        try:
            # First pass - get chapter list
            chapter_urls = await get_chapter_list(browser, base_url)
            if not chapter_urls:
                print("No chapters found")
                return

            # Second pass - parallel chapter scraping
            semaphore = asyncio.Semaphore(5)  # Concurrent requests limit
            tasks = [scrape_chapter(browser, url, semaphore) for url in chapter_urls]
            chapters = await asyncio.gather(*tasks)

            # Async write all chapters
            async with aiofiles.open("chapters.txt", "w", encoding="utf-8") as f:
                for chapter in chapters:
                    if chapter:
                        await f.write(f"{chapter}\n\n--- End of Chapter ---\n\n")

        finally:
            await browser.close()

@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1))
async def get_chapter_list(browser, base_url):
    """Extract all chapter URLs from the table of contents"""
    context = await browser.new_context()
    page = await context.new_page()
    
    try:
        await page.goto(base_url, timeout=60000)
        await page.click("text=READ NOW")
        
        # Find chapter list pattern - adjust based on actual site structure
        await page.wait_for_selector("#chr-content", timeout=10000)
        
        # Extract chapter URLs from navigation
        chapter_urls = []
        while True:
            current_url = page.url
            if current_url not in chapter_urls:
                chapter_urls.append(current_url)
                
            next_link = await page.query_selector("a:has-text('Next Chapter')")
            if not next_link:
                break
                
            await next_link.click()
            await page.wait_for_load_state("networkidle")
            
        return chapter_urls
        
    except Exception as e:
        print(f"Error getting chapters: {str(e)}")
        return []
    finally:
        await context.close()

@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1))
async def scrape_chapter(browser, url, semaphore):
    """Scrape individual chapter with retry logic"""
    async with semaphore:
        context = await browser.new_context()
        page = await context.new_page()
        
        try:
            await page.goto(url, timeout=60000)
            content = await page.wait_for_selector("#chr-content", timeout=10000)
            html = await content.inner_html()
            
            # Clean content with BeautifulSoup
            soup = BeautifulSoup(html, "html.parser")
            for element in soup(["script", "style", "div.ads"]):
                element.decompose()
                
            text = soup.get_text("\n", strip=True)
            return f"Chapter {url.split('/')[-1]}:\n{text}"
            
        except Exception as e:
            print(f"Failed to scrape {url}: {str(e)}")
            return None
        finally:
            await context.close()

async def main():
    novel_name = input("Enter novel name: ").strip()
    await novel_scraper(novel_name)

if __name__ == "__main__":
    asyncio.run(main())
