# Webtoon
This is a scrapper/downloader for https://www.webtoons.com/
they do a wonderfull work but i only read them in the train when going to work.

So i made this scrapper that pack them to .cbz files
it uses `BeautifulSoup 4` and `lxml` to parse .html files from the remote server,


## Requirements
You need `python3` and `neo4j` graph database.
then just run

```shell
virtualenv venc
source ./venv/bin/activate
pip install -r requirements.txt
```

## Usage
```shell
export PASSWORD='database password'
./webtoons.py --help
```
