import requests
import json
import argparse
import os
import lxml
import datetime

from bs4 import BeautifulSoup
from dateutil.parser import parse
from datetime import datetime, timedelta

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
        api_url = "https://graph.facebook.com/certificates?query={}&fields=cert_hash_sha256,domains,issuer_name,serial_number,certificate_pem&limit=10000&access_token=727706161384748|IfGdH0dhYXQJNh-F-Oz5lKqesq0".format(domain)
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
    
    facebook_sha256 = {}
    facebook_cert_details = {}
    
    try:
        if args.domain:
            print("Downloading certificates from " + args.domain)
            certs = cralwer.retrieve_cert(args.domain, True, True)
            print("Before dedup contains %d" % len(certs["data"]))
            certs_detail_list = cralwer.dedup(certs)
            print("After dedup contains %d" % len(certs_detail_list))
            
            for item in certs_detail_list:
                current_id = item["id"]
                if "0x" in item["serial_number"] :
                    dec = int(str.lower(item["serial_number"]), 16)
                    # print(dec)
                    
                    facebook_sha256[str(dec)] = current_id
                    facebook_cert_details[current_id] = item
                else:
                    dec = str.lower(item["serial_number"])
                    # print(dec)
                    facebook_sha256[dec] = current_id
                    facebook_cert_details[current_id] = item
            
            missing_serial = []
            with open("./missing_certs.json", "r") as f:
                data = json.load(f)
                
            now = datetime.now()

            for key, value in data.items():
                if "not_before" not in value or "not_after" not in value:
                    continue
                not_before = datetime.strptime(value["not_before"][:10], "%Y-%m-%d")
                not_after = datetime.strptime(value["not_after"][:10], "%Y-%m-%d")
                if now < not_before or now > not_after:
                    continue
                missing_serial.append(value["serial"])
            
            keys = list(facebook_sha256.keys())
            
            for item in missing_serial:
                dec = str(int(str.lower(item), 16))
                if dec not in keys:
                    print("{} not found in Facebook".format(dec))
            
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