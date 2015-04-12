from bson.objectid import ObjectId
import pymongo
import logging

class Database:
    logging.basicConfig(filename='web.log', level=logging.INFO, format='%(asctime)s %(message)s', datefmt='%m/%d/%Y %I:%M:%S %p')

    def __init__(self, dbName):
        self._dbName = dbName
        self._connection = None

        try:
            self._connection = pymongo.MongoClient('localhost',27017)
        except (pymongo.errors.OperationFailure, pymongo.errors.ConnectionFailure), e:
            logging.error('Problem with db connection: %s' % e)
    
    def getObjects(self,name,query={}):
        try:
            return self._connection[self._dbName][name].find(query)
        except Exception as e:
            logging.error('Database get %s operation failed: %s' % (name,e))
            return []
    
    def updatePerson(self,data):
        try:
            self._connection[self._dbName]['people'].update(
                {"_id": data.get('_id')},
                data,
                upsert=False #if no such document is found, don't create a new document         
            )
        except Exception as e:
                 logging.error('Database updatePerson operation failed: %s' % e)

    def getObject(self, name, field, id_):
        try:
            id_ = ObjectId(id_)
            return self._connection[self._dbName][name].find_one({field:id_})
        except Exception as e:
            logging.error('Database get %s operation failed: %s' % (name, e))
            return None
    
    def getEvent(self, id):
        return self.getObject('events', '_id', id)

    def addObject(self, name, data, primaryKey=''):
        try:
            connection = self._connection[self._dbName][name]
            if primaryKey == '':
                return connection.insert_one(data)
            else:
                connection.update(
                    {primaryKey:data.get(primaryKey)},
                    data,
                    upsert=True
                )
                return data['_id']
        except Exception as e:
            logging.error('Database add %s operation failed: %s' % (name,e))
        
    def addEvent(self, data):
        return self.addObject('events',data)

    def addUser(self, user):
        dict = user.__dict__ 
        return self.addObject('users',dict, 'social_id')

    def getUser(self,id):
        obj =self.getObject('users','_id', id)
        if obj:
            return User(**obj)
        else:
            return None

    def getUserBySocialId(self,id):
        obj = self.getObject('users','social_id',id)
        if obj:
            return User(**obj)
        else: 
            return None

    def removeEvent(self, id):
        id = ObjectId(id)
        collection = self._connection[self._dbName]['events']
        collection.remove({'_id':id})
