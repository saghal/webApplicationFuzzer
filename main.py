from typing import Counter
from bs4 import BeautifulSoup as bs
from pprint import pprint
import argparse
import requests
from urllib.parse import urlparse, urljoin
from bs4 import BeautifulSoup
import colorama
import time
currSession = requests.Session()
currSession.headers["User-Agent"] = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.106 Safari/537.36"
# init the colorama module
colorama.init()

GREEN = colorama.Fore.GREEN
GRAY = colorama.Fore.LIGHTBLACK_EX
RESET = colorama.Fore.RESET
YELLOW = colorama.Fore.YELLOW


def Login(username, password, url, form_details):
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
    inputss = []
    inputs = []
    tempInput = {}

    for input_tag in form.find_all("input"):

        for key in input_tag.attrs:
            k = key
            val = input_tag.attrs[key]
            #print(k," : ",val)
            tempInput[k] = val

        inputss.append(tempInput.copy())
        tempInput.clear()
        if input_tag.attrs.get("type", "text") is not None:
            input_type = input_tag.attrs.get("type", "text")
        else:
            input_type = None

        if input_tag.attrs.get("name") is not None:
            input_name = input_tag.attrs.get("name")
        else:
            input_name = None

        if input_tag.attrs.get("value") is None:
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
        """    textarea = []
    tempTextarea = {}

    for textarea_tag in form.find_all("textarea"):
        for key in textarea_tag.attrs:
            k = key
            val = textarea_tag.attrs[key]
            #print(k, " : ", val)
            tempTextarea[k] = val

        textarea.append(tempTextarea.copy())
        tempTextarea.clear()
        """
    #print(textarea)
    details["action"] = action
    details["method"] = method
    details["inputs"] = inputss
    #details["textarea"] = textarea
#    print("print detailllllllllllls: ",details)
    if loginCheck[0] == True and loginCheck[1] == True and loginCheck[2] == True:
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
    soup = BeautifulSoup(currSession.get(url).content,
                         "html.parser", from_encoding="iso-8859-1")
    for a_tag in soup.findAll("a"):
        href = a_tag.attrs.get("href")
        if href == "" or href is None or (href.lower().find('logout') != -1) or (href.lower().find('exit') != -1) or (href.lower().find('signout') != -1) or (href.lower().find('security') != -1) or (href.lower().find('level') != -1):
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


def submit_form(form_details, url, value):
    """
    Submits a form given in `form_details`
    Params:
        form_details (list): a dictionary that contain form information
        url (str): the original URL that contain that form
        value (str): this will be replaced to all text and search inputs
    Returns the HTTP Response after form submission
    """
    # construct the full URL (if the url provided in action is relative)
    target_url = urljoin(url, form_details["action"])
    # get the inputs
    inputs = form_details["inputs"]
    #textareas = form_details["textarea"]
    data = {}
    #print(inputs)
    for input in inputs:
        # replace all text and search values with `value`
        if input["type"] == "text" or input["type"] == "search":
            """            if input["maxlength"] is not None:
                            if int(input["maxlength"]) < len(value) :
                                input["value"] = int(input["maxlength"]) * "A"
                        else:
            """
            input["value"] = value

        if input.get("name") is None:
            input_name = None
        else:
            input_name = input.get("name")

        input_value = input.get("value")
        #print(input_name, " : ",input_value)
        if input_name and input_value:
            # if input name and value are not None,
            # then add them to the data of form submission

            data[input_name] = input_value

    if form_details["method"] == "post":
        return currSession.post(target_url, data=data)
    else:
        return currSession.get(target_url, params=data)


def scan_xss(url, level):
    forms = get_all_forms(url)
    print(f"[+] Detected {len(forms)} forms on {url}")
    detectForm = [False]*len(forms)
    if level == 1:
        file1 = open('xss-payload-list-low.txt', 'r')
        Lines = file1.readlines()
        file1.close()
    else:
        file1 = open('xss-payload-list-high.txt', 'r')
        Lines = file1.readlines()
        file1.close()

    is_vulnerable = False
    for line in Lines:
        temp = 0
        for checkForm in detectForm:
            if checkForm == True:
                temp = temp + 1

        if temp == len(forms):
            break
        # iterate over all forms
        count = 0
        for form in forms:
            if detectForm[count] == True:
                continue
            form_details, x = get_form_details(form)
            content = submit_form(form_details, url, line).content.decode()
            if line in content:
                detectForm[count] = True
                print(f"[+] XSS Detected on {url}")
                print(f"[*] Form details:")
                pprint(form_details)
                f = open("report.txt", "a")
                f.write("#"*100)
                f.write("\n** XSS ATTACK **\n")
                f.write("\npath: ")
                f.write(url)
                f.write("\n")
                f.write(str(form_details))
                f.write("#"*100)

                f.close()

                is_vulnerable = True
            count = count + 1
    return is_vulnerable


