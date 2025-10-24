from spacebee_commander.message_manager import MessageManager
from spacebee_commander.communication import Communication
from spacebee_commander.commands_loader import load_commands


class Commander:

    telecommands = load_commands().values()
    messageManager = MessageManager()
    communication = Communication()

    def __init__(self):
        pass

    def getTelecommand(self,id):
        "Retrieve the telecommand using its telecommand ID."
        for telecommand in self.telecommands:
            if telecommand.getOperationNumber() == id:
                return telecommand

    def send(self, telecommand):
        "SEND. Consists of a single message sent without expecting a response."
        interaction_type=1
        message = self.messageManager.make_message(telecommand,interaction_type)
        self.communication.send(message)

    def submit(self, telecommand):
        "SUBMIT. It consists of a message with an acknowledgement response. It return True if ACK is okay and False otherwise "
        interaction_type=2
        message = self.messageManager.make_message(telecommand,interaction_type)
        self.communication.send(message)
        response=self.communication.receive()
        if response != None:
            ack=self.messageManager.unpack(response)

            if ack:
                print("ACK")
                return True
            else:
                print("No ACK")
                return False
        else: 
            print("Error no response receive")
            return False

    def request(self, telecommand):
        "REQUEST. In of a message with a response message. It returns the message if everything is okay, False otherwise"

        interaction_type=3
        message = self.messageManager.make_message(telecommand,interaction_type)
        self.communication.send(message)

        response=self.communication.receive()

        if response!= None:
            unpack_response=self.messageManager.unpack(response)
            response_dict=telecommand.parseOutputArguments(unpack_response)
            print(f"Response_dict: {response_dict}")
            return response_dict
        else:
            print("Error no response receive")
            return False

    def send_message(self,telecommand,interaction_type):
        "Receive a telecommand and interaction type and then send the corresponding interaction."
        if interaction_type==1:
            return self.send(telecommand)
        elif interaction_type==2:
            return self.submit(telecommand)
        elif interaction_type==3:
            return self.request(telecommand)
