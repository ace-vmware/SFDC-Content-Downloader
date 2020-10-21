#! python3

import webbrowser, os, glob, time, shutil, easygui
from simple_salesforce import Salesforce

# Login to SalesForce
# login_items = easygui.multpasswordbox(
#     'Please see the ReadMe.txt for instructions on how to procure your SalesForce Lightning Security Token. '
#     '\n\nYour username will be like \'jappleseed@vmware.com.gs\'', 'SalesForce Login', ['Username', 'Password'])
#
# username = login_items[0]
# password = login_items[1]

# Login to SalesForce
sf = Salesforce(
    username=os.environ["sf_username"],
    password=os.environ["sf_password"],
    security_token=os.environ["SECURITY_TOKEN"]
)

# Finds account id, case number, and href for recordid for all NOT closed tickets
def CaseDetails(TSE, STATUS=None):
    TSE = TSE.upper()
    STATUS = STATUS.upper()

    full_CaseDetails_dict = {}

    # Base query off Status
    if STATUS == 'OPEN' or STATUS == 'PENDING':
        opCases = sf.query(f"SELECT AccountId, Id, GSS_Case_Number__c, CaseNumber, GSS_Case__c FROM Case WHERE Case_Owner_Name__c = '{TSE}' AND Status = '{STATUS}'")
    elif STATUS == 'NOT CLOSED':  # Not Closed or all Open/Pending
        STATUS = 'CLOSED'
        opCases = sf.query(f"SELECT AccountId, Id, GSS_Case_Number__c, CaseNumber, GSS_Case__c FROM Case WHERE Case_Owner_Name__c = '{TSE}' AND Status != '{STATUS}'")


    # Cull query results down to only records
    records = opCases.get('records')

    # Pull details from individual records
    for record in records:
        record_num = records.index(record)

        # Find AccountID, Case Number, and Case Link
        AccountID = record.get('AccountId')

        CaseNumber = record.get('CaseNumber')

        CaseLink = record.get('GSS_Case__c').split('"')[1]

        # Find Account Name
        AccountName = ''
        AccountName_Query = sf.query(f"SELECT Name FROM Account WHERE Id = '{AccountID}'")
        AccountRecords = AccountName_Query.get('records')
        for account_record in AccountRecords:
            nonstripped_AccountName = account_record.get('Name')
            for letter in nonstripped_AccountName:
                if str(letter).isalnum() or str(letter).isspace():
                    AccountName += letter
                else:
                    pass

        # Find Documents
        CaseId = record.get('Id')
        Documents_Query = sf.query(f"SELECT ContentDocumentId,Id,IsDeleted,LinkedEntityId,"
                                   f"ShareType,SystemModstamp,Visibility "
                                   f"FROM ContentDocumentLink "
                                   f"WHERE LinkedEntityId = '{CaseId}'")
        DocumentsRecords = Documents_Query.get('records')
        LatestPublishedVersionId_list = []
        for document_record in DocumentsRecords:
            ContentDocumentId = document_record.get('ContentDocumentId')
            LatestPublishedVersionId = sf.ContentDocument.get(f'{ContentDocumentId}').get('LatestPublishedVersionId')
            LatestPublishedVersionId_list.append(LatestPublishedVersionId)

        # Create smaller dictionary
        indv_CaseDetails_dict = {'AccountName': AccountName, 'AccountID': AccountID, 'CaseNumber': CaseNumber, 'CaseLink': CaseLink, 'VersionIds': LatestPublishedVersionId_list}

        # Add smaller dictionaries to larger dictionary
        full_CaseDetails_dict['Case_' + str(record_num)] = indv_CaseDetails_dict

        # TOGGLE to Open pages
        # webbrowser.open('https://vmware-gs.lightning.force.com' + CaseLink)

        # Create Directories
        doc_folder = os.path.join(os.environ['USERPROFILE'], 'Documents')
        if not os.path.exists(os.path.join(doc_folder, 'Case Files', f'{AccountName}', f'{CaseNumber}')):
            os.makedirs(os.path.join(doc_folder, 'Case Files', f'{AccountName}', f'{CaseNumber}'))

        # TOGGLE to download content
        attachment_count = len(LatestPublishedVersionId_list)
        for attachment in LatestPublishedVersionId_list:
            webbrowser.open(f'https://vmware-gs.lightning.force.com/sfc/servlet.shepherd/version/download/' + attachment)

        # Place downloaded content into folders
        time.sleep(10)
        downloads_folder = os.path.join(os.environ['USERPROFILE'], 'Downloads')
        files_path = os.path.join(downloads_folder, '*')
        files = sorted(glob.iglob(files_path), key=os.path.getctime, reverse=True)
        latest_files = files[:attachment_count]
        for i in latest_files:
            while i.endswith('.crdonwload') or i.endswith('.tmp'):
                time.sleep(1)
            attachment_destination = os.path.join(doc_folder, 'Case Files', f'{AccountName}', f'{CaseNumber}', os.path.basename(str(i)))
            shutil.move(i, attachment_destination)

    return full_CaseDetails_dict

var = easygui.multenterbox('Please enter the first and last name of the person whose cases you want to download.\n\nAcceptable statuses are: \'Open\', \'Pending\', and \'Not Closed\' ', 'Find Documents', ['TSE Name', 'Case Status'])
CaseDetails(var[0], var[1])


"""
Case Id = 500f400000Uq8TaAAJ

SELECT ContentDocumentId 
FROM ContentDocumentLink 
WHERE LinkedEntityId = '500f400000Uq8TaAAJ'

This returns a list of ContentDocumentID associated with the CaseId/LinkedEntityId (500f400000Uq8TaAAJ)
example ContentDocumentID = 069f400000HCRQ3AAP

Use ContentDocumentID to search for LastPublishedVersionID
SELECT LatestPublishedVersionId 
FROM ContentDocument 
WHERE Id = '069f400000HCRQ3AAP'

LastPublishedVersionID = 068f400000Ioh2tAAB

Use LastPublishedVersionID within this API to find VersionData
/services/data/v48.0/ContentVersion/068f400000Ioh2tAAB/VersionData

Downloads file.
"""