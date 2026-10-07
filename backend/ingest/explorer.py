from bs4 import BeautifulSoup

PATH = r"C:\Users\Dell\OneDrive\Attachments\Desktop\Projects\document-copilot\downloads\AAPL\2021\aapl-20210925.htm"

with open(PATH, encoding="utf-8", errors="ignore") as f:
    html = f.read()

soup = BeautifulSoup(html, "xml")


print("Tables:", len(soup.find_all("table")))
print("Contexts:", len(soup.find_all("xbrli:context")))
print("Facts:", len(soup.find_all("ix:nonfraction")))

print("\n--- SAMPLE FACTS ---\n")

for tag in soup.find_all():
	print("NAME:", tag.get("name"))
	print("VALUE:", tag.get_text(strip=True))
	print("UNIT:", tag.get("unitRef"))
	print("CONTEXT:", tag.get("contextRef"))
	print("SCALE:", tag.get("scale"))