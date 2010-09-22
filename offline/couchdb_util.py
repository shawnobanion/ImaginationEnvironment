import couchdb

def get_doc(db, doc_id):
    MAX_GET_ATTEMPTS = 3
    for i in range(0, MAX_GET_ATTEMPTS):
        try:
            doc = db[doc_id]
            print 'Successfully retrieved couchdb document id [' + str(doc_id) + ']'
            return doc
        except Exception, e:
            print 'Error while retrieving couchdb document id [' + str(doc_id) + ']'
            print e
    print 'Reached maximum number of get attempts (' + str(MAX_GET_ATTEMPTS) + ').'

def update_doc(db, doc):
    MAX_UPDATE_ATTEMPTS = 3
    for i in range(0, MAX_UPDATE_ATTEMPTS):
        try:
            db[doc.id] = doc
            print 'Successfully updated couchdb document id [' + str(doc.id) + ']'
            return
        except Exception, e:
            print 'Error while updating couchdb document id [' + str(doc.id) + ']'
            print e
    print 'Reached maximum number of update attempts (' + str(MAX_UPDATE_ATTEMPTS) + '). Document not updated.'

def store_doc(db, doc):
    MAX_STORE_ATTEMPTS = 3
    for i in range(0, MAX_STORE_ATTEMPTS):
        try:
            db.save(doc)
            print 'Successfully stored couchdb document'
            return
        except Exception, e:
            print 'Error while storing couchdb document'
            print e
    print 'Reached maximum number of store attempts (' + str(MAX_STORE_ATTEMPTS) + '). Document not stored.'
