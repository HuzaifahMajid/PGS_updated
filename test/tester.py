# Importing necessary libraries
import cloudscraper
from bs4 import BeautifulSoup
import PyPDF2
from io import BytesIO

# Initialize Cloudscraper to handle website scraping with anti-bot measures
scraper = cloudscraper.create_scraper()

def read_urls_from_file(file_path):
    """Read URLs from the provided text file."""
    print("[INFO] Reading URLs from the file...")
    with open(file_path, 'r') as file:
        lines = file.readlines()
    
    urls = []
    for line in lines:
        # Extract the URL from the line if it contains 'https://'
        if 'https://' in line:
            start_idx = line.find('https://')
            url = line[start_idx:].strip(')\n')  # Extract the URL and strip extra characters
            urls.append(url)
    
    print(f"[INFO] Extracted {len(urls)} URLs from the file.")
    return urls

def get_case_number():
    """Prompt user for case number."""
    # Ask for user input to get the case number
    case_number = input("Enter the case number: ")  
    print(f"[INFO] Case number entered: {case_number}")
    return case_number

def construct_document_list_url(case_number):
    """Construct the document list URL based on case number."""
    # Construct the URL using the provided case number
    base_url = "https://iapps.courts.state.ny.us/nyscef/DocumentList?docketId="
    docket_id = case_number  # In practice, you'd extract the docket ID from the case number
    document_list_url = f"{base_url}{docket_id}"
    print(f"[INFO] Constructed Document List URL: {document_list_url}")
    return document_list_url

def fetch_document_list_page(document_list_url):
    """Fetch the document list HTML."""
    print(f"[INFO] Fetching document list page for URL: {document_list_url}")
    # Send a GET request to fetch the document list page
    response = scraper.get(document_list_url)
    if response.status_code == 200:
        print("[SUCCESS] Document list page fetched successfully.")
        return BeautifulSoup(response.content, 'html.parser')
    else:
        raise Exception(f"[ERROR] Failed to load document list page: {response.status_code}")

def find_summons_link(soup):
    """Find the link to the Summons + Complaint PDF in the document list."""
    base_url = "https://iapps.courts.state.ny.us/nyscef/"
    print("[INFO] Searching for the 'Summons + Complaint' link in the document list...")
    # Search for the link that contains the text "SUMMONS + COMPLAINT"
    for link in soup.find_all('a', string="SUMMONS + COMPLAINT"):
        summons_url = base_url + link.get('href')
        print(f"[SUCCESS] Found Summons + Complaint link: {summons_url}")
        return summons_url
    raise Exception("[ERROR] Summons + Complaint link not found")

def fetch_summons_pdf(summons_url):
    """Fetch the Summons + Complaint PDF."""
    print(f"[INFO] Fetching the PDF from the link: {summons_url}")
    # Send a GET request to fetch the PDF content
    response = scraper.get(summons_url)
    if response.status_code == 200:
        print("[SUCCESS] PDF fetched successfully.")
        return response.content
    else:
        raise Exception(f"[ERROR] Failed to load PDF: {response.status_code}")

import re
def extract_defendant_address(pdf_content):
    """Extract the line starting with 'DEF1' from the first page of the PDF."""
    print("[INFO] Extracting text from the PDF...")
    
    # Load the PDF content
    with BytesIO(pdf_content) as pdf_stream:
        reader = PyPDF2.PdfReader(pdf_stream)
        
        # Extract text from the first page
        first_page = reader.pages[0]
        full_text = first_page.extract_text()
        
        # Use regular expression to find the line starting with 'DEF1'
        print("[INFO] Searching for the line starting with 'DEF1'...")
        
        # Regular expression pattern to capture the line starting with 'DEF1'
        pattern = r"^DEF.*  "
        match = re.search(pattern, full_text, re.MULTILINE)  # Use re.MULTILINE to match at the start of lines
        
        if match:
            defendant_line = match.group().strip()  # Extract the line and remove any extra spaces
            print(f"[SUCCESS] Line extracted:\n\n\n {defendant_line}")
            return defendant_line
        else:
            print("[INFO] Line starting with 'DEF1' not found on the first page, continuing with the rest of the program...")
            return None  # Continue with the rest of the program


def main():
    # Step 1: Read the URLs from the 'test.txt' file
    file_path = 'test.txt'
    urls = read_urls_from_file(file_path)
    addy_found=0

    for document_list_url in urls:
        try:
            # Step 2: Fetch the document list page
            soup = fetch_document_list_page(document_list_url)
            
            # Step 3: Find the Summons + Complaint link
            summons_link = find_summons_link(soup)
            
            # Step 4: Fetch the Summons + Complaint PDF
            summons_pdf = fetch_summons_pdf(summons_link)
            
            # Step 5: Extract the defendant's address from the PDF and print it
            defendant_address = extract_defendant_address(summons_pdf)
            if defendant_address:
                print(f"Defendant's Address: {defendant_address}")
                addy_found= addy_found+1
            else:
                print("[INFO] 'DEF1' line not found in this document.")
        
        except Exception as e:
            print(str(e))
    print(addy_found)

if __name__ == "__main__":
    # Start the main process
    print("[INFO] Starting the case lookup process...")
    
    main()
    
    print("[INFO] Process completed.")
