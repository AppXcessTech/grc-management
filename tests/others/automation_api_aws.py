import os
import requests
from bs4 import BeautifulSoup

BASE_URL = "https://docs.aws.amazon.com/boto3/latest/reference/services"
INPUT_FILE = "config_api_call_aloone.txt"
OUTPUT_DIR = "response_syntax"

os.makedirs(OUTPUT_DIR, exist_ok=True)


def extract_response_syntax(url):
    r = requests.get(url, timeout=30)
    r.raise_for_status()

    soup = BeautifulSoup(r.text, "html.parser")

    # Find the "Response Syntax" heading
    heading = soup.find(
        lambda tag: tag.name in ("h2", "h3")
        and "Response Syntax" in tag.get_text(strip=True)
    )

    if heading is None:
        return None

    # Find the first <pre> after the heading
    pre = heading.find_next("pre")

    if pre is None:
        return None

    return pre.get_text()


current_service = None

with open(INPUT_FILE) as f:
    for line in f:
        line = line.strip()

        # Blank line -> next line is a new service
        if not line:
            current_service = None
            continue

        if current_service is None:
            current_service = line
            continue

        api = line
        url = f"{BASE_URL}/{current_service}/client/{api}.html"

        print(f"Processing {current_service}.{api}")

        try:
            response_syntax = extract_response_syntax(url)

            if response_syntax is None:
                print("  -> Response Syntax not found")
                continue

            service_dir = os.path.join(OUTPUT_DIR, current_service)
            os.makedirs(service_dir, exist_ok=True)

            outfile = os.path.join(service_dir, f"{api}.txt")

            with open(outfile, "w") as out:
                out.write(response_syntax)

            print(f"  -> Saved to {outfile}")

        except Exception as e:
            print(f"  -> ERROR: {e}")
