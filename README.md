# Cert_Fetcher
Fetch certificates from [crt.sh](https://crt.sh/) and [Facebook Certificate Transparency](https://developers.facebook.com/tools/ct/) by using public APIs

# dependency
- Python 3.x
- [requests](https://requests.readthedocs.io/en/master/)
- [BeautifulSoup](https://www.crummy.com/software/BeautifulSoup/bs4/doc/)
- [lxml](https://lxml.de/)
- [dateutil](https://pypi.org/project/python-dateutil/)
# Example
<a href="url"><img src="https://github.com/LinkWoong/Cert_Fetcher/blob/master/img/result.png" align="center" height="250" ></a>
# Usage
First clone this repo
```
git clone https://github.com/LinkWoong/Cert_Fetcher.git
cd ./Cert_Fetcher
```
Before running any script, please install requirement.txt first by using
```
pip install -r requirements.txt
```
or
```
pip3 install -r requrements.txt
```

## crtsh_fetcher.py
```
python3 crtsh_fetcher.py -d <domain-name> -s <path-for-saving-the-certs>
```
For example, if I'd like to retrieve certificates of domain **[www.google.com](www.google.com)** and stored it to my current directory **./**, just simply type
```
python3 crtsh_fetcher.py -d www.google.com -s .
```
or if you don't want to save the certs locally, just ignore the -s parameter
```
python3 crtsh_fetcher.py -d www.google.com
```

## Facebook_fetcher.py
```
python3 Facebook_fetcher.py -d <domain-name> -s <path-for-saving-the-certs>
```
For example, if I'd like to retrieve certificates of domain **[www.google.com](www.google.com)** and stored it to my current directory **./**, just simply type
```
python3 Facebook_fetcher.py -d www.google.com -s .
```
or if you don't want to save the certs locally, just ignore the -s parameter
```
python3 Facebook_fetcher.py -d www.google.com
```

## TODO
- Multithread
- Header Pool to avoid being locked down
- Google CT Monitor, Censys, SSL Mate
- Process domains in batches (like reading from .csv file)
