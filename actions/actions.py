# This files contains your custom actions which can be used to run
# custom Python code.
#
# See this guide on how to implement these action:
# https://rasa.com/docs/rasa/custom-actions


# This is a simple example for a custom action which utters "Hello World!"

# from typing import Any, Text, Dict, List
#
# from rasa_sdk import Action, Tracker
# from rasa_sdk.executor import CollectingDispatcher
#
#
# class ActionHelloWorld(Action):
#
#     def name(self) -> Text:
#         return "action_hello_world"
#
#     def run(self, dispatcher: CollectingDispatcher,
#             tracker: Tracker,
#             domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
#
#         dispatcher.utter_message(text="Hello World!")
#
#         return []
from typing import Any, Text, Dict, List

from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher
import random
from pymongo import MongoClient
from fuzzywuzzy import fuzz
from fuzzywuzzy import process
from bs4 import BeautifulSoup
import requests

def get_database():
 
   # Provide the mongodb atlas url to connect python to mongodb using pymongo
   CONNECTION_STRING = "mongodb+srv://kudo313:kudo_321@cluster1.mza5o.mongodb.net/?retryWrites=true&w=majority"
 
   # Create a connection using MongoClient. You can import MongoClient or use pymongo.MongoClient
   client = MongoClient(CONNECTION_STRING)
 
   # Create the database for our example (we will use the same database throughout the tutorial
   return client['rasa']
  
dbname = get_database()
ask_infor = [None]

class ActionRecommend(Action):

    def name(self) -> Text:
        return "action_recommend"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        
        
        collection_name = dbname["test_do_an"]
        items = collection_name.find()
        list_food = []
        for item in items:
        # This does not give a very readable output
            list_food.append(item['mon_an'])
        
        food = []   
        for i in range(2):
            food_number = random.randrange(len(list_food))
            food.append(list_food[food_number])

        dispatcher.utter_message(
            text="Em nghĩ hôm nay anh chị có thể thử món '{}' hoặc bên cạnh đó cũng có thể là món '{}' ạ".format(food[0], food[1]))

        return []

class GetName(Action):
    def name(self) -> Text:
        return "get_name"
    
    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        
        ask_infor[0] = next(tracker.get_latest_entity_values("position"), None)
        if ask_infor[0]  != None:
            ask_infor[0]  = "position"
        else:
            ask_infor[0]  = next(tracker.get_latest_entity_values("department"), None)
            if ask_infor[0]  != None:
                ask_infor[0]  = "department"
        dispatcher.utter_message(
            text = "Anh chị có thể cho em xin tên của mình được không ạ")                
        print(ask_infor[0])

        return []

class GetInfor(Action):
    def name(self) -> Text:
        return "get_infor"
    
    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        name =  next(tracker.get_latest_entity_values("name_person"), None)
        collection_name = dbname["company"]
        items = collection_name.find()
        print(ask_infor[0] )
        if name != None:
            for item in items:
                ten_nv = item['ten_nv'].lower()
                name = name.lower()
                if name in ten_nv:
                    if ask_infor[0]  == "department":
                        dispatcher.utter_message(
                        text = "Trung tâm của anh chị bên " + item['trung_tam'])
                    elif ask_infor[0] == "position":
                        dispatcher.utter_message(
                            text = "Vị trí của anh/chị là " + item['chuc_vu'])
                    else:
                        dispatcher.utter_message(
                        text = "Xin lỗi em không thể tìm thấy thông tin của anh/chị")
                    break
        else:
            dispatcher.utter_message(
                text = "Xin lỗi, nhưng em không phân biệt được tên anh chị")
        return []

class AnsIndiInfor(Action):
    def name(self) -> Text:
        return "ans_indi_infor"
    
    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        
        name = next(tracker.get_latest_entity_values("name_person"), None)
        ques = next(tracker.get_latest_entity_values("indi_ques"), None)
        collection_name = dbname["company"]
        items = collection_name.find()
        print(ques)
        print(name)
        if name != None:
            for item in items:
                ten_nv = item['ten_nv'].lower()
                name = name.lower()
                
                if name in ten_nv:
                    if ques != None:
                        ques = ques.lower()
                        if ques == "trung tâm":
                            dispatcher.utter_message(
                            text = "Trung tâm của anh chị bên " + item['trung_tam'])
                        elif ques == "vị trí":
                            dispatcher.utter_message(
                                text = "Vị trí của anh/chị là " + item['chuc_vu'])
                        elif ques == "thông tin":
                            dispatcher.utter_message(
                                text = "Vị trí của anh/chị là " + item['chuc_vu'] + "bên trung tâm" + item['trung_tam'])
                        else:
                            dispatcher.utter_message(
                            text = "Xin lỗi em không thể tìm thấy thông tin của anh/chị")
                        break
                    else:
                        dispatcher.utter_message(
                            text = "Xin lỗi, nhưng em chưa hiểu câu hỏi của anh chị")
        else:
            dispatcher.utter_message(
                text = "Xin lỗi, nhưng em không phân biệt được tên anh chị")
        return []

