class PrefixAlreadyExistException(Exception): 
   def __init__(self, message: str = "Prefix already exists"):
        self.message = message
        super().__init__(self.message)
        
        
        
        
class PrefixNotFoundException(Exception): 
   def __init__(self, message: str = "Prefix not found"):
        self.message = message
        super().__init__(self.message)        