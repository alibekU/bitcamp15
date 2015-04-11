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

    def getPerson(self,id_):
        try:
            id_ = ObjectId(id_)
            return self._connection[self._dbName]['people'].find_one({'_id':id_})
        except Exception as e:
            logging.error('Database getPerson() operation failed: %s' % e)
            return None

    def getPeople(self):
        return self.getObjects('people')

    def getVolunteers(self):
        return self.getObjects('volunteers')

    def addObject(self, name, data):
        try:
            collection = self._connection[self._dbName][name]
            new_person = {}

            for key,value in data.items():
                new_person[key] = value
            
            return collection.insert(new_person)
        except Exception as e:
            logging.error('Database add %s operation failed: %s' % (name,e))
        
    def addPerson(self, data):
        return self.addObject('people',data)

    def addVolunteer(self, data):
        return self.addObject('volunteers',data)
