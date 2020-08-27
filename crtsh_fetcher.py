import requests
import json
import argparse
import os
import lxml
import datetime

from bs4 import BeautifulSoup
from dateutil.parser import parse

class crtsh_fetcher(object):
    def retrieve_cert(self, domain, wildcard=True, exprired=True) -> {}:
        """ Return example
        {
            "issuer_ca_id": 16418,
            "issuer_name": "C=US, O=Let's Encrypt, CN=Let's Encrypt Authority X3",
            "name_value": "hatch.uber.com",
            "min_cert_id": 325717795,
            "min_entry_timestamp": "2018-02-08T16:47:39.089",
            "not_before": "2018-02-08T15:47:39"
        }
        """
        print("Downloading certificates from " + domain)
        api_url = "https://crt.sh/?q={}&output=json"
        if not exprired:
            api_url =  api_url + "&exclude=expried"
        if wildcard and "%" not in domain:
            domain = "%.{}".format(domain)
        url = api_url.format(domain)
        
        crawler_header = 'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:40.0) Gecko/20100101 Firefox/40.1'
        http_request = requests.get(url, headers={'User-Agent': crawler_header})
        
        if http_request.ok:
            try:
                response = http_request.content.decode('utf-8')
                certs = json.loads(response)
                return certs
            except Exception as err:
                print("Error during the request")
        else:
            print("Exception during HTTP Requests")
        return None
    
    def dedup(self, certs) -> set():
        """
        Return unique cert id 
        crt.sh returns Precertificate and Leaf certificate for a specific domain
        """
        unique_id = set()
        for cert in certs:
            for key, value in cert.items():
                if key == "id":
                    unique_id.add(value)
        return unique_id
    
    def get_cert_detail(self, id, type="sha1") -> {}:
        http_request = requests.get(url="https://crt.sh/", params={'id': id})
        try:
            beautifulSoup = BeautifulSoup(http_request.text, 'lxml')
            table = beautifulSoup.find_all('table')[1]
            cert = {}
            content = table.find_all('tr', recursive=False)
            
            if len(content) < 6:
                return None
            
            cert['id'] = content[0].td.text
            cert['sha256'] = content[4].find("th", text="SHA-256").find_next_sibling("td").text
            cert['sha1'] = content[4].find("th", text="SHA-1").find_next_sibling("td").text
            certinfo = str(content[5].td)[60:-6].split("<br/>")
            
            i = 0
            while i < len(certinfo):
                if "Version:" in certinfo[i]:
                    cert['version'] = certinfo[i].strip().split("\xa0")[1]
                if "Serial\xa0Number:" in certinfo[i]:
                    # Size of serial may change
                    ends = certinfo[i][25:].find('"')
                    cert['serial'] = certinfo[i][25:25+ends]
                if "Signature\xa0Algorithm:" in certinfo[i]:
                    if 'signature_algorithm' in cert.keys():
                        signature = ""
                        i += 1
                        while certinfo[i].startswith("\xa0\xa0\xa0\xa0\xa0\xa0\xa0\xa0\xa0"):
                            signature += certinfo[i][9:]
                            i += 1
                        i -= 1
                        cert['signature'] = signature.replace(":", "")
                    else:
                        cert['signature_algorithm'] = certinfo[i].split(":")[1].strip()
                if ">Issuer:</a>" in certinfo[i]:
                    cert['issuer'] = {'id': certinfo[i].split('"')[1][6:]}
                    i += 1
                    while certinfo[i].startswith('\xa0\xa0\xa0\xa0\xa0\xa0\xa0\xa0\xa0\xa0\xa0\xa0'):
                        split = certinfo[i].split("=")
                        cert['issuer'][split[0].strip()] = split[1].strip().replace('\xa0', ' ')
                        i += 1
                    i -= 1
                if "\xa0Not\xa0Before:" in certinfo[i]:
                    cert['not_before'] = parse(certinfo[i][24:])
                if "\xa0Not\xa0After\xa0:" in certinfo[i]:
                    cert['not_after'] = parse(certinfo[i][24:])
                if "\xa0Subject:" in certinfo[i]:
                    cert['subject'] = {}
                    i += 1
                    while certinfo[i].startswith('\xa0\xa0\xa0\xa0\xa0\xa0\xa0\xa0\xa0\xa0\xa0\xa0'):
                        split = certinfo[i].split("=")
                        cert['subject'][split[0].strip()] = split[1].strip().replace('\xa0', ' ')
                        i += 1
                    i -= 1
                if "Subject\xa0Public\xa0Key\xa0Info:</a>" in certinfo[i]:
                    cert["publickey"] = {'sha256': certinfo[i].split("=")[2][:64]}
                if "Public\xa0Key\xa0Algorithm" in certinfo[i]:
                    cert["publickey"]["algorithm"] = certinfo[i].split(":")[1].strip()
                if "\xa0Public-Key:\xa0(" in certinfo[i]:
                    cert["publickey"]["size"] = int(certinfo[i].split("(")[1].split("\xa0")[0])
                if "\xa0Modulus:" in certinfo[i]:
                    modulus = ""
                    i += 1
                    while certinfo[i].startswith("\xa0\xa0\xa0\xa0\xa0\xa0\xa0\xa0\xa0\xa0\xa0\xa0\xa0\xa0\xa0\xa0\xa0\xa0\xa0\xa0"):
                        modulus += certinfo[i][20:]
                        i += 1
                    cert['publickey']['modulus'] = modulus.replace(":", "")
                    i -= 1
                if "Exponent:" in certinfo[i]:
                    cert["publickey"]["exponent"] = certinfo[i][26:].split("\xa0")[0]
                if "X509v3\xa0extensions:" in certinfo[i]:
                    cert["extensions"] = {}
                if "\xa0Subject\xa0Alternative\xa0Name:" in certinfo[i]:
                    cert["extensions"]["alternative_names"] = []
                    i += 1
                    while certinfo[i].startswith("\xa0\xa0\xa0\xa0\xa0\xa0\xa0\xa0\xa0\xa0\xa0\xa0\xa0\xa0\xa0\xa0DNS:"):
                        cert["extensions"]["alternative_names"].append(certinfo[i][20:].strip())
                        i += 1
                    i -= 1
                if "X509v3\xa0Basic\xa0Constraints:\xa0" in certinfo[i]:
                    i += 1
                    cert["extensions"]["basic_constraints"] = ("CA:FALSE" not in certinfo[i])
                if "X509v3\xa0Key\xa0Usage:" in certinfo[i]:
                    cert["extensions"]["key_usage"] = {
                        "critical": ("Usage:\xa0critical" in certinfo[i])
                    }
                    i += 1
                    cert["extensions"]["key_usage"]["usage"] = [a.strip().replace("\xa0", " ") for a in certinfo[i].split(",")]
                if "X509v3\xa0CRL\xa0Distribution\xa0Points:" in certinfo[i]:
                    i += 3
                    cert["extensions"]["crl_distribution"] = {"url": certinfo[i].split("URI:")[1].strip()}
                if "X509v3\xa0Extended\xa0Key\xa0Usage:" in certinfo[i]:
                    i += 1
                    cert["extensions"]["extended_key_usage"] = {"usage": [a.strip().replace("\xa0", " ") for a in certinfo[i].split(",")]}
                if "X509v3\xa0Authority\xa0Key\xa0Identifier:" in certinfo[i]:
                    i += 1
                    cert["extensions"]["authority_key_identifier"] = certinfo[i][22:].replace(":", "")
                if "X509v3\xa0Subject\xa0Key\xa0Identifier:" in certinfo[i]:
                    i += 1
                    cert["extensions"]["subject_key_identifier"] = certinfo[i][16:].replace(":", "")
                if "Authority\xa0Information\xa0Access:" in certinfo[i]:
                    cert["extensions"]["authority_information_access"] = {}
                    i += 1
                    while certinfo[i].startswith("\xa0\xa0\xa0\xa0\xa0\xa0\xa0\xa0\xa0\xa0\xa0\xa0\xa0\xa0\xa0\xa0"):
                        split = certinfo[i].split("\xa0-\xa0")
                        cert["extensions"]["authority_information_access"][split[0].strip().replace("\xa0", " ")] = split[1].strip()
                        i += 1
                    i -= 1
                # Warning : does not parse all the X509 extensions
                i += 1
        except BaseException:
            print("Exception during HTTP GET Requests")
        return cert
        
