import socket
import time
import random
import threading
from threading import Lock
import collections # provides a double-ended queue and is implemented as a doubly-linked list internally
import queue
import pickle
import hashlib
import numpy as np
import shelve
import sys



blockchain = collections.deque()
depth = 0
Q = queue.Queue()
Q1 = queue.Queue()

sock = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
udp_host = socket.gethostbyname("")
sock.setblocking(False)
udp_port = 45935

sock.bind((udp_host,udp_port))
lcip = "127.0.0.1"

active1 = True
active2 = True
active3 = True
active4 = True
active5 = True


def send_all(msg):
    if active1 == True:
        sock.sendto(msg,(lcip,45931))
    if active2 == True :
        sock.sendto(msg,(lcip,45932))
    if active3 == True:
        sock.sendto(msg,(lcip,45933))
    if active4 == True:
        sock.sendto(msg,(lcip,45934))


def send_port(msg,id):
    if id == 1:
        sock.sendto(msg,(lcip,45931))
    if id == 2:
        sock.sendto(msg,(lcip,45932))
    if id == 3:
        sock.sendto(msg,(lcip,45933))
    if id == 4:
        sock.sendto(msg,(lcip,45934))
    if id == 5:
        sock.sendto(msg,(lcip,45935))

def nonce(a):
    print("calculating nonce")
    if(len(blockchain)!=0):
        print("previous blockchain",blockchain[-1].encode('utf-8'))
        previous_block = blockchain[-1].encode('utf-8')
    else:
        print("no previous block")


    while True:
        r_value = random.randint(0,15)
        r_value1 = r_value
        r_value = bytes(r_value)
        x = hashlib.sha256(a)
        x.update(r_value)
        if(len(blockchain)!= 0):
            x.update(previous_block)
        z = x.hexdigest()
        print(z)
        print(z[63])
        lastdigit = int(z[63],16)
        if lastdigit >=0 and lastdigit <=4:
            print("good")
            print("heyyyyyy",r_value1)
            return r_value1

depth = 0
ballotnum = [0,5,0]
acceptnum = 0
acceptval = 0
accepted_acks = 0
promise_acks = 0
balance = 100
credit = 100

def restart_election():
    global promise_acks
    global accepted_acks
    while(1):
        time.sleep(1)
        while(Q.empty()==False):
            x = random.randint(0,10)
            time.sleep(x)
            print("starting leader election")
            ballotnum[0] = ballotnum[0] + 1
            ballotnum[1] = 5
            ballotnum[2] = len(blockchain)
            transaction1 = transaction
            print(transaction1)
            preparemsg = ("prepare",ballotnum)
            preparemsg = pickle.dumps(("prepare",ballotnum))
            send_all(preparemsg)
            time.sleep(5)
            accepted_acks = 0
            promise_acks = 0
            print("DONE")

