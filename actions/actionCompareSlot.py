# from rasa_sdk import Action, Tracker
# from rasa_sdk.executor import CollectingDispatcher
# from rasa_sdk.events import SlotSet
# from typing import Any, Text, Dict, List

# class ActionCompareSlots(Action):

#     def name(self) -> Text:
#         return "action_compare_slots"

#     def run(self, dispatcher: CollectingDispatcher,
#             tracker: Tracker,
#             domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

#         active_painting = tracker.get_slot("active_painting")
#         favourite_painting = tracker.get_slot("favourite_painting")

#         # Ensure slots are not null and not the same
#         if active_painting and favourite_painting and active_painting != favourite_painting:
#             return [SlotSet("compare_slots", "different")]
#         else:
#             return [SlotSet("compare_slots", "same_or_null")]

