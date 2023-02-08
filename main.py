from selectolax.parser import HTMLParser
import urllib.parse
import time
from seleniumbase import Driver
from seleniumbase import page_actions
import cfscrape
import re
import requests


# host = "https://french-stream.gg/serie/"
host = "https://streem.re/serie/"
cf_clearance = ''
headers = {
    "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/109.0.0.0 Safari/537.36"
}


def getCookie(url=host):
    try:
        print("Getting cf cookie...")
        driver = Driver(headless=False, uc=True)
        driver.get(url)
        page_actions.wait_for_element_visible(
            driver=driver, selector="a.logotype")
        cf = driver.get_cookie('cf_clearance')
        print("ok")
        return cf["value"]
    except:
        print("error getting cf cookie...retrying...")
        return getCookie()


def get(url=host):
    try:
        print("Get request...")
        driver = Driver(headless=True, uc=True)
        driver.get(url)
        page_actions.wait_for_element_visible(
            driver=driver, selector="a.logotype")
        print("ok")
        html = driver.page_source
        driver.quit()
        return html
    except:
        print("error getting request...retrying...")
        return get(url=url)


def post(url=host, data={}):
    try:
        print("Post request...")
        driver = Driver(headless=True, uc=True)
        dataString = urllib.parse.urlencode(data)
        driver.get(url)
        page_actions.wait_for_element_visible(
            driver=driver, selector="a.logotype")

        js = '''var xhr = new XMLHttpRequest();
            xhr.open('POST', \''''+url+'''\', false);
            xhr.setRequestHeader('Content-type', 'application/x-www-form-urlencoded');
            xhr.send(\''''+dataString+'''\');
            return xhr.response;'''
        result = driver.execute_script(js)
        driver.quit()
        return result
    except:
        print("error making post request...retrying...")
        return post(url=url, data=data)


def parseLecteurURL(type="", html=""):

    regex = r"sources: \[\"(https?:\/\/(?:www\.)?[-a-zA-Z0-9@:%._\+~#=]{1,256}\.[a-zA-Z0-9()]{1,6}\b(?:[-a-zA-Z0-9()@:%_\+.~#?&\/=]*))\"\]"

    print(re.search(regex, html).groups() or "Actually None")


def htmlDataParser(html_page):
    results_per_page = []

    html = HTMLParser(html_page)

    data = html.css("div.short div.short-in.nl")

    for item in data:
        show = {
            "title": item.css_first("div.short-title").text(),
            "url": item.css_first("a.short-poster").attributes["href"]
        }
        results_per_page.append(show)

    return results_per_page


def askToChooseShow(list):
    for i, show in enumerate(list):
        print(" {}- {} ".format(i+1, show['title']))
    show_choice = int(input("\nVotre choix: "))
    try:
        assert show_choice > 0
        res = get(list[show_choice-1]["url"])
        parseSerieChoiceHTMLToEps(res)
    except AssertionError:
        print("Mauvais choix.............Ah oui!\n")


def parseEpData(data):
    print(data["title"])
    print('-----------------------')
    for i, url in enumerate(data['url']):
        print(f"{i+1}- {url['source']}")

    choix_source = int(input("Choix de source: "))

    try:
        assert choix_source <= len(data['url'])

        print(data['url'][choix_source-1]["url"])

        res = requests.get(url=data['url'][choix_source-1]["url"])
        parseLecteurURL(
            html=res.text, type=data['url'][choix_source-1]["source"])

    except AssertionError:
        print("Oh mais quand même hein...")


def askToChooseEps(list):
    print('VF / VOSTFR :')
    print('1- VF')
    print('2- VOSTFR')

    choix_lang = int(input("Choix: "))

    try:
        assert choix_lang > 0
        assert choix_lang < 3

        lang = ["vf", "vostfr"][choix_lang-1]

        print(f'{lang.upper()} ----')
        for i, ep in enumerate(list[lang]):
            title = ep.get("title")
            print("{}- {} ".format(i+1, str(title)))
        ep_choice = int(input("\nVotre choix: "))

        parseEpData(list[lang][ep_choice])

    except AssertionError:
        pass


def parseSerieChoiceHTMLToEps(html_page):

    episodes = {
        "vf": [],
        "vostfr": []
    }

    html = HTMLParser(html_page)

    eps_nodes = html.css(
        "div.series-center div.fullsfeature > div")
    for elt in eps_nodes:
        if (elt.css_first("ul.btnss li > a") and elt.css_first("ul.btnss li > a").attributes['href'] and elt.css_first("span")):
            title = elt.css_first("span").text()
            urls = [{"source": i.text().strip(),
                     "url": i.attributes["href"]
                     } for i in elt.css("ul.btnss li > a")]

            if 'VF' in title:
                episodes["vf"].append({
                    'title': title,
                    'url': urls,
                })
            elif "VOSTFR" in title:
                episodes["vostfr"].append({
                    'title': title,
                    'url': urls,
                })

    askToChooseEps(episodes)


def search(keyword):

    playload = {
        "do": "search",
        "subaction": "search",
        "story": keyword
    }
    res = post(url=host, data=playload)
    search_results = htmlDataParser(res)
    askToChooseShow(search_results)


def getCatalogue():
    results = []
    cf = cfscrape.create_scraper()

    # last_page_node = page.locator("span.navigation a:last-child")
    # last_page = int(last_page_node.text_content())

    page_th = 1
    while page_th <= 1:
        print(f"Fethcing from page {page_th}...")
        time.sleep(1)
        _url = urllib.parse.urljoin(host, f"page/{page_th}")
        res = get(url=_url)

        results.extend(htmlDataParser(res))

        page_th = page_th+1

    cf.close()
    askToChooseShow(results)


def main():
    # print(cf_clearance)
    menu = ["Get Catalogue", "Get a specific page", "Search", "Exit"]

    while True:
        try:
            for i, el in enumerate(menu):
                print(" {}- {} ".format(i+1, el))
            choice = input("\n Votre choix de menu: ")

            if choice == "1":
                getCatalogue()
            elif choice == "2":
                keyword = str(input("Enter keyword: "))
                search(keyword)
            elif choice == "3":
                keyword = str(input("Enter keyword: "))
                search(keyword)
            elif choice == "0":
                print("Exiting...")
                exit()
            else:
                continue
        except KeyboardInterrupt:
            print("Exiting...")
            # break
            exit()


if __name__ == "__main__":
    cf_clearance = ""
    # cf_clearance = getCookie()
    main()
    # search("The big bang")
