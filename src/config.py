#!/usr/bin/python
# -*- coding: UTF-8 -*-

'''
Created on 7 juin 2012

@author: maxisoft
'''

import sqlite3
from base64 import b64decode, b64encode

import zlib
import socket
import md5
import os
import sys
import random

from Crypto.Cipher import AES

from time import strftime, localtime, strptime, mktime, time

from LogIt import logit as logclass
logit = logclass()

class config(object):
    '''
    Gestion de la Config sqlite du bot
    '''


    def __init__(self):
        '''
        Constructor 
        ''' 
        try:
            os.chdir(os.path.dirname(sys.argv[0]))
        except:
            pass
        finally:
            os.chdir('./config')
                    
        #db
        if not os.path.exists('config.db'):
            logit.log("Erreur, retelecharger le programme")
            raise Exception("""Erreur, retelecharger le programme""")
        
        self.conn = sqlite3.connect('config.db')
        self.__c = self.conn.cursor()
        
#    def __del__(self):
#        del(self.__c)
#        self.conn.close()
        
    def getLogin(self):
        '''Retourne un dict contenant l'utilisateur (le 1er) et le password.'''
        
        self.__c.execute("""SELECT
                multiacc.user,
                multiacc.passw
            FROM
                multiacc
            GROUP BY
                multiacc.user
            ORDER BY
                multiacc.prior ASC 
            LIMIT 1;""")
        sqlres = self.__c.fetchone()
        
        if not sqlres:
            logit.log("Vous devez configurer le bot.")
            raise Exception("Vous devez configurer le bot.")

        
        return {'user':str(sqlres[0]),'passw':self.decrypt(sqlres[1])}
        
        
#    def setLogin(self, user, passw):
#        user = (str(user),)
#        passw = (self.crypt(passw),)
#        self.__c.execute("""UPDATE "main"."cfg" SET "value"=? WHERE ("param"='user')""", user)
#        self.__c.execute("""UPDATE "main"."cfg" SET "value"=? WHERE ("param"='passw')""", passw)
#        self.conn.commit()
    
    def getVersionNbr(self):
        self.__c.execute('SELECT value FROM "main"."cfg" WHERE param="Version"')
        return str(self.__c.fetchone()[0])
    
    def getHeader(self):
        self.__c.execute('SELECT value FROM "main"."cfg" WHERE param="User-Agent"')
        return str(self.__c.fetchone()[0])
    
    def getTopName(self, id):
        id = (int(id),)
        self.__c.execute('SELECT Nom FROM "main"."TOP" WHERE VoteId=?', id)
        return str(self.__c.fetchone()[0])
        
    
    #---------------------------------------
    # Time Here
    
    def writeTime(self):
        '''Ecrit le temps actuel dans la db'''
        curtime = (strftime("%d/%m/%Y %H:%M", localtime()),)
        self.__c.execute("""UPDATE "main"."cfg" SET "value"=? WHERE ("param"='lastrun')""", curtime)
        self.conn.commit()
            
    def getTime(self):
        '''retourne un objet temp qui est stock� dans la db'''
        time = strptime('01/01/2000 00:00', "%d/%m/%Y %H:%M")
        
        try:
            self.__c.execute('SELECT value FROM "main"."cfg" WHERE param="lastrun"')
            time = strptime(str(self.__c.fetchone()[0]), "%d/%m/%Y %H:%M")
        except:
            pass
            
        return time
    
    
    def difTime(self):
        """ Retourne la differance(en seconde) entre le temps du log et le temps actuel """
        
        return int(mktime(localtime()) - mktime(self.getTime()))
        
    #--------------------------------------- 
    # Crypto Here  
    
    def __getComputerMD5Name(self):
        """Pour Crypter le password"""
        return str(md5.new(socket.gethostname()).hexdigest())
    
    
    
    
    def crypt(self, string):
        """Algo de keke ..."""
        
        def encipher(S):
            return AES.new(self.__getComputerMD5Name(),AES.MODE_PGP).encrypt(S)
        
        computerName = self.__getComputerMD5Name()
        string = encipher(b64encode(string))
        return b64encode(zlib.compress(string) + computerName[0:int(computerName[-1], 16)])
    
    def decrypt(self, cstring):
        """Algo de kiki ..."""
        
        def decipher(S, n=3):
            return AES.new(self.__getComputerMD5Name(),AES.MODE_PGP).decrypt(S)
        
        computerName = self.__getComputerMD5Name()
        return b64decode(decipher(zlib.decompress(b64decode(cstring).replace(computerName[0:int(computerName[-1], 16)], ''))))
    
    def useProxy(self):
        try:
            os.chdir(os.path.dirname(sys.argv[0]))
        except:
            pass
        return os.path.exists('./proxy.txt') # TODO mieux
    
        
