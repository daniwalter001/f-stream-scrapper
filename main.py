import json
from playwright.sync_api import sync_playwright
from selectolax.parser import HTMLParser
import urllib.parse
import time
import requests


host = "https://french-stream.gg/serie/"


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
        # page.goto(url=list[show_choice-1]["url"],
        #           wait_until="domcontentloaded", timeout=100000)

        res = requests.get(list[show_choice-1]["url"])
        parseSerieChoiceHTMLToEps(res.text)
    except AssertionError:
        print("Mauvais choix.............Ah oui!\n")


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
            urls = [{i.text().strip(): i.attributes["href"]}
                    for i in elt.css("ul.btnss li > a")]

            if 'VF' in title:
                episodes["vf"].append({
                    title: urls
                })
            elif "VOSTFR" in title:
                episodes["vostfr"].append({
                    title: urls
                })

    for i in episodes["vf"]:
        print(i)
        print("---------")

    for i in episodes["vostfr"]:
        print(i)
        print("---------")


def search(keyword):

    playload = {
        "do": "search",
        "subaction": "search",
        "story": keyword
    }

    headers = {"Content-Type": "application/x-www-form-urlencoded"}

    res = requests.post(host, data=playload, headers=headers)

    search_results = htmlDataParser(res.text)

    askToChooseShow(search_results)


def getCatalogue():
    with sync_playwright() as pw:
        results = []

        browser = pw.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(url=host, wait_until="domcontentloaded", timeout=100000)

        last_page_node = page.locator("span.navigation a:last-child")
        # last_page = int(last_page_node.text_content())

        page_th = 1
        while page_th <= 1:
            print(f"Fethcing from page {page_th}... ")
            time.sleep(1)
            page.goto(url=urllib.parse.urljoin(host, f"page/{page_th}"),
                      wait_until="domcontentloaded", timeout=100000)

            results.extend(htmlDataParser(page.content()))

            page_th = page_th+1
        askToChooseShow(results)


def main():
    menu = ["Get Catalogue", "Search", "Exit"]

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
    main()
    # search("The big bang")