class AnsListEmploy(Action):
    def name(self) -> Text:
        return "ans_list_employ"
    
    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        name_department = next(tracker.get_latest_entity_values("name_department"), None)
        name_position = next(tracker.get_latest_entity_values("name_position"), None)
        collection_name = dbname["company"]
        items = collection_name.find()
        list_employ = ""
        print(name_department)
        print(name_position)
        if name_department != None and name_position != None:
            for item in items:
                department = item['trung_tam'].lower()
                name_department = name_department.lower()
                position = item['chuc_vu'].lower()
                name_position = name_position.lower()
                if name_position != "thành viên":
                    if name_department in department and name_position in position:
                        list_employ += item['ten_nv'] + "\n"
                else:
                    if name_department in department :
                        list_employ += item['ten_nv'] + "\n"
            if list_employ == "":
                dispatcher.utter_message(
                    text = "Hiện tại không có nhân viên nào ở vị trí này")
            else:
                list_employ = "Danh sách " + name_position + " bên " + name_department + " hiện tại: \n" + list_employ
                dispatcher.utter_message(
                    text = list_employ)
        else:
            dispatcher.utter_message(
                text = "Xin lỗi, nhưng em chưa hiểu câu hỏi của anh chị")
        return []    

class AnsNumEmploy(Action):
    def name(self) -> Text:
        return "ans_number_employ"
    
    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        name_department = next(tracker.get_latest_entity_values("name_department"), None)
        name_position = next(tracker.get_latest_entity_values("name_position"), None)
        collection_name = dbname["company"]
        items = collection_name.find()
        number = 0
        print(name_department)
        print(name_position)
        if name_department != None and name_position != None:
            for item in items:
                department = item['trung_tam'].lower()
                name_department = name_department.lower()
                position = item['chuc_vu'].lower()
                name_position = name_position.lower()
                if name_position != "thành viên":
                    if name_department in department and name_position in position:
                        number +=1 
                else:
                    if name_department in department :
                        number += 1
            if number == 0:
                dispatcher.utter_message(
                    text = "Hiện tại không có nhân viên nào ở vị trí này")
            else:
                list_employ = "Có tổng "+ str(number) + name_position + " bên " + name_department + " hiện tại: \n"
                dispatcher.utter_message(
                    text = list_employ)
        else:
            dispatcher.utter_message(
                text = "Xin lỗi, nhưng em chưa hiểu câu hỏi của anh chị")
        return []

class AnsForJob(Action):
    def name(self) -> Text:
        return "ans_for_job"
    
    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:



        url = 'https://careers.rikai.technology/tuyen-dung'
        # page = urllib.request.urlopen(url, context=context)
        page = requests.get(url, verify=False)
        soup = BeautifulSoup(page.text, 'html.parser')
        all_jobs = {}
        all_jobs_text = ""
        for n in range(len(soup.find_all(class_='page5sl-text',))):
            jobs = soup.find_all(class_='page5sl-text',)[n]
            name_job = jobs.find_all('a', href=True)[0].decode_contents()
            link_jd = jobs.find_all('a', href=True)[0]['href']
            num = jobs.find_all(class_="xanh")[0].decode_contents()
            all_jobs[name_job] = {'num':num, 'link_jd':link_jd}
            all_jobs_text += name_job + ":" + "\n" + num + "\n" + "Link JD: " + link_jd + "\n"
        name_job = next(tracker.get_latest_entity_values("name_job"), None)
        name_position = next(tracker.get_latest_entity_values("name_position"), None)
        print(name_job)
        print(name_position)
        if name_job != None :
            name_job = name_job.lower()
            found = False
            for name_job_data in all_jobs.keys():
                name_job_data_lower = name_job_data.lower()
            
                if fuzz.partial_ratio(name_job_data_lower, name_job) > 80:
                    text = ("Hiện công ty đang tuyển vị trí: " + name_job_data + "\n" + all_jobs[name_job_data]['num']
                            + "\n" + "Link JD: " + all_jobs[name_job_data]['link_jd'])
                    
                    dispatcher.utter_message(
                        text = text)
                    found = True
                    break
            if found == False:
                dispatcher.utter_message(
                        text = "Hiện bên mình không còn tuyển vị trí này nữa")

        else:
            dispatcher.utter_message(
                text = "Hiện bên mình đang tuyển các vị trí sau:\n " + all_jobs_text)
        return []    