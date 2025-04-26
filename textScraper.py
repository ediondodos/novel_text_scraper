import json
import sys
import os
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from bs4 import BeautifulSoup
import time

def novel_scraper(novel_name):
    """ scraps the novel from novelbin.com"""

     # Set up Chrome options for stealth
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option("useAutomationExtension", False)
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--no-sandbox")
    
    # Speed optimization options
    options.add_argument('--disable-images')
    options.add_argument('--disable-gpu')
    options.add_argument('--disable-extensions')
    prefs = {"profile.managed_default_content_settings.images": 2}
    options.add_experimental_option("prefs", prefs)
    
    # Format the novel name for the URL
    formatted_name = novel_name.lower().replace(" ", "-")
    url = f"https://novelbin.com/b/{formatted_name}"
       
     # Initialize the driver
    service = Service(executable_path=ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)



    try:
         # Navigate to the novel's URL first
        driver.get(url)
        print(f"Navigated to: {url}")
        read_now_button = WebDriverWait(driver, 3).until(
            EC.element_to_be_clickable((By.LINK_TEXT, "READ NOW"))
        )
        read_now_button.click()
        print("Clicked READ NOW button.")
 

    
        # Main scraping loop
        while True:
            max_retries = 10
            retry_count = 0
            wait_time = 0.5  # Start with a shorter delay
            
            while retry_count < max_retries:
                try:
                    # More robust wait condition - wait for either the content or an error message
                    WebDriverWait(driver, 10).until(
                        EC.presence_of_element_located((By.ID, "chr-content"))
                    )
                    break  # Content found, exit retry loop
                except Exception as e:
                    retry_count += 1

 
                    # Print only a simple status message to console
                    print(f"Waiting attempt {retry_count}/{max_retries}...")
                    # print(f"Waiting attempt {retry_count}/{max_retries}: {str(e)}")
                    
                    if retry_count >= max_retries:
                        print(f"Maximum retries reached. Moving on.")
                        break
                    
                    time.sleep(wait_time)
                    wait_time *= 2  # Exponential backoff
            
            html_content = driver.page_source
            soup = BeautifulSoup(html_content, 'html.parser')
            chapter_content = soup.find("div", {"id": "chr-content"})
            
            if chapter_content and chapter_content.get_text().strip():
                chapter_text = chapter_content.get_text("\n", strip=True)
                print("\nChapter Text:")
                print(chapter_text[:100] + "...")  # Show just a preview
                
                # Append chapter text to file
                with open("chapter_text.txt", "a", encoding="utf-8") as f:
                    f.write(chapter_text)
                    f.write("\n\n--- End of Chapter ---\n\n")
                print("\nText appended to chapter_text.txt")
            else:
                print("Chapter content not found or empty. Exiting.")
                break
            
            # Attempt to navigate to the next chapter
            try:
                next_link = WebDriverWait(driver, 3).until(
                    EC.element_to_be_clickable((By.LINK_TEXT, "Next Chapter"))
                )
                next_link.click()
                print("Navigating to next chapter...")
            except Exception as e:
                print("No more chapters available or navigation error.")
                break
                
    finally:
        driver.quit()

   
def main():
    try:
          # Check if novel_name is provided as command line argument
        # if len(sys.argv) < 2:
        #     print("Usage:  python3 novel_takerV2.py  echo  'Kill the Sun' | python3 novel_taker+checherV1.py")
        #     return
            
        # novel_name = sys.argv[1]

         
        # Check if novel_name is provided as command line argument
        if len(sys.argv) > 1:
            novel_name = sys.argv[1]
        else:
            # Try to read from stdin if no arguments provided
            novel_name = sys.stdin.read().strip()
         

        
    #     novel_scraper(novel_name.replace('*', '').strip() )
    # except Exception as e:
    #     print(f"Error: {str(e)}")

        if not novel_name:
            print("Usage: python3 novel_taker+checherV1.py 'Novel Name'")
            print("   or: echo 'Novel Name' | python3 novel_taker+checherV1.py")
            return
            
        novel_scraper(novel_name.replace('*', '').strip())
    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    main()
