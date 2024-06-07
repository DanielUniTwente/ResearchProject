# This files contains your custom actions which can be used to run
# custom Python code.
#
# See this guide on how to implement these action:
# https://rasa.com/docs/rasa/custom-actions


# This is a simple example for a custom action which utters "Hello World!"

from typing import Any, Text, Dict, List
from neo4j import GraphDatabase
from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.events import SlotSet
import dotenv
import os
import openai

from fuzzywuzzy import fuzz
from fuzzywuzzy import process

# load_status = dotenv.load_dotenv("actions/Neo4j-5775be33-Created-2024-05-27.txt")
# if load_status is False:
#     raise RuntimeError('Environment variables not loaded.')

# URI = os.getenv("NEO4J_URI")
# AUTH = (os.getenv("NEO4J_USERNAME"), os.getenv("NEO4J_PASSWORD"))
URI = "bolt://localhost:7687"
AUTH = ("neo4j", "53ds!6g81ds8nmD_F74982FH89D7ds54gSD")
openai.api_key = os.getenv("OPENAI_API_KEY")

class ActionTestDatabaseAccess(Action):
    def name(self) -> Text:
        return "action_test_database_access"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        with GraphDatabase.driver(URI, auth=AUTH) as driver:
            driver.verify_connectivity()
            records, summary, keys = driver.execute_query(
                """
                MATCH (n) WHERE (n.name) IS NOT NULL 
                RETURN DISTINCT "node" as entity, n.name AS name LIMIT 25 
                UNION ALL 
                MATCH ()-[r]-() WHERE (r.name) IS NOT NULL 
                RETURN DISTINCT "relationship" AS entity, r.name AS name LIMIT 25
                """,
                database_="neo4j",
            )
            # Loop through results and do something with them
            for record in records:
                print(record.data())  # obtain record as dict
            # Summary information
            print("The query `{query}` returned {records_count} records in {time} ms.".format(
                query=summary.query, records_count=len(records),
                time=summary.result_available_after
            ))       
        return []
    
class ActionSendToAPI(Action):
    def name(self) -> Text:
        return "action_send_to_api"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        
        # user_input = tracker.latest_message.get('text')
        # print(user_input)
        conversation_history = tracker.events
        active_painting = tracker.get_slot("active_painting")
        stage = tracker.get_slot("stage")
        query= f"""MATCH (p:Paintings)-->(i:Item) WHERE p.name="King Caspar" RETURN i.name, i.Description"""
        knownObjects = tracker.get_slot("known_objects")
        print(knownObjects)
        items=""
        databaseObjects=usefull.callDatabase(query)
        for record in databaseObjects:
            items = items + f"""\nItem: {record['i.name']}\nDescription: {record['i.Description']}"""
        compare=""  
        if stage == "compare":
            last_active_painting = tracker.get_slot("last_active_painting")
            # favorite_painting = tracker.get_slot("favourite_painting")
            compare = f"The paintings you want the user to compare are {active_painting}, {last_active_painting}."

        instructions = f"""
You are a tour guide trained in Visual Thinking Strategies (VTS). 
You are chatting with a single user who is interested in learning more about the artwork {active_painting}.
Do not describe the artwork, ask open-ended questions to guide the user through it.
If the user tries to talk about another painting , gently guide them back to {active_painting}
You want to do this in 5 stages: observation, describe story, describe author technique, describe feelings and compare.
The current stage is {stage}. Do not go to other stages. Vary the beginnings of your responses.
Here are all the items in the painting: {items}
If the user begins describing objects not in the above list ask them to focus on the items in the painting.
{compare}
        """
        # Construct the history of conversation
        messages = usefull.constructPrompt(conversation_history, active_painting, instructions)

        # API call
        
        openai_response = usefull.getAPIResponse(messages)
        

        dispatcher.utter_message(text=openai_response)
        if knownObjects is None:
            return [SlotSet('known_objects',  databaseObjects)]
        elif len(knownObjects) == 0:
            return [SlotSet('known_objects',  None)]
        else:
            del messages[0]
            covered_items = usefull.check_chat_for_items(messages[-3:], [x[0] for x in knownObjects])
            return [SlotSet('known_objects', [t for t in knownObjects if t[0] not in covered_items])]
    