### -------------------------------------------       

 
class ProxyConfig(config):
    
    def __init__(self):
        config.__init__(self)
        self.__c = self.conn.cursor()
        
        
    def setLogin(self , user, passw, id=None):
        sqlparma = [str(user), self.crypt(passw), ]
        if id != None:
            sqlparma.insert(0, int(id))
            self.__c.execute("""INSERT OR REPLACE INTO "main"."multiacc" (prior, user, passw) VALUES (?, ?, ?);""", sqlparma)
            self.conn.commit()
        else:
            self.__c.execute("""INSERT OR REPLACE INTO "main"."multiacc" (user, passw) VALUES (?, ?);""", sqlparma)
            self.conn.commit()
    
    def writeTime(self, user=None):
        
        config.writeTime(self)
        if user != None:
            #print time()
            self.__c.execute("""UPDATE "main"."multiacc" SET "lastVote"=strftime('%s','now') WHERE ("user"=?);""", (str(user),))
            self.conn.commit()
            
    def getReadyacc(self):
        '''Retourne un tuple de dict de tous les comptes qui on voté il y a plus de 2h'''      
        self.__c.execute(
         """SELECT
                multiacc.user,
                multiacc.passw
            FROM
                multiacc
            WHERE
                strftime('%s', 'now') - multiacc.lastVote > ?
            GROUP BY
                multiacc.user
            ORDER BY
                multiacc.prior ASC ;""",(int(2*60*60+random.random()*60*3),))
            
        return tuple({'user':str(item[0]),'passw':self.decrypt(item[1])} for item in self.__c.fetchall())
    
        
    def getAllacc(self):
        '''Retourne un tuple de dict de tous les comptes'''
        self.__c.execute(
         """SELECT
                multiacc.user,
                multiacc.passw
            FROM
                multiacc
            GROUP BY
                multiacc.user
            ORDER BY
                multiacc.prior ASC ;""")
            
        return tuple({'user':str(item[0]),'passw':self.decrypt(item[1])} for item in self.__c.fetchall())
    
    def deleteAll(self):
        self.__c.execute("""DELETE FROM "main"."multiacc";""")
        self.conn.commit()
        self.__c.execute("""DELETE FROM "main"."sqlite_sequence";""")
        self.conn.commit()
### -------------------------------------------        

if __name__ == '__main__':
    debug = 1
    
    if debug:
#        a = ProxyConfig()
##        a = config()
#        print a.getTime()
#        a.writeTime()
#        print a.getTime()
#        print a.difTime()
#        print a.getTopName(3)
#        print a.getReadyacc()
        #a.setLogin('coucou', 'passw')
        #a.writeTime('se')
        a = config()
        #print a.getLogin()
        c = a.crypt(u'²&é"\'(-è_çà)=~#{[|`\^@]}azertyuiopqsdfghjklmwxcvbn0123456789,;:!<>^$ù*,;:!¨£%µ?./§')
        print c
        print len(c)
        print a.decrypt(c),len(a.decrypt(c))
        a = ProxyConfig()
        print a.getAllacc()
        def test(user,passw):
            print user,passw
        
        test(**a.getAllacc()[0])
        
        
        
    else:
        a = config()
        print """
    
     __      __   _         ____        _   
     \ \    / /  | |       |  _ \      | |  
      \ \  / /__ | |_ ___  | |_) | ___ | |_ 
       \ \/ / _ \| __/ _ \ |  _ < / _ \| __|
        \  / (_) | ||  __/ | |_) | (_) | |_ 
         \/ \___/ \__\___| |____/ \___/ \__|
                                            
                                            
    
    
        """
    
        print '---  Configuration  ---'
        a.setLogin(str(raw_input("\n\nEntrez le nom d'Utilisateur\n")).strip(), str(raw_input("\n\nEntrer le mot de passe\n")).strip())
        raw_input('\n\n Ok. Vous pouvez lancer le bot maintenant')
        
        #print a.getLogin()
    pass
