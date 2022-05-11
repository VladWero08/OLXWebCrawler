from bs4 import BeautifulSoup
import requests
import re
import json
import concurrent.futures

regexs = ['([oO]+u[aăle]*)',
          '([aA]+nvelop[aăe]+|[cC]+auci(?:ucuri+|oace+))', # VERIFICAT - anvelope
          '([cC]+artofi*|[mM]+orcovi*|[cC]+astrave(?:t|ți*)|[pP]+[aă]trunjel|[mM]+[aă]rar|[aA]+rdei+|[mM]+az[aă]re+|[[rR]+o[sș]+[ie]+|[gG]+ogo[sș]ari*|[cC]+eap[aăe]+|[lL]+eu[sș]tean)',
          '([Ff]+ruct(?:e*|u+l)|[Mm]+[eaă]r(?:e*l|u+l*)|[Pp]+[ae]r[aăe]+|[Bb]+anan[aăe]+|[Pp]+epen[ei]+|[Gg]+utuie*|[Pp]+run[aeă]+|[cC]+ais[aeă]+|[Pp]+ortocal[aeă]+)',
          '([pP]+orumb|[hH]+ri[sș]c[aă]+|[gG]+r[aîâ]u+|[oO]+(?:v[aă]|re*)z|[rR]+api[tț][aă]+)',
          '([Pp]+as[aă]r[ie]+|[gG][aă]in(?:[aă]+|i*(?:le)*)|[Pp]+orumbe[li]+|[rR]+a[tț][aăe]+|[gG]+[aâ]+[sș]+(?:te+|c[aă]+)|[Cc]+urcani*|[pP]+[aă]un[ui]*)',
          '([Vv]+ac[aăi]+|[Cc]+a[lui]+|[oO]+(?:a+i+e+|i+)|[cC]+apr[aăe]+|[Mm]+ie[li]+|[vV]+i[tț]e[li]+|[Ii]e(?:d|zi*)|[Ii]+epur[ei]+)',
          '([pP]+eșt[ei]+|[sșSȘ]+al[aă][ui]+|[cC]+ara[sș]i*|[cC]+rapi*|[bB]+ibani*|[sșSȘ]+tiuc[aăi]+)',
          '([uU]+tilaje*|[cC]+ombin(?:[aă]+|e+)|[pP]+lug(?:uri+)*|[cC]+ositoar[ei]+|(?:[tT]+racto|[cC]+ompacto|[eE]+xcavato|[mM]+iniexcavato)(?:r|are+))',
          '([lL]+apte+|[uU]+rd[aă]+|[Cc]+a[sș]|(?:[cC]+|[kK]+)h*efir|[iI]+aurt(?:e+|uri)*|[bB]+r[aîâ]+nz[aăe](?:turi+)*|[sS]+m[aîâ]+nt[aîâ]+n[aăe]+)']
# list of dictionaries that will be tranformed to json and transfered to the front-end
scraping_results = {"oua": [], "anvelope": [], "legume": [], "fructe": [],
                    "cereale": [], "pasari": [], "mamifere": [], "pesti": [],
                    "masini, utilaje & unelte": [], "lactate": [], "altele": []}

# generate all URLs of the 25 pages
pages_URL = ["https://www.olx.ro/d/anunturi-agricole/"]
for i in range(25):
    pages_URL.append("https://www.olx.ro/d/anunturi-agricole/" + "?page=" + str(i+1))

# for each page given, it returns an array of links
# to the articles posted on that page

def adOLXparser(page_link):
    # some OLX links have promoted pages from autovit,
    # pages that cannot be crawled, so we
    forbidden_text = re.compile("autovit")
    if len(forbidden_text.findall(page_link)) != 0:
        return False
    else:
        return True


def pageDescriptionGenerator(page_link):
    # for each ad posted we get its description
    html_text = requests.get(page_link).text
    soup = BeautifulSoup(html_text, "html.parser")
    return soup.find("div", {"class": "css-g5mtbi-Text"}).text

def matchedPageGenerator(page_link):
    global scraping_results
    pageDescription = pageDescriptionGenerator(page_link)
    scraping_items = scraping_results.items()
    isCategorized = False
    i = 0

    if adOLXparser(page_link) == True:
        for category in scraping_items:
            # we take the description and apply the regexs in order to find
            # in which subcategories we can include it( if possible)
            if len(re.findall(r'\b'+regexs[i]+r'\b',pageDescription)) != 0:
                # if we find any match, we will append it to the regex's dictionary that mathced it
                subsection_length = len(category[1])
                category[1].append({"id":str(subsection_length + 1), "link":page_link})
                isCategorized = True
            i += 1

    # if the link does not belong to any category, we put it in 'others' category
    if isCategorized == False:
        subsection_length = len(scraping_results[10])
        scraping_results[10].append({"id": str(subsection_length + 1), "link": page_link})

def pageAdsGenerator(page_link):
    # for each of the 25 pages displayed, we get the links to every ad
    pageADS = []
    html_text = requests.get(page_link).text
    soup = BeautifulSoup(html_text, "html.parser")
    for a in soup.select(".css-19ucd76 a"):
        pageADS.append("https://www.olx.ro" + a["href"])

    # multi-threading
    with concurrent.futures.ThreadPoolExecutor() as executor:
        executor.map(matchedPageGenerator, pageADS)

# multi-threading
with concurrent.futures.ThreadPoolExecutor() as executor:
    executor.map(pageAdsGenerator, pages_URL)

# our dictionary will be written inside a json file
# for front-end purposes
for i in scraping_results:
    print(scraping_results[i])

subcategory_json = json.dumps(scraping_results)
with open('subcategories.json', 'w') as output:
    json.dump(subcategory_json, output)