class ActionSummarize(Action):
    def name(self) -> Text:
        return "action_summarize"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        # user_input = tracker.latest_message.get('text')
        conversation_history = tracker.events
        active_painting = tracker.get_slot("active_painting")
        query = f"""MATCH (n:Paintings) WHERE n.name="{active_painting}" RETURN n.exhibit"""
        description = usefull.callDatabase(query)[0].data()["n.exhibit"]
        instructions = f"""
You are a tour guide trained in Visual Thinking Strategies (VTS). 
You are chatting with a single user who is interested in learning more about the artwork {active_painting}.
Summarize the conversation regarding the painting {active_painting} in no more than 5 bullet points.
Use the information from the conversation and this description of the artwork:{description} 
        """
        messages = usefull.constructPrompt(conversation_history, active_painting, instructions)
        print(messages)

        # API call
        openai_response = usefull.getAPIResponse(messages)
        
        dispatcher.utter_message(text=openai_response)

        return []   

class ActionAuthorTechnique(Action):    
    def name(self) -> Text:
        return "action_author_technique_api"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        
        # user_input = tracker.latest_message.get('text')
        conversation_history = tracker.events
        active_painting = tracker.get_slot("active_painting")
        stage = tracker.get_slot("stage")
        
        query = f"""MATCH (g:Genre)<--(n:Paintings)-[on_MATERIAL]->(m:Material) 
                    WHERE n.name="King Caspar" 
                    RETURN m.name ,m.description,g.name,g.description"""
        materials=""
        for record in usefull.callDatabase(query):
            materials= materials + f"""\nMaterial: {record['m.name']}\nDescription: {record['m.description']}
Genre: {record['g.name']}\nDescription: {record['g.description']}"""
            
        instructions = f"""
You are a tour guide trained in Visual Thinking Strategies (VTS). 
You are chatting with a single user who is interested in learning more about the artwork {active_painting}.
You want to do this in 5 stages: observation, describe story, describe author technique, describe feelings and compare.
The current stage is {stage}. Do not go to other stages. Ask open-ended questions to guide the user. Vary the beginnings of your responses.
You may describe the techniques if the user is having trouble perceiving or identifying them.
Here are some details genre and materials: {materials}
        """
        print(instructions)
        # Construct the history of conversation
        messages = usefull.constructPrompt(conversation_history, active_painting, instructions)

        # API call
        openai_response = usefull.getAPIResponse(messages)
        print(f"{stage}")

        dispatcher.utter_message(text=openai_response)
        return []

class ActionSetImage(Action):
    def name(self) -> Text:
        return "action_set_image"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        
       
        active_painting = tracker.get_slot("active_painting")
        if active_painting=="King Caspar":
            image_url="flask-ui/static/images/kingcaspar.jpeg"
        elif active_painting=="Head of a Boy in a Turban":
            image_url="flask-ui/static/images/headofboyinturban.jpeg"
        elif active_painting=="Diego Bemba, a Servant of Don Miguel de Castro":
            image_url=""   
        elif active_painting=="Pedro Sunda, a Servant of Don Miguel de Castro":
            image_url=""
        return [SlotSet("image_url", image_url)]

class usefull():
    def constructPrompt(conversation_history, active_painting, instructions):
        current_painting = None
        messages = [{"role": "system", "content": instructions}]
        for event in conversation_history:
            if event.get("event") == "slot" and event.get("name") == "active_painting":
                current_painting = event.get("value")
            if current_painting == active_painting:
                if event.get("event") == "user":
                    messages.append({"role": "user", "content": event.get("text")})
                elif event.get("event") == "bot":
                    messages.append({"role": "assistant", "content": event.get("text")})
        return messages
    
    def callDatabase(query):
        with GraphDatabase.driver(URI, auth=AUTH) as driver:
            driver.verify_connectivity()
            records, summary, keys = driver.execute_query(
                query,
                database_="neo4j",
            )
        return records
    
    def getAPIResponse(messages):
        try:
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo-0301",
                messages=messages,
                max_tokens=150,
                n=1,
                stop=None,
                temperature=0.9,
            )
            openai_response = response['choices'][0]['message']['content'].strip()
        except Exception as e:
            openai_response = f"Sorry, I encountered an error: {str(e)}"
        return openai_response
    
    def check_chat_for_items(chat, items, threshold=80):
        """
        Check if a chat contains items from a list with a specified similarity threshold.

        :param chat: Dictionary representing the chat
        :param items: List of items to check for in the chat
        :param threshold: Similarity threshold for fuzzy matching (default is 80)
        :return: Dictionary with chat keys and list of found items for each key
        """

        for message in chat:
            content = message['content']
            found_items = []
            for item in items:
                # Using fuzzy matching to find close matches
                match_score = fuzz.partial_ratio(content.lower(), item.lower())
                print(f"for {content} and {item} score:{match_score}")
                if match_score >= threshold:
                    found_items.append(item)
        return found_items