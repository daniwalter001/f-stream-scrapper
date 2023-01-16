from playwright.sync_api import sync_playwright
from selectolax.parser import HTMLParser
import urllib.parse
import time


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


def main():
    with sync_playwright() as pw:
        results = []

        browser = pw.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(url=host, wait_until="domcontentloaded", timeout=100000)

        last_page_node = page.locator("span.navigation a:last-child")
        # last_page = int(last_page_node.text_content())

        page_th = 1
        while page_th <= 4:
            print(f"Fethcing from page {page_th}... ")
            time.sleep(1)
            page.goto(url=urllib.parse.urljoin(host, f"page/{page_th}"),
                      wait_until="domcontentloaded", timeout=100000)

            results.extend(htmlDataParser(page.content()))

            page_th = page_th+1

        for i, show in enumerate(results):
            print(" {}- {} ".format(i+1, show['title']))
        show_choice = int(input("\nVotre choix: "))

        page.goto(url=results[show_choice]["url"],
                  wait_until="domcontentloaded", timeout=100000)
        parseSerieChoiceHTMLToEps(page.content())


def parseSerieChoiceHTMLToEps(html_page):

    # episodes = {
    #     "vf": [],
    #     "vostfr": []
    # }

    html = HTMLParser(html_page)

    eps_nodes = html.css(
        "div.series-center div.fullsfeature > div")
    for elt in eps_nodes:
        if (elt.css_first("ul.btnss li > a") and elt.css_first("ul.btnss li > a").attributes['href'] and elt.css_first("span")):
            title = elt.css_first("span").text()
            urls = [{i.text(): i.attributes["href"]}
                    for i in elt.css("ul.btnss li > a")]
            print({
                "title": title,
                "urls": urls
            })


main()
