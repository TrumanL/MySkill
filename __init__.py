# TODO: Add an appropriate license to your skill before publishing.  See
# the LICENSE file for more information.

# Below is the list of outside modules you'll be using in your skill.
# They might be built-in to Python, from mycroft-core or from external
# libraries.  If you use an external library, be sure to include it
# in the requirements.txt file so the library is installed properly
# when the skill gets installed later by a user.
import json
from adapt.intent import IntentBuilder
from mycroft.skills.core import MycroftSkill, intent_handler
from mycroft.util.log import LOG
from datetime import datetime, timedelta
from mycroft.audio import wait_while_speaking
from mycroft.configuration import ConfigurationManager
from os.path import join, abspath, dirname
from mycroft.filesystem import FileSystemAccess

# Each skill is contained within its own class, which inherits base methods
# from the MycroftSkill class.  You extend this class as shown below.

# TODO: Change "Template" to a unique name for your skill
class MySkill(MycroftSkill):
  
  # The constructor of the skill, which calls MycroftSkill's constructor
  def __init__(self):
    super(MySkill, self).__init__(name="MySkill")
    self.MessageQueueFileName = 'MessageQueue.json'
    
    # Initialize working variables used within the skill.
  def initialize(self):
      try: 
          self.add_event('notificaton.check', self.handle_read_messages_passive)
          self.log.info("*******Handler Added Successfully")
          temp  = self.file_system.open(self.MessageQueueFileName, 'w')
          temp.close()
      except:
          pass
  # The "handle_xxxx_intent" function is triggered by Mycroft when the
  # skill's intent is matched.  The intent is defined by the IntentBuilder()s
  # pieces, and is triggered when the user's utterance matches the pattern
  # defined by the keywords.  In this case, the match occurs when one word
  # is found from each of the files:
  #    vocab/en-us/Hello.voc
  #    vocab/en-us/World.voc
  # In this example that means it would match on utterances like:
  #   'Hello world'
  #   'Howdy you great big world'
  #   'Greetings planet earth'
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
          #open(self.jsonPath, "w").write(json.dumps(messageData, sort_keys=True, indent=4, separators=(',', ': ')))
          
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
    #with open(self.jsonPath, 'r+') as f:
    with self.file_system.open(self.MessageQueueFileName, 'r+b') as f:
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
    

  def stop(self):
    return False

# The "create_skill()" method is used to create an instance of the skill.
# Note that it's outside the class itself.

def create_skill():
  return MySkill()


