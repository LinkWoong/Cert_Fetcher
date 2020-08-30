import requests
import json
import argparse
import os
import lxml
import datetime

from bs4 import BeautifulSoup
from dateutil.parser import parse

class Facebook_fetcher(object):
    def __init__(self, domain, wildcard=True, expried=True):
        self.domain = domain
        self.wildcard = wildcard
        self.expried = expried

    def retrieve_cert(self, domain, wildcard=True, exprired=True) -> {}:
        """ Return example
        {
            "data": [
                {
                "certificate_pem": "-----BEGIN CERTIFICATE-----
            MIIH5DCCBsygAwIBAgIQDACZt9eJyfZmJjF+vOp8HDANBgkqhkiG9w0BAQsFADBw
            MQswCQYDVQQGEwJVUzEVMBMGA1UEChMMRGlnaUNlcnQgSW5jMRkwFwYDVQQLExB3
            d3cuZGlnaWNlcnQuY29tMS8wLQYDVQQDEyZEaWdpQ2VydCBTSEEyIEhpZ2ggQXNz
            dXJhbmNlIFNlcnZlciBDQTAeFw0xNjEyMDkwMDAwMDBaFw0xODAxMjUxMjAwMDBa
            MGkhMRMwEQYDVQQHEwpNZW5sbyBQYXJrMRcwFQYDVQQKEw5GYWNlYm9vaywgSW5j
            LjEXMBUGA1UEAwwOKi5mHwYDVR0jBBgwFoAUUWj/kK8CB3U8zNllZGKiErhZcjsw
            YWNlYm9vay5jb20wWTATBgcqhkjOPQIBBggqhkjOPQMBBwNCAASg8YyvpzmIaFsT
            Vg4VFbSnRe8bx+WFPCsE1GWKMTEi6qOS7WSdumWB47YSdtizC0Xx/wooFJxP3HOp
            s0ktoHbTo4IFSjCCBUYwHwYDVR0jBBgwFoAUUWj/kK8CB3U8zNllZGKiErhZcjsw
            HQYDVR0OBBYEFMuYKIyhcufiMqmaPfINoYFWoRqLMIHHBgNVHREEgb8wgbyCDiou
            ZmFjZWJvb2suY29tgg4qLmZhY2Vib29rLm5ldIIIKi5mYi5jb22CCyouZmJjZG4u
            bmV0ggsqLmZic2J4LmNvbYIQKi5tLmZ
            -----END CERTIFICATE-----",
                "id": "1662768163744657"
                }
            ]
        }
        """
        # print("Downloading certificates from " + domain)
        api_url = "https://graph.facebook.com/certificates?query={}&fields=cert_hash_sha256,domains,issuer_name,certificate_pem&limit=10000&access_token=727706161384748|IfGdH0dhYXQJNh-F-Oz5lKqesq0".format(domain)
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
        data = certs["data"]
        certs = []
        for cert in data:
            for key, value in cert.items():
                if key == "id":
                    unique_id.add(value)
            certs.append(cert)     
        return certs
        
def datetime_handler(x):
    if isinstance(x, datetime.datetime):
        return x.isoformat()
    raise TypeError("Unknown type")

def main():
    parser = argparse.ArgumentParser(description="Arg parser for running this crawler")
    parser.add_argument('-d', dest='domain', action='store', help="domain name")
    parser.add_argument('-s', dest='save', action='store', help='destination directory for saving the certificates')
    
    args = parser.parse_args()
    cralwer = Facebook_fetcher(args.domain, True, True)
    certs = []
    certs_detail = {}
    unique_id = set()
    
    try:
        if args.domain:
            print("Downloading certificates from " + args.domain)
            certs = cralwer.retrieve_cert(args.domain, True, True)
            print("Before dedup contains %d" % len(certs["data"]))
            certs_detail = cralwer.dedup(certs)
            print("After dedup contains %d" % len(certs_detail))
            
        if args.save:
            if certs is None or len(certs_detail) == 0:
                print("Current result is empty")
            elif not os.path.exists(args.save):
                os.mkdir(args.save)
                with open(os.path.join(args.save, "/facebook_certs_detail.json"), "w", encoding="utf-8") as f:
                    json.dump(certs_detail, f, ensure_ascii=False, indent=4)
            else:
                with open(args.save + "/facebook_certs_detail.json", "w", encoding="utf-8") as f:
                    json.dump(certs_detail, f, ensure_ascii=False, indent=4, default=datetime_handler)
    except ValueError:
        print("Argument value error!")
    
if __name__ == "__main__":
    main()