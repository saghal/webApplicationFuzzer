from bs4 import BeautifulSoup as bs
from pprint import pprint
import argparse
import requests
from urllib.parse import urlparse, urljoin
from bs4 import BeautifulSoup
import colorama
currSession = requests.Session()
currSession.headers["User-Agent"] = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.106 Safari/537.36"

# init the colorama module
colorama.init()

GREEN = colorama.Fore.GREEN
GRAY = colorama.Fore.LIGHTBLACK_EX
RESET = colorama.Fore.RESET
YELLOW = colorama.Fore.YELLOW

def Login(username, password ,url , form_details):
    target_url = urljoin(url, form_details["action"])
    # get the inputs
    inputs = form_details["inputs"]
    data = {}
    for input in inputs:
        # replace all text and search values with `value`
        if input["type"] == "text":
            input["value"] = username
        if input["type"] == "password":
            input["value"] = password

        input_value = input.get("value")
        input_name = input.get("name")
        if input_name and input_value:
            # if input name and value are not None,
            # then add them to the data of form submission
            data[input_name] = input_value

    if form_details["method"] == "post":
        result = currSession.post(target_url, data=data)
    else:
        result = currSession.get(target_url, params=data)

    print("this place: ", result.url)
    return result.url

def get_all_forms(url):
    """Given a `url`, it returns all forms from the HTML content"""
    soup = bs(currSession.get(url).content, "html.parser")
    return soup.find_all("form")


def get_form_details(form):
    """
    This function extracts all possible useful information about an HTML `form`
    """
    loginCheck = [False]*3

    details = {}
    # get the form action (target url)
    if form.attrs.get("action") is not None:
        action = form.attrs.get("action").lower()
    else:
        action = None
    # get the form method (POST, GET, etc.)
    if form.attrs.get("method") is not None:
        method = form.attrs.get("method", "get").lower()
    else:
        method = None
    inputs = []

    for input_tag in form.find_all("input"):
        if input_tag.attrs.get("type", "text") is not None:
            input_type = input_tag.attrs.get("type", "text")
        else:
            input_type = None

        if input_tag.attrs.get("name") is not None:
            input_name = input_tag.attrs.get("name")
        else:
            input_name = None

        if input_tag.attrs.get("value") == None:
            inputs.append({"type": input_type, "name": input_name})
        else:
            input_value = input_tag.attrs.get("value")
            inputs.append(
                {"type": input_type, "name": input_name, "value": input_value})

        if input_type == "text":
            loginCheck[0] = True
        elif input_type == "password":
            loginCheck[1] = True
        elif input_type == "submit":
            loginCheck[2] = True

    # put everything to the resulting dictionary
    details["action"] = action
    details["method"] = method
    details["inputs"] = inputs

    if loginCheck[0] == True and loginCheck[1] == True and loginCheck[2] == True:
        print(loginCheck)
        return details, True
    else:
        return details, False


# initialize the set of links (unique links)
internal_urls = set()
external_urls = set()

total_urls_visited = 0


def is_valid(url):
    """
    Checks whether `url` is a valid URL.
    """
    parsed = urlparse(url)
    return bool(parsed.netloc) and bool(parsed.scheme)
def is_logout(url):
    parsed = urlparse(url)
    print(parsed)

def get_all_website_links(url):
    """
    Returns all URLs that is found on `url` in which it belongs to the same website
    """
    # all URLs of `url`
    urls = set()
    # domain name of the URL without the protocol
    domain_name = urlparse(url).netloc
    soup = BeautifulSoup(currSession.get(url).content, "html.parser")
    for a_tag in soup.findAll("a"):
        href = a_tag.attrs.get("href")
        
        if href == "" or href is None or (href.lower().find('logout') != -1) or (href.lower().find('exit') != -1) or (href.lower().find('signout') != -1):
            # href empty tag
            continue
        # join the URL if it's relative (not absolute link)
        href = urljoin(url, href)
        parsed_href = urlparse(href)
        # remove URL GET parameters, URL fragments, etc.
        href = parsed_href.scheme + "://" + parsed_href.netloc + parsed_href.path
        if not is_valid(href):
            # not a valid URL
            continue
        if href in internal_urls:
            # already in the set
            continue
        if domain_name not in href:
            # external link
            if href not in external_urls:
                print(f"{GRAY}[!] External link: {href}{RESET}")
                external_urls.add(href)
            continue
        print(f"{GREEN}[*] Internal link: {href}{RESET}")
        urls.add(href)
        internal_urls.add(href)
    return urls


def crawl(url, max_urls=30):
    """
    Crawls a web page and extracts all links.
    You'll find all links in `external_urls` and `internal_urls` global set variables.
    params:
        max_urls (int): number of max urls to crawl, default is 30.
    """
    global total_urls_visited
    total_urls_visited += 1
    print(f"{YELLOW}[*] Crawling: {url}{RESET}")
    links = get_all_website_links(url)
    for link in links:
        if total_urls_visited > max_urls:
            break
        crawl(link, max_urls=max_urls)


if __name__ == "__main__":
    url = input("Enter your URL: ")
    flag = False
    forms = get_all_forms(url)
    # iteratte over forms
    for i, form in enumerate(forms, start=1):
        form_details, loginStatus = get_form_details(form)
        print("="*50, f"form #{i}", "="*50)
        pprint(form_details)

        if loginStatus == True:
            print("="*50, "Login form detected", "="*50)
            username = input("Enter Username and password\nUsername: ")
            password = input("password: ")
            url = Login(username, password, url, form_details)
            flag = True
            break

    if flag == False:
        print("*"*50, "Login form not detected", "*"*50)

    crawl(url, max_urls=1000)

    print("[+] Total Internal links:", len(internal_urls))
    print("[+] Total External links:", len(external_urls))
    print("[+] Total URLs:", len(external_urls) + len(internal_urls))
    print("[+] Total crawled URLs:", 100)

    for i in internal_urls:
        print(i)


"""print("="*50, f"form #{i}", "="*50)
pprint(form_details)
"""
