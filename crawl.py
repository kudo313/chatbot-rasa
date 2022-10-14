from bs4 import BeautifulSoup
import urllib.request
import ssl
import requests
import json
import csv
url = 'https://careers.rikai.technology/tuyen-dung'
# page = urllib.request.urlopen(url, context=context)
page = requests.get(url, verify=False)
soup = BeautifulSoup(page.text, 'html.parser')
all_jobs = {}
for n in range(len(soup.find_all(class_='page5sl-text',))):
    jobs = soup.find_all(class_='page5sl-text',)[n]
    name_job = jobs.find_all('a', href=True)[0].decode_contents()
    link_jd = jobs.find_all('a', href=True)[0]['href']
    num = jobs.find_all(class_="xanh")[0].decode_contents()
    all_jobs[name_job] = {'num':num, 'link_jd':link_jd}
all_jobs