def communication_thread():

    global ballotnum
    global acceptnum
    global acceptval
    global promise_acks
    global accepted_acks
    global Q
    global Q1
    global balance
    global credit
    global depth
    global blockchain

    while(1):

        try:
            msg = sock.recvfrom(1246)
            if msg!=socket.error:
                msg = pickle.loads(msg[0])
                if msg[0] == "prepare":
                    time.sleep(0.5)
                    if(depth <= msg[1][2]):
                        if msg[1][0] > ballotnum[0]:
                            ballotnum = msg[1]
                            promisemessage = ("promise",ballotnum,acceptnum,acceptval)
                            print("sending promise to, ", msg[1][1])
                            promisem = pickle.dumps(promisemessage)
                            send_port(promisem,msg[1][1])
                        else:
                            if msg[1][0] == ballotnum[0]:
                                if msg[1][1] > ballotnum[1]:
                                    ballotnum = msg[1]
                                    promisemessage = ("promise",ballotnum,acceptnum,acceptval)
                                    print("sending promise to, ", msg[1][1])
                                    promisem = pickle.dumps(promisemessage)
                                    send_port(promisem,msg[1][1])
                    else:
                        print("ack : sending update for blockchain")
                        msgx = pickle.dumps(("update for block",blockchain))
                        send_port(msgx,msg[1][1])

                if msg[0] == "update for block":
                    if depth < len(msg[1]):
                        print("new blockchain received, fixing state of blockchain")
                        blockchain = msg[1]
                        depth = len(blockchain)

                if msg[0] == "promise":
                    print("promise ack")
                    promise_acks = promise_acks + 1

                    if promise_acks == 2 and promise_acks < 3:
                        list1 = [Q1.get()]
                        while(Q1.empty()==False):
                            list1.append(Q1.get())
                        for i in Q.queue:
                            Q1.put(i)
                        x = np.array(list1)
                        block_hash = hashlib.sha256(x)
                        Nonce = nonce(x)
                        print("Nonce : ", Nonce)
                        Nonce = bytes(Nonce)
                        block_hash.update(Nonce)
                        if(len(blockchain)!=0):
                            previous_block = blockchain[-1].encode('utf-8')
                            block_hash.update(previous_block)
                        print("hash(transaction||Nonce) : ",block_hash.hexdigest())
                        m = hashlib.sha256(x)
                        print("original : " , m.hexdigest())
                        print(list1)
                        acceptval = block_hash.hexdigest()
                        acceptm = ("accept",ballotnum,acceptval)
                        acceptm = pickle.dumps(acceptm)
                        print("sending accepts")
                        send_all(acceptm)

                if msg[0] == "accept":
                    if msg[1][0] > ballotnum[0]:
                        acceptnum = msg[1]
                        acceptval = msg[2]
                        acceptedm = ("accepted",ballotnum,1)
                        acceptedm = pickle.dumps(acceptedm)
                        print("sending accept to ", msg[1][1])
                        send_port(acceptedm,msg[1][1])
                    else:
                        if msg[1][0] == ballotnum[0]:
                            if msg[1][1] >= ballotnum[1]:
                                acceptnum = msg[1]
                                acceptval = msg[2]
                                acceptedm = ("accepted",ballotnum,1)
                                acceptedm = pickle.dumps(acceptedm)
                                print("sending accept to ", msg[1][1])
                                send_port(acceptedm,msg[1][1])

                if msg[0] == "accepted_value":
                    v = msg[1]
                    for i in msg[2]:
                        if i[1] == 5:
                            balance = balance + i[2]
                            credit = credit + i[2]
                    print("acceptval : ",v)
                    blockchain.append(v)
                    depth = len(blockchain)

                if msg[0] == "accepted":
                    accepted_acks = accepted_acks + 1
                    print("accept ack")

                    if accepted_acks == 2:
                        list_of_transactions = list()
                        for i in Q.queue:
                            list_of_transactions.append(i)
                            balance = balance - i[2]
                        print("acceptval : ",acceptval)
                        print("sending accepted val")
                        msgv = pickle.dumps(("accepted_value",acceptval,list_of_transactions))
                        Q.queue.clear()
                        send_all(msgv)
                        blockchain.append(acceptval)
                        depth = len(blockchain)

        except socket.error:
            time.sleep(1)
            pass

t2 = threading.Thread(target = communication_thread, daemon = True)
t2.start()
t3 = threading.Thread(target = restart_election, daemon = True)
t3.start()

while(1):
    global transaction
    x = input("\n1 = moeny Transaction = , 2 = faillink , 3 = failProcess , 4 = printBlockchain , 5 = printBalance , 6 = printQueue, 7 = recover state\n")
    if x == '1':
        accepted_acks = 0
        promise_acks = 0
        value = input("value = ")
        if int(value) <= credit:
            credit = credit - int(value)
            rcvr = input("reciever = ")
            transaction = [1,int(rcvr),int(value)]
            Q.put(transaction)
            Q1.put(transaction)
        else:
            print("value exceeds balance, try again")
            continue
    if x == '2':
        d = input("\n 1 = activate linke 2 = deactivate link: ")
        if(d=='2'):
            d2 = input("\n what link to deactivate 1 , 2 , 3 , 4 : ")
            if(d2=='1'):
                active1 = False
            if(d2=='2'):
                active2 = False
            if(d2=='3'):
                active3 = False
            if(d2=='4'):
                active4 = False
            if(d2=='5'):
                active5 = False
        if(d=='1'):
            d2 = input("\n what link to activate 1 , 2 , 3 , 4 : ")
            if(d2=='1'):
                active1 = True
            if(d2=='2'):
                active2 = True
            if(d2=='3'):
                active3 = True
            if(d2=='4'):
                active4 = True
            if(d2=='5'):
                active5 = True
    if x == '3':
        shfile = shelve.open("shelf_file")
        shfile['bc']= blockchain
        shfile['depth']= depth
        shfile['credit']= credit
        shfile['balance']= balance
        shfile['ballotnum']= ballotnum
        shfile['acceptval']= acceptval
        shfile['acceptnum']= acceptnum
        shfile.close()
        sys.exit()
    if x =='4':
        print(blockchain)
    if x =='5':
        print(balance)
    if x =='6':
        print(list(Q.queue))
    if x =='7':
        var = shelve.open("shelf_file")
        blockchain = var['bc']
        depth = var['depth']
        credit = var['credit']
        balance = var['balance']
        ballotnum = var['ballotnum']
        acceptval = var['acceptval']
        acceptnum = var['acceptnum']
        var.clear()
        var.clear()
