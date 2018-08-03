# TODO: Add an appropriate license to your skill before publishing.  See
# the LICENSE file for more information.a

import sys
import time
import json
from adapt.intent import IntentBuilder
from mycroft.skills.core import MycroftSkill, intent_handler
from mycroft.util.log import LOG
from mycroft.audio import wait_while_speaking
from os.path import join, abspath, dirname
from mycroft.filesystem import FileSystemAccess
from mycroft.messagebus.message import Message
try:
    import RPi.GPIO as GPIO
except:
    pass


class MySkill(MycroftSkill):
  
  
  def __init__(self):
    super(MySkill, self).__init__(name="MySkill")
    self.MessageQueueFileName = 'MessageQueue.json' # file_system object handles the full path
    # GPIO variables created to make system changes much easier 
    self.GPIO_Pin = 27
    self.pull_up_down = GPIO.PUD_UP
    self.falling_rising = GPIO.FALLING
    
    self.testMessage = Message.deserialize(json.dumps({"type":"NULL", "data":{"messageData":{"data":"hi, how are you doing?", "sender":"bob","response-needed":"True"}}}))
  def initialize(self):
      #initialize notification events
      try: 
          self.add_event('notification.check', self.handle_read_messages_passive)
          self.add_event('notification.push', self.handle_push_notification)
      except:
          pass
      
      try:
          self.emitTest = self.emitter
          self.log.info("Emmiter Recieved")
      except:
          self.log.info("Emmiter NOT Recieved")
      try: # try except needed to be cross platform 
          #GPIO setup 
          GPIO.setmode(GPIO.BCM)
          GPIO.setup(self.GPIO_Pin, GPIO.IN, pull_up_down=self.pull_up_down)
          #self.log.info("******GPIO SETUP:" + str(self.GPIO_Pin))
          GPIO.add_event_detect(self.GPIO_Pin, self.falling_rising, callback=self.handle_read_messages_passive, bouncetime=300)
          self.log.info("******GPIO EVENT ADDED: " + str(self.GPIO_Pin))
      except:
          self.log.info("******GPIO EVENT FAILED OR ALREADY EXISTS")
          #self.log.info(sys.exc_info())
          pass
          
      #initialize the message queue file if it does not already exist
      try:
          t = self.file_system.open(self.MessageQueueFileName, 'r')
          t.close() # opening as read only checks if the file exists and throwns and exception if it doesn't
      except:
          t = self.file_system.open(self.MessageQueueFileName, 'w')
          t.write(json.dumps({"messages":[]},  sort_keys=True, indent=4, separators=(',', ': ')))
          t.close() # new file created at the app data path 
 
  @intent_handler(IntentBuilder("").require("Read").require("Messages"))  
  def handle_read_messages_intent(self, message): 
    # user initialized use case
    with self.file_system.open(self.MessageQueueFileName, 'r+') as f:
      self.read_messages(f, False)
  
  @intent_handler(IntentBuilder("").require("Add").require("Test").require("Messages"))
  def handle_add_test_message(self, message):
     self.handle_push_notification(self.testMessage)
  
  def handle_read_messages_passive(self, message):
    # passive (ie sensor, camera) activatied use case
    with self.file_system.open(self.MessageQueueFileName, 'r+') as f:
      self.read_messages(f, True)
 
  def read_messages(self, f, passive):
      """
      # read_messages : function to make changing the core mechanics/ui of reading through messages
      # easier while still maintaing a differance between use cases
      # args : 
      #     f : (.json file) the file where the message queue is stored
      #     passive : (bool) : handles the different use case of a passive activation (ie by a motion tracker)
      # no return
      """
      
      messageData = json.load(f)    # Message Data stored in a list in a json object
      yes_words = set(self.translate_list('confirm'))
      if len(messageData["messages"]) > 0:     # checks if there are any messages
        if len(messageData["messages"]) == 1: # 1 message plural fix
            self.speak(str(len(messageData["messages"])) + " new message.")
        else:
            self.speak(str(len(messageData["messages"])) + " new messages.")
        if passive:  # asks the user to confirm a read if it is passive activation
            #confirmedIntent =  self.ask_yesno("ask.confirm_message_view") 
            #self.log.info(confirmedIntent)
            #confirmedBool = true if confirmedIntent == 'yes' else false
            confirmedBool = True
        else:
            confirmedBool = True
        
        fullData = messageData # this is nessasary to maintain a copy of the full data to make looping more consistant 
        if confirmedBool: 
            for i in range(len(fullData["messages"])):
              
              poppedData = messageData["messages"].pop() # pop works well here because we want it to work like a voicemail
              self.speak("Message "+ str(i) +" from " + poppedData["sender"] + ". " + poppedData["sender"] +" says") #actual reading of the message
              wait_while_speaking()
              self.speak(poppedData["data"])
              wait_while_speaking()
              
              if poppedData["response-needed"] == "True":
                
                outMessageConfirm = self.get_response('ask.confirm_message_response')
                if any(word in outMessageConfirm for word in yes_words):
                    self.speak_dialog('ask.for_message')
                    wait_while_speaking()
                    #record(self.file_system.path+'/test.wav', 600, 44100, 1)
                    self.log.info("Audio Request Sending")
                    self.emitTest.wait_for_response(Message.deserialize(json.dumps({"type":"skill-audio-record:AudioRecordSkillIntent", "data":{"utterance":"record audio 10 seconds"}})), 'mycroft.skill.handler.complete', 10)
                    self.emitTest.wait_for_response(Message.deserialize(json.dumps({"type":"NULL"})), 'mycroft.skill.handler.complete', 15)
                    self.speak('Done')
                    wait_while_speaking()
              #the following lines write the poped data to the json file
              f.seek(0) 
              f.write(json.dumps(messageData, sort_keys=True, indent=4, separators=(',', ': ')))
              f.truncate()
              if len(messageData["messages"]) > 0: 
                self.speak("Next Message")
                wait_while_speaking()
              else:
                self.speak("End Of messages")
                f.close()
                wait_while_speaking()
        else:
            self.speak("I'll read them another time")
            if passive: # GPIO events need to be reset 
                 try: # needed for compatability between a system other than a pi
                      GPIO.cleanup()
                 except:
                      pass
            wait_while_speaking()
            self.stop()
      elif not passive:
          self.speak("No new messages")
          wait_while_speaking()
          self.stop()
      else: # GPIO events need to be reset 
          try: # needed for compatability between a system other than a pi
              GPIO.cleanup()
          except:
              print("except on passive no messages")
          self.stop()
          
  def handle_push_notification(self, message):
    """
      # handle_push_notifications : used to inject a notification into the message queue from the websocket
      # args : 
      #    message : message object : the message data sent through the websocket; contains the message we want to inject
      # no return
    """
    with self.file_system.open(self.MessageQueueFileName, 'r+') as f:
        messageQueue = json.load(f)
        # message data needs to be serialized to access the json object and lista
        messageQueue["messages"].append(json.loads(message.serialize())["data"]["messageData"])
        # the following lines write the update json to the file
        f.seek(0)
        f.write(json.dumps(messageQueue, sort_keys=True, indent=4, separators=(',', ': ')))
        f.truncate()
        f.close()
  
  def stop(self):
    return False

def create_skill():
  return MySkill()


