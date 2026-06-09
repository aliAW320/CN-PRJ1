Users={}
files = {}
online_users = {}
class User :
    def __init__(self, name , password) :
        self.name = name
        self.password = password
    def __str__(self) :
        return f"User(name={self.name})"
    
    def register(name , password) :
        if name in Users :
            return False
        else :
            Users[name] = password
            return True
        
    
    def login(name , password , client_socket) :
        if (name in Users )and (Users[name] == password) and (name not in online_users) :
            online_users[name] = client_socket
            return True , "ok" ,User(name , password)
        elif name in online_users:
            return False , "user already online" ,None
        else :
            return False , "name or password is incorrect" , None
        

    def logout(self) :
        if self.name in online_users :
            del online_users[self.name]
            return True
        else :
            return False 
    def exit(self) :
        if self.name in online_users :
            del online_users[self.name]
            return True
        else :
            return False
# class Message :
#     def __init__(self, sender, receiver, content) :
#         self.sender = sender
#         self.receiver = receiver
#         self.content = content
#     def __str__(self) :
#         return f"Message(sender={self.sender}, receiver={self.receiver}, content={self.content})"
def list_online_users(self) :
    if self.name in online_users :
        online_users_list = list(online_users)
        online_users_list.remove(self.name)
        if len(online_users_list) == 0 :
               return True , 'you are the only online user' 
        return True , online_users_list
    else :
        return False , None
