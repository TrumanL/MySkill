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
try:
    from RPi.GPIO import RPi.GPIO as GPIO
except as e:
    print(sys.exc_info()[0])



class MySkill(MycroftSkill):
  
  
  def __init__(self):
    super(MySkill, self).__init__(name="MySkill")
    self.MessageQueueFileName = 'MessageQueue.json'
    
    # Initialize working variables used within the skill.
  def initialize(self):
      #initialize notification events
      try: 
          self.add_event('notification.check', self.handle_read_messages_passive)
          self.add_event('notification.push', self.handle_push_notification)
      except:
          pass
      try:
          GPIO.setup(23, GPIO.IN, pull_up_down=GPIO.PUD_UP)
          self.log.info("******GPIO SETUP")
          GPIO.add_event_detect(23, GPIO.FALLING, callback=self.handle_read_messages_passive, bouncetime=300)
          self.log.info("******GPIO EVENT ADDED")
      except:
          self.log.info("******GPIO EVENT FAILED")
      #initialize the message queue file if it does not already exist
      try:
          t = self.file_system.open(self.MessageQueueFileName, 'r')
          t.close()
      except:
          t = self.file_system.open(self.MessageQueueFileName, 'w')
          t.write(json.dumps({"messages":[]},  sort_keys=True, indent=4, separators=(',', ': ')))
          t.close()
 
  @intent_handler(IntentBuilder("").require("Read").require("Messages"))  
  def handle_read_messages_intent(self, message):
    with self.file_system.open(self.MessageQueueFileName, 'r+') as f:
      messageData = json.load(f)
      
      if len(messageData["messages"]) > 0:
        if len(messageData["messages"]) == 1:
            self.speak(str(len(messageData["messages"])) + " new message.")
        else:
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
          f.close()
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
      self.log.info(len(messageData["messages"]))
      if len(messageData["messages"]) > 0:
        if len(messageData["messages"]) == 1:
            self.speak(str(len(messageData["messages"])) + " new message.")
        else:
            self.speak(str(len(messageData["messages"])) + " new messages.")
        yes_words = set(self.translate_list('confirm'))
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
              f.close()
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
          messageQueue["messages"].append(json.loads(message.serialize())["data"]["messageData"])
          f.seek(0)
          f.write(json.dumps(messageQueue, sort_keys=True, indent=4, separators=(',', ': ')))
          f.truncate()
          f.close()
  
  def stop(self):
    return False

def create_skill():
  return MySkill()


