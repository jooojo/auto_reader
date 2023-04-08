import multiprocessing
import urllib.parse
from urllib.request import urlopen

import typer
from bs4 import BeautifulSoup
from tqdm import tqdm


# parse paper info from paper url
def parse_paper_info(url):
    with urlopen(url) as f:
        soup = BeautifulSoup(f.read(), "html.parser")
        title = soup.find("div", id="papertitle").get_text().strip()
        authors = soup.find("div", id="authors").get_text().strip()
        abstract = soup.find("div", id="abstract").get_text().strip()
        link = urllib.parse.urljoin(url, soup.find("a", string="pdf")["href"])
        return "\t".join([title, authors, link, abstract])


# parse paper lists from conference index page
def parse_paper_url(url):
    papers = []
    with urlopen(url) as f:
        soup = BeautifulSoup(f.read(), "html.parser")
        dl_data = soup.find_all("dl")
        data = dl_data[0]
        for dt in data.find_all("dt"):
            paper_link = urllib.parse.urljoin(url, dt.find("a")["href"])
            papers.append(paper_link)
    return papers


def get_cvf_paper_list(index_url, before18=False):
    if before18:
        return parse_paper_url(index_url)

    paper_list = []
    with urlopen(index_url) as f:
        soup = BeautifulSoup(f.read(), "html.parser")
        dl_data = soup.find("dl")
        for dd in dl_data.find_all("dd"):
            daily_url = urllib.parse.urljoin(index_url, dd.find("a")["href"])
            if "all" in daily_url:
                continue
            else:
                paper_list.extend(parse_paper_url(daily_url))
    return paper_list


# parse paper lists from conference index page
def parse_eccv(url, t=0):
    with urlopen(url) as f:
        soup = BeautifulSoup(f.read(), "html.parser")
        dl_data = soup.find_all("dl")
        data = dl_data[t]
        for dt in tqdm(data.find_all("dt")):
            paper_link = urllib.parse.urljoin(url, dt.find("a")["href"])
            yield paper_link


# eccv_url = 'http://www.ecva.net/papers.php'
# conference_list = parse_eccv(eccv_url, 0)
# with open(f'./data/ECCV2022.tsv', 'w') as outfile:
#    outfile.write("title\tauthors\tlink\tabstrct\n")
#    for i, paper in enumerate(conference_list):
#        outfile.write(f"{parse_paper_info(paper)}\n")

# conference_list = parse_eccv(eccv_url, 1)
# with open(f'./docs/ECCV2020.tsv', 'w') as outfile:
#    for i, paper in enumerate(conference_list):
#        outfile.write(f"{parse_paper_info(paper)}\n")
#
# conference_list = parse_eccv(eccv_url, 2)
# with open(f'./docs/ECCV2018.tsv', 'w') as outfile:
#    for i, paper in enumerate(conference_list):
#        outfile.write(f"{parse_paper_info(paper)}\n")

# conference_list = "CVPR2018,CVPR2019,ICCV2019,CVPR2020,CVPR2021"
# for conference in "ICCV2021".split(","):
#    conference_index = f"https://openaccess.thecvf.com/{conference}"
#    conference_list = get_cvf_paper_list(conference_index)
#
#    with open(f'../docs/{conference}.tsv', 'w') as outfile:
#        for i, paper in enumerate(conference_list):
#            outfile.write(f"{parse_paper_info(paper)}\n")


app = typer.Typer()


@app.command()
def crawler(
    confs: str = typer.Argument(..., help="conference list"),
    outfile: typer.FileTextWrite = typer.Argument(...),
    conf_index_url: str = "https://openaccess.thecvf.com/",
    num_workers: int = None
):
    for conference in confs.split(","):
        conference_index = f"{conf_index_url}{conference}"
        if int(conference[-4:]) < 2018:
            before18 = True
        else:
            before18 = False
        paper_list = list(get_cvf_paper_list(conference_index, before18))

        with multiprocessing.Pool(processes=num_workers) as pool:
            results = pool.imap_unordered(parse_paper_info, paper_list)
            for result in tqdm(results, total=len(paper_list)):
                outfile.write(f"{result}\n")


if __name__ == "__main__":
    app()
