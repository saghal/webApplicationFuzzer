from bs4 import BeautifulSoup as bs
from pprint import pprint
import argparse
import requests
from urllib.parse import urlparse, urljoin
from bs4 import BeautifulSoup
import colorama
currSession = requests.Session()
currSession.headers["User-Agent"] = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.106 Safari/537.36"


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


if __name__ == "__main__":
    url = input("Enter your URL: ")

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
        else:
            print("not detected")

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
        
        print(data,target_url)
        if form_details["method"] == "post":
            result = currSession.post(target_url, data=data)
        else:
            result = currSession.get(target_url, params=data)

        print("this place: ", result.url)







"""print("="*50, f"form #{i}", "="*50)
pprint(form_details)
"""
