# Importing necessary libraries
import cloudscraper
from bs4 import BeautifulSoup
from io import BytesIO
import re
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
import PyPDF2

# Initialize Cloudscraper to handle website scraping with anti-bot measures
scraper = cloudscraper.create_scraper()

def read_urls_from_file(file_path):
    """Read URLs from the provided text file."""
    print("[INFO] Reading URLs from the file...")
    with open(file_path, 'r') as file:
        lines = file.readlines()
    
    urls = []
    for line in lines:
        if 'https://' in line:
            start_idx = line.find('https://')
            url = line[start_idx:].strip(')\n')
            urls.append(url)
    
    print(f"[INFO] Extracted {len(urls)} URLs from the file.")
    return urls

def setup_webdriver():
    """Set up the Selenium WebDriver with Chrome options."""
    chrome_options = Options()
    chrome_options.add_argument("--headless")  # Run headless for no browser window
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    chrome_service = Service('/Users/zazi/Desktop/Tlaw/PGS/chromedriver.exe')  # Provide path to chromedriver
    driver = webdriver.Chrome(service=chrome_service, options=chrome_options)
    return driver


def extract_text_from_pdf(pdf_content):
    """Extract text from a PDF."""
    with BytesIO(pdf_content) as pdf_stream:
        reader = PyPDF2.PdfReader(pdf_stream)
        full_text = ""
        for page in reader.pages:
            full_text += page.extract_text()
    return full_text

def find_defendant_address_smart(full_text):
    """Attempt to find the defendant's address using various tactics."""
    print("[INFO] Attempting to find the defendant's address using smart tactics...")
    
    # Tactic 1: Look for 'DEF1' followed by an address-like structure
    pattern = r"^DEF1.*"
    match = re.search(pattern, full_text, re.MULTILINE)
    if match:
        print("[SUCCESS] 'DEF1' line found, extracting address...")
        return match.group().strip()
    
    # Tactic 2: Look for chunks of text that resemble an address
    address_patterns = [
        r"\d{1,5}\s\w+\s(?:Street|St|Avenue|Ave|Boulevard|Blvd|Road|Rd|Drive|Dr)\W?,?\s?\w+\W?\s?\d{5}",  # e.g., "123 Main St, City, 12345"
        r"\b(?:Defendant|Defendants)\b.*Address:.{1,100}"  # e.g., "Defendant Address: 123 Main St..."
    ]
    
    for pattern in address_patterns:
        match = re.search(pattern, full_text, re.MULTILINE | re.IGNORECASE)
        if match:
            print("[SUCCESS] Address-like structure found.")
            return match.group().strip()
    
    print("[INFO] No clear defendant address found.")
    return None

def fetch_document_and_extract_address(url, driver):
    """Fetch the document from the link and extract the defendant's address."""
    print(f"[INFO] Navigating to {url} to extract the document...")
    driver.get(url)
    
    # Attempt to find the link to the Summons + Complaint PDF directly
    try:
        summons_link = driver.find_element(By.LINK_TEXT, 'SUMMONS + COMPLAINT').get_attribute('href')
        print(f"[SUCCESS] Found Summons + Complaint link: {summons_link}")
        
        # Fetch the PDF
        response = scraper.get(summons_link)
        if response.status_code == 200:
            print("[INFO] PDF fetched successfully. Extracting text...")
            pdf_content = response.content
            full_text = extract_text_from_pdf(pdf_content)
            return find_defendant_address_smart(full_text)
        else:
            print(f"[ERROR] Failed to fetch PDF. Status code: {response.status_code}")
    except Exception as e:
        print(f"[ERROR] Could not find the Summons + Complaint link: {e}")
    
    return None

def main():
    # Step 1: Read the URLs from the 'test.txt' file
    file_path = 'test.txt'
    urls = read_urls_from_file(file_path)

    # Step 2: Set up the WebDriver
    driver = setup_webdriver()

    for url in urls:
        try:
            # Step 3: Fetch document and extract address
            defendant_address = fetch_document_and_extract_address(url, driver)
            if defendant_address:
                print(f"Defendant's Address: {defendant_address}")
            else:
                print("[INFO] Defendant's address not found using available tactics.")
        
        except Exception as e:
            print(str(e))
    
    # Close the WebDriver
    driver.quit()

if __name__ == "__main__":
    # Start the main process
    print("[INFO] Starting the case lookup process...")
    main()
    print("[INFO] Process completed.")
