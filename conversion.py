"""
Converts the companies Google sheet to the markdown formatting of the repository readme.
Due to the manual process of the information gathering on the companies & complex markdown formatting in the github
readme, the company data is managed in a Google sheet. This script automatically converts and formats it.

Add "--check-urls" to check for broken company website URLs.
"""

from typing import List
from urllib.request import Request, urlopen
from urllib.error import URLError
import argparse

import pandas as pd
from tqdm import tqdm


parser = argparse.ArgumentParser(
    description="Convert the csv to markdown, optionally check the website urls via --check-urls"
)
parser.add_argument(
    "--check-urls",
    default=False,
    action="store_true",
    help="Check the company website urls.",
)
args = parser.parse_args()


def check_urls(urls: List[str]):
    # Include basic header info to avoid scraping blocks
    headers = {"User-Agent": "Mozilla/5.0"}

    for url in tqdm(urls):
        req = Request(url, headers=headers)
        try:
            urlopen(req)
        except (URLError, ValueError) as e:
            # Do something when request fails
            print("Broken URL - ", url, e)


def reformat(df):
    categories = {
        "Earth Observation": ":earth_americas:",
        "UAV / Aerial": ":airplane:",
        "GIS / Spatial Analysis": ":globe_with_meridians:",
        "Digital Farming": ":seedling:",
        "Webmap / Cartography": ":world_map:",
        "Satellite Operator": ":artificial_satellite:",
    }
    df = df.replace({"Category": categories})

    df["Company"] = df.apply(lambda x: f"[{x['Company']}]({x['Website']})", axis=1)
    df["Focus"] = df["Category"] + " " + df["Focus"]

    gmaps_url = "https://www.google.com/maps/search/"
    df["Address"] = df.apply(
        lambda x: "".join(y + "+" for y in x["Address"].split(" ")), axis=1
    )
    df["Address"] = df.apply(
        lambda x: f"[:round_pushpin: {x['City']}]({gmaps_url}{x['Address']})", axis=1
    )

    df = df.drop(["Website", "Category", "City", "Notes (ex-name)"], axis=1)

    return df


pdf = pd.read_csv("awesome-geospatial-companies - Companies A-Z.csv")
# display(pdf.head(1))
print(f"Unique companies: {pdf['Focus'].nunique()}")

if pdf.loc[:, pdf.columns != 'Notes (ex-name)'].isnull().values.any():
    print(pdf[pdf.loc[:, pdf.columns != 'Notes (ex-name)'].isnull().any(axis=1)])
    raise ValueError("Table contains NA values!!!")

if args.check_urls:
    check_urls(urls=pdf["Website"].values)

pdf = reformat(df=pdf)

chapter_string = ""
markdown_string = ""
for country in sorted(pdf.Country.unique()):
    df_country = pdf[pdf["Country"] == country]
    df_country = df_country.drop(["Country"], axis=1)

    country_emoji = {
        "china": "cn",
        "france": "fr",
        "germany": "de",
        "italy": "it",
        "south_korea": "kr",
        "spain": "es",
        "turkey": "tr",
        "uae": "united_arab_emirates",
        "usa": "us",
        "russia": "ru",
        "japan": "jp",
    }
    flag_emoji = country.lower()
    flag_emoji = flag_emoji.replace(" ", "_")
    if flag_emoji in list(country_emoji.keys()):
        flag_emoji = country_emoji[flag_emoji]

    repo_link = "https://github.com/chrieke/awesome-geospatial-companies#"
    chapter_link = (
        f"[:{flag_emoji}: {country}]({repo_link}{country.lower().replace(' ', '-')}-{flag_emoji})"
    )
    chapter_string = chapter_string + f"{chapter_link} - "

    markdown_string = (
        markdown_string
        + f"## :{flag_emoji}: {country} *({df_country.shape[0]})* \n"
        + f"{df_country.to_markdown(index=False)} \n\n "
    )

with open("Output.md", "w") as text_file:
    text_file.write(chapter_string + "\n\n" + markdown_string)
