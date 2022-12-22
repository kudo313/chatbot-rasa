import yaml

from yaml import CLoader as Loader, CDumper as Dumper
from pymongo import MongoClient

# Provide the mongodb atlas url to connect python to mongodb using pymongo
CONNECTION_STRING = "mongodb+srv://kudo313:kudo_321@cluster1.mza5o.mongodb.net/?retryWrites=true&w=majority"

# Create a connection using MongoClient. You can import MongoClient or use pymongo.MongoClient
client = MongoClient(CONNECTION_STRING)
dbname = client['rasa']
collection = dbname['company']
items = collection.find()
list_examples = ''
tmp1 = ""
temp1 = ''
temp2 = ''
temp3 = ''
temp4 = ''
temp5 = ''
temp6 = ''
temp7 = ''
temp8 = ''
temp10 = ''
temp9 = ''

for item in items:
    ten_nv = item['ten_nv'].split(' ')
    tmp1 = '- cho mình xin [thông tin]{"entity": "indi_ques"}' + ' [{}]'.format(item['ten_nv']) + '{"entity":"name_person"}\n'
    temp1 += tmp1
    tmp2 = '- [anh]{"entity": "pronouns"} ' +'[{0}]'.format(ten_nv[-1]) + '{"entity":"name_person"}' + ' làm ở [vị trí]{"entity": "indi_ques"} nào thế\n'
    temp2 += tmp2
    tmp3 = '- [bạn]{"entity": "pronouns"}'+' [{0}]'.format(ten_nv[-1]) + '{"entity":"name_person"}' + ' có [chức danh]{"entity": "indi_ques"} gì thế\n'
    temp3 += tmp3
    tmp4 = '- [anh]{"entity": "pronouns"}'+' [{0}]'.format(ten_nv[-1]) + '{"entity":"name_person"}' + ' làm ở [trung tâm]{"entity": "indi_ques"} nào\n'
    temp4 += tmp4
    tmp5 = '- [chị]{"entity": "pronouns"}'+' [{0}]'.format(ten_nv[-1]) + '{"entity":"name_person"}' + ' làm ở [vị trí]{"entity": "indi_ques"} nào thế\n'
    temp5 += tmp5
    tmp6 = '- [chị]{"entity": "pronouns"}'+' [{0}]'.format(ten_nv[-1]) + '{"entity":"name_person"}' + ' làm ở [bộ phận]{"entity": "indi_ques"} nào thế\n'
    temp6 += tmp6
    tmp7 = '- [anh]{"entity": "pronouns"}'+' [{0}]'.format(ten_nv[-1]) + '{"entity":"name_person"}' + ' làm ở [bộ phận]{"entity": "indi_ques"} nào thế\n'
    temp7 += tmp7
    tmp8 = '- cho mình xin [thông tin]{"entity": "indi_ques"}' + ' [anh]'+'{"entity": "pronouns"}'+' [{}]'.format(ten_nv[-1]) + '{"entity":"name_person"}\n'
    temp8 += tmp8
    tmp9 = '- [chức vụ]{"entity": "indi_ques"}' + ' của [anh]'+'{"entity": "pronouns"}'+' [{}]'.format(ten_nv[-1]) + '{"entity":"name_person"}\n'
    temp9 += tmp9
    tmp10 = '- [chức vụ]{"entity": "indi_ques"}' + ' của [chị]'+'{"entity": "pronouns"}'+' [{}]'.format(ten_nv[-1]) + '{"entity":"name_person"}\n'
    temp10 += tmp10
list_examples = temp1 + temp2 + temp3 + temp4 + temp5 + temp6 + temp7 + temp8 + temp9 + temp10
with open("data/nlu.yml", "r") as stream:
    i = yaml.load(stream, Loader=Loader)
    print(i)
    for z in i['nlu']:
        if z['intent'] == 'ask_for_indiviual_infor':
            z['examples'] = list_examples
            break

print(i)
with open("test.yml", "w") as stream:
    # data = {'-':{'intents': {'provide_name':['greet', 'goodbye', 'thankyou', 'praise', 'decry', 'ask_for_lunch', 'ask_ability', 'provide_name', 'ask_for_infor']}}}
    data = i
    yaml.dump(data,sort_keys= False,allow_unicode = True, stream=stream)

