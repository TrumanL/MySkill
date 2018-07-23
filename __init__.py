# TODO: Add an appropriate license to your skill before publishing.  See
# the LICENSE file for more information.


import json
from adapt.intent import IntentBuilder
from mycroft.skills.core import MycroftSkill, intent_handler
from mycroft.util.log import LOG
from datetime import datetime, timedelta
from mycroft.audio import wait_while_speaking
from mycroft.configuration import ConfigurationManager
from os.path import join, abspath, dirname
from mycroft.filesystem import FileSystemAccess

class MySkill(MycroftSkill):
  
  
  def __init__(self):
    super(MySkill, self).__init__(name="MySkill")
    self.MessageQueueFileName = 'MessageQueue.json'
    
    # Initialize working variables used within the skill.
  def initialize(self):
      #initialize notification events
      try: 
          self.add_event('notificaton.check', self.handle_read_messages_passive)
          self.log.info("*******Handler Added Successfully")
      except:
          pass
      #initialize the message queue file if it does not already exist
      t = self.file_system.open(self.MessageQueueFileName, 'w')
      t.write(json.dumps({"messages":[]},  sort_keys=True, indent=4, separators=(',', ': ')))
      t.close()
      self.log.info("********Message Queue Initialized")
 
  @intent_handler(IntentBuilder("").require("Read").require("Messages"))  
  def handle_read_messages_intent(self, message):
    with self.file_system.open(self.MessageQueueFileName, 'r+') as f:
      messageData = json.load(f)
      
      if len(messageData["messages"]) > 0:
        
        self.speak(str(len(messageData["messages"])) + " new messages.")
        yes_words = set(self.translate_list('confirm'))
        
        fullData = messageData
        for i in range(len(fullData["messages"])):
          
          poppedData = messageData["messages"].pop()
          self.speak("From " + poppedData["sender"] + ". " + poppedData["sender"] +" says")
          wait_while_speaking()
          self.speak(poppedData["data"])
          wait_while_speaking()
          
          if poppedData["response-needed"] == "true":
            
            outMessageConfirm = self.get_response('ask.confirm_message_response')
            if any(word in outMessageConfirm for word in yes_words):
                outMessage = self.get_response('ask.for_message')
                #send outMessage to other person
                print(outMessage)
          f.seek(0)
          f.write(json.dumps(messageData, sort_keys=True, indent=4, separators=(',', ': ')))
          f.truncate()
          
          if len(messageData["messages"]) > 0: 
            self.speak("Next Message")
            wait_while_speaking()
          else:
            self.speak("End Of messages")
            wait_while_speaking()
      else:
          self.speak("No new messages")
          wait_while_speaking()
          self.stop()
     
  def handle_read_messages_passive(self, message):
    with self.file_system.open(self.MessageQueueFileName, 'r+') as f:
      messageData = json.load(f)
      
      if len(messageData["messages"]) > 0:
        
        self.speak("You have " + str(len(messageData["messages"])) + " new messages.")
        confirmedIntent =  self.get_response("ask.confirm_message_view")
        yes_words = set(self.translate_list('confirm'))
        
        print(yes_words)
        if any(word in confirmedIntent for word in yes_words):
            fullData = messageData
            for i in range(len(fullData["messages"])):
              
              poppedData = messageData["messages"].pop()
              self.speak("From " + poppedData["sender"] + ". " + poppedData["sender"] +" says")
              wait_while_speaking()
              self.speak(poppedData["data"])
              wait_while_speaking()
              
              if poppedData["response-needed"] == "true":
                
                outMessageConfirm = self.get_response('ask.confirm_message_response')
                if any(word in outMessageConfirm for word in yes_words):
                    outMessage = self.get_response('ask.for_message')
                    #send outMessage to other person
                    print(outMessage)
              f.seek(0)
              f.write(json.dumps(messageData, sort_keys=True, indent=4, separators=(',', ': ')))
              f.truncate()
              
              if len(messageData["messages"]) > 0: 
                self.speak("Next Message")
                wait_while_speaking()
              else:
                self.speak("End Of messages")
                wait_while_speaking()
        else :
            self.speak("I'll show them another time")
            self.stop()
      else:
          self.stop()       
    
  
  def handle_push_notification(self, message):
      with self.file_system.open(self.MessageQueueFileName, 'r+') as f:
          messageQueue = json.load(f)
          messageQueue["messages"].append(message["messageData"])
          f.seek(0)
          f.write(json.dumps(messageData, sort_keys=True, indent=4, separators=(',', ': ')))
          f.truncate()
  
  def stop(self):
    return False

def create_skill():
  return MySkill()