def datetime_handler(x):
    if isinstance(x, datetime.datetime):
        return x.isoformat()
    raise TypeError("Unknown type")

def main():
    parser = argparse.ArgumentParser(description="Arg parser for running this crawler")
    parser.add_argument('-d', dest='domain', action='store', help="domain name")
    parser.add_argument('-s', dest='save', action='store', help='destination directory for saving the certificates')
    
    args = parser.parse_args()
    cralwer = crtsh_fetcher()
    certs = []
    certs_detail = {}
    
    try:
        if args.domain:
            certs = cralwer.retrieve_cert(args.domain, True, True)
            
            print("Before dedup contains %d" % len(certs))
            unique_id = cralwer.dedup(certs)
            print("After dedup contains %d" % len(unique_id))
            
        if args.save:
            for id in unique_id:
                certs_detail[id] = cralwer.get_cert_detail(id)
            # print("Save path is " + args.save)
            if certs is None or len(certs_detail) == 0:
                print("Current result is empty")
            elif not os.path.exists(args.save):
                os.mkdir(args.save)
                with open(args.save + "/crtsh_cert.json", "w", encoding="utf-8") as f:
                    json.dump(certs, f, ensure_ascii=False, indent=4)
                with open(os.path.join(args.save, "/crtsh_certs_detail.json"), "w", encoding="utf-8") as f:
                    json.dump(certs_detail, f, ensure_ascii=False, indent=4)
            else:
                with open(args.save + "/crtsh_cert.json", "w", encoding="utf-8") as f:
                    json.dump(certs, f, ensure_ascii=False, indent=4)
                with open(args.save + "/crtsh_certs_detail.json", "w", encoding="utf-8") as f:
                    json.dump(certs_detail, f, ensure_ascii=False, indent=4, default=datetime_handler)
    except ValueError:
        print("Argument value error!")
    
if __name__ == "__main__":
    main()