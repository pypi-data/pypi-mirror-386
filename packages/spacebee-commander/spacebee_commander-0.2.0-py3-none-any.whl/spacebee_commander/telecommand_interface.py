class SingletonMeta(type):
    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super().__call__(*args, **kwargs)
        return cls._instances[cls]


class TelecommandInterface(metaclass=SingletonMeta):

    interaction_stage = 1       # 8 bits	1 or 2 according to message order
    transaction_id = None       # Unique incremental identifier
    service= 1                  # 0 for telemetries (TM) or 1 for telecommands (TC)
    operation=None              # 16 bits	Unique identifier for a given telemetry or telecommand
    area_version=None           # 16 bits	Protocol version
    is_error_message=False      # 8 bit	Boolean value to indicate if is an error message (0x1 for true, 0x0 for false)
    body_length = None          # 16 bits	Longitude in bytes of the message body
    body= None

    name=""                     # string Name of the telecommand
    help=""                     # string Description and usage for the telecommand
    help_input=""               # string Description for the input arguments
    num_inputs=None             # int Number of input arguments for this command	
    def getOperationNumber(self):
        return self.operation

    def loadInputArguments(self,arg):
        "Load input arguments into the body and calculate the body length."
        raise NotImplementedError("Telecommand must implement this method")

    def parseOutputArguments(self,response):
        "Parse the output argument, where the response is a byte sequence, and return a dictionary."
        raise NotImplementedError("Telecommand must implement this method")
