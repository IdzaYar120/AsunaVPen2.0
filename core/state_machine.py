class PetState:
    def __init__(self, name, loop=True):
        self.name = name
        self.loop = loop

class StateMachine:
    def __init__(self):
        self.current_state = "idle"
        
    def change_state(self, new_state):
        self.current_state = new_state
        return self.current_state