def scan_HTMLI(url):
    forms = get_all_forms(url)
    print(f"[+] Detected {len(forms)} forms on {url}")
    detectForm = [False]*len(forms)
    file1 = open('html-payload.txt', 'r')
    Lines = file1.readlines()
    file1.close()

    is_vulnerable = False
    for line in Lines:
        temp = 0
        for checkForm in detectForm:
            if checkForm == True:
                temp = temp + 1

        if temp == len(forms):
            break
        # iterate over all forms
        count = 0
        for form in forms:
            if detectForm[count] == True:
                continue
            form_details, x = get_form_details(form)
            content = submit_form(form_details, url, line).content.decode()
            if line in content:
                detectForm[count] = True
                print(f"[+] XSS Detected on {url}")
                print(f"[*] Form details:")
                pprint(form_details)
                f = open("report.txt", "a")
                f.write("#"*100)
                f.write("\n** HTML injection **\n")
                f.write("\npath: ")
                f.write(url)
                f.write("\n")
                f.write(str(form_details))
                f.write("#"*100)

                f.close()

                is_vulnerable = True
            count = count + 1
    return is_vulnerable


def is_vulnerable(response):
    """A simple boolean function that determines whether a page 
    is SQL Injection vulnerable from its `response`"""
    errors = {
        # MySQL
        "you have an error in your sql syntax;",
        "warning: mysql",
        # SQL Server
        "unclosed quotation mark after the character string",
        # Oracle
        "quoted string not properly terminated",
    }
    for error in errors:
        # if you find one of these errors, return True
        if error in response.content.decode().lower():
            return True
    # no error detected
    return False


def scan_sql_injection(url):
    # test on URL
    for c in "\"'":
        new_url = f"{url}{c}"
        res = currSession.get(new_url)
        if is_vulnerable(res):
            print("[+] SQL Injection vulnerability detected, link:", new_url)
            return
    forms = get_all_forms(url)
    print(f"[+] Detected {len(forms)} forms on {url}.")
    for form in forms:
        form_details, x = get_form_details(form)
        for c in "\"'":
            data = {}
            for input_tag in form_details["inputs"]:
                if input_tag.get("value") or input_tag["type"] == "hidden":
                    try:
                        data[input_tag["name"]] = input_tag["value"] + c
                    except:
                        pass
                elif input_tag["type"] != "submit":
                    data[input_tag["name"]] = f"test{c}"
            url = urljoin(url, form_details["action"])
            if form_details["method"] == "post":
                res = currSession.post(url, data=data)
            elif form_details["method"] == "get":
                res = currSession.get(url, params=data)
            # test whether the resulting page is vulnerable
            if is_vulnerable(res):
                print("[+] SQL Injection vulnerability detected, link:", url)
                print("[+] Form:")
                pprint(form_details)
                f = open("report.txt", "a")
                f.write("#"*100)
                f.write("\n** SQL injection **\n")
                f.write("\npath: ")
                f.write(url)
                f.write("\n")
                f.write(str(form_details))
                f.write("#"*100)

                f.close()

                break


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
    print("[+] Total crawled URLs:", 1000)
    options = 1
    while options > 0:
        print("*"*100, "\n", "*"*99)
        options = int(
            input("Choose Attack:\n1.XSS\n2.SQL injection\n3.HTML injection\n0.Exit\n"))
        if options == 0:
            break
        elif options == 1:
            level = int(input("choose level:\n1.low\n2.high\n"))
            if level == 1 or level == 2:
                for link in internal_urls:
                    scan_xss(link, level)
            else:
                print("choose right Level")
                continue
        elif options == 2:
            for link in internal_urls:
                scan_sql_injection(link)
        elif options == 3:
            for link in internal_urls:
                scan_HTMLI(link)

        else:
            continue
