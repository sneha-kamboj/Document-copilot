from bs4 import BeautifulSoup

PATH = r"C:\Users\Dell\OneDrive\Attachments\Desktop\Projects\document-copilot\downloads\AAPL\2021\aapl-20210925.htm"

soup = BeautifulSoup(open(PATH,encoding="utf-8",errors="ignore").read(),"lxml")
#
# print("Tables:",len(soup.find_all("table")))
# print("p/div:",len(soup.find_all(["p","div"])))
# print("\nFirst 500 characters:\n")
# print(soup.get_text(" ", strip=True)[:500])

for tag in soup.find_all():
	if ":" in tag.name:
		print(tag.name)
		print(tag.attrs)
		print(tag.get_text(strip=True)[:50])
		print("-" * 50)