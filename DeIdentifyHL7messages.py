'''
A script (and a function) to partially de-identify an HL7 message.
Full de-identification is not possible without knowing the details of any HL7 extensions
that exist in the message, such as extra fields in segments, or Z segments.
And missed de-identification can occur if senders misuse standard fields for non-standard data,
such as putting the patient's birth name in withdrawn fields like the Social Security Number Field.
'''

import sys
import re
import glob
import argparse
import logging


# The next section can be used as a function in other code
# Paramater: segment - an array of HL7 segment (being the whole message, starting with MSH)
# Returnes: segments - the same array of HL7 segments, just de-idenitified
#
# The following imports and data are required by the deidentifyHL7message() function
#
import os.path
import base64
import random
import pandas as pd
from openpyxl import load_workbook
LoremIpsum = {}         # Paragraphs, sentences, words of random latin
LoremIpsum_PDF = None
LoremIpsum_PNG = None
LoremIpsum_GIF = None
LoremIpsum_JPG = None
LoremIpsum_TIFF = None
allText = []
allFT = []
wb = None               # The workbook of test demographic data
patients = []
doctors = []
providers = []
organisations = []
fieldSep = compSep = repSep = escChar = subCompSep = None

# Set the following variables at command run time
dataDir = './data/.'                # MUST CONTAIN the file LorumIpsum.txt
testHealthPopulation = 'testHealthPopulation.xlsx'

# This function will initialise itself with data from the 'dataDir'
# Specifically the files 'LoremIpsum.txt', 'LoremIpsum.pdf', 'LoremIpsum.png', 'LoremIpsum.gif', 'LoremIpsum.jpg', 'LoremIpsum.tiff' and the Excel Workbook testDemographics.xlsx
# which can be created with the mkHealthPopulation.py script (https://github.com/russellmcdonell/mkHealth_Population-Australia)
def deidentifyHL7message(segments):
    # Deidentify an HL7 message
    global LoremIpsum, LOremIpsum_PDF, LoremIpsum_PNG, LoremIpsum_GIF, LoremIpsum_JPG, LoremIpsum_TIFF, allText, allFT,  wb, patients, doctors, providers, fieldSep, compSep, repSep, escChar, subCompSep, dataDir
    if len(LoremIpsum) == 0:
        with open(os.path.join(dataDir, "LoremIpsum.txt"), 'r', newline='') as LoremIpsumFile:
            for para in LoremIpsumFile:
                paragraph = para.strip()
                paraLen = len(paragraph)
                if 'all' not in LoremIpsum:
                    LoremIpsum['para'] = []
                LoremIpsum['para'].append(paragraph)
                if 'text' not in LoremIpsum:
                    LoremIpsum['text'] = {}
                if paraLen not in LoremIpsum['text']:
                    LoremIpsum['text'][paraLen] = []
                LoremIpsum['text'][paraLen].append(paragraph)
                paragraphFT = paragraph
                at = 80
                nextBreak = paragraphFT[at:].find('. ')
                while nextBreak != -1:
                    paragraphFT = paragraphFT[:at + nextBreak + 1] + '\\.br\\' + paragraphFT[at + nextBreak + 2:]
                    at += nextBreak + 3
                    nextBreak = paragraphFT[at:].find('. ')
                paraFTlen = len(paragraphFT)
                if 'FT' not in LoremIpsum:
                    LoremIpsum['FT'] = {}
                if paraFTlen not in LoremIpsum['FT']:
                    LoremIpsum['FT'][paraFTlen] = []
                LoremIpsum['FT'][paraFTlen].append(paragraphFT)
                paragraphBytes = paragraph.encode('UTF-8')
                lines = paragraph.split('. ')
                for eachLine in lines:
                    line = eachLine.strip()
                    lineLen = len(line)
                    if lineLen not in LoremIpsum['text']:
                        LoremIpsum['text'][lineLen] = []
                    LoremIpsum['text'][lineLen].append(line)
                    lineBytes = line.encode('UTF-8')
                    words = line.split(' ')
                    for eachWord in words:
                        word = eachWord.strip()
                        if word[-1] == ',':
                            word = word[:-1]
                        wordLen = len(word)
                        if wordLen not in LoremIpsum['text']:
                            LoremIpsum['text'][wordLen] = []
                        LoremIpsum['text'][wordLen].append(word)
        allText = sorted(LoremIpsum['text'])
        allFT = sorted(LoremIpsum['FT'])
        with open(os.path.join(dataDir, 'LoremIpsum.pdf'), 'rb') as file:
            data = file.read()
            LoremIpsum_PDF = base64.b64encode(data)
        with open(os.path.join(dataDir, 'LoremIpsum.png'), 'rb') as file:
            data = file.read()
            LoremIpsum_PNG = base64.b64encode(data)
        with open(os.path.join(dataDir, 'LoremIpsum.gif'), 'rb') as file:
            data = file.read()
            LoremIpsum_GIF = base64.b64encode(data)
        with open(os.path.join(dataDir, 'LoremIpsum.jpg'), 'rb') as file:
            data = file.read()
            LoremIpsum_JPG = base64.b64encode(data)
        with open(os.path.join(dataDir, 'LoremIpsum.tiff'), 'rb') as file:
            data = file.read()
            LoremIpsum_TIFF = base64.b64encode(data)

    if wb is None:      # Test demographic data not yet loaded
        wb = load_workbook(os.path.join(dataDir, testHealthPopulation))
    if len(patients) == 0:          # Patient and Doctors not yet loaded
        ws = wb['HL7_PID']
        heading = True
        for row in ws.rows:
            if heading:
                heading = False
                continue
            patients.append(row[1].value)
        for sheet in ['Public Hospital Staff', 'Private Hospital Staff', 'GP Clinic Staff', 'Specialists']:
            ws = wb[sheet]
            data = list(ws.values)
            df = pd.DataFrame(data[1:], columns=data[0])
            dfData = df.to_dict(orient='records')
            for row in dfData:
                doctors.append(row)
            sheet = 'Public Hospitals'
            ws = wb[sheet]
            data = list(ws.values)
            df = pd.DataFrame(data[1:], columns=data[0])
            df.columns.values[1] = 'HPI-O'
            df.columns.values[2] = 'Name'
            dfData = df.to_dict(orient='records')
            for row in dfData:
                organisations.append(row)
            for sheet in ['Private Hospitals', 'GP Clinics', 'Specialist Services']:
                ws = wb[sheet]
                data = list(ws.values)
                df = pd.DataFrame(data[1:], columns=data[0])
                df.columns.values[0] = 'HPI-O'
                df.columns.values[1] = 'Name'
                dfData = df.to_dict(orient='records')
                for row in dfData:
                    organisations.append(row)
        ws = wb['HL7_PRD']
        heading = True
        for row in ws.rows:
            if heading:
                heading = False
                continue
            providers.append(row[1].value)

    # Deidentify the HL7 message
    if segments[0][0:3] == 'MSH':
        fieldSep = segments[0][3:4]
        compSep = segments[0][4:5]
        repSep = segments[0][5:6]
        escChar = segments[0][6:7]
        subCompSep = segments[0][7:8]
        if escChar == fieldSep:
            escChar = None
            subCompSep = None
        elif subCompSep == fieldSep:
            subCompSep = None
    else:
        fieldSep = '|'
        compSep = '^'
        repSep = '~'
        escChar = '\\'
        subCompSep = '&'
    PV1_9 = None
    for i, segment in enumerate(segments):
        seg = segment[0:3]
        fields = segment.split(fieldSep)
        # Chapter 2 Segments
        if seg == 'MSH':                                    # De-identify MSH-3,4,5,6
            # Sending Application, Sending Facility, Receiving Application, Receiving Facility
            for field in range(2, 6):
                mkText(fields, field)
        elif seg == 'MSA':                                  # De-identify MSA-3
            mkText(fields, 3)                           # Text message
        elif seg == 'NTE':                                  # De-identify NTE-3
            mkFT(fields, 3)                             # Comment
        # Chapter 3 Segments
        elif seg == 'EVN':                                  # De-identify EVN-5
            mkXCN(fields, 5, compSep, True)             # Operator ID
        elif seg == 'PID':                                  # De-identify PID - replace whole segment
            newPID = random.choice(patients)
            if newPID.find('<UR>') != -1:               # Preserve UR is possible
                PID3s = fields[3].split('repSep')
                for id in PID3s:
                    idParts = id.split(compSep)
                    if (len(idParts) > 4) and (idParts[4] == 'MR'):
                        newPID = newPID.replace('<UR>', idParts[0])
                        newPID = newPID.replace('<AUTH>', idParts[3])
                        break
                else:
                    newPID = newPID.replace('<UR>', str(99999999))
                    newPID = newPID.replace('<AUTH>', 'unknown')
            segments[i] = newPID
            continue
        elif seg == 'PV1':                                  # De-identify PV1-3,6,7,8,9,11,14,15,16,17,42,43,52
            for field in [3, 6, 11, 14, 15, 16, 42, 43]:        # Locations
                mkText(fields, field)
            mkXCN(fields, 7, compSep, False)            # Attending
            mkXCN(fields, 8, compSep, False)            # Referring
            mkXCN(fields, 9, compSep, False)            # Consulting
            if (len(fields) <= 9) or (fields[9] == ''):
                PV1_9 = None
            else:
                comps = fields[9].split(compSep)
                PV1_9 = comps[0]
            mkXCN(fields, 17, compSep, False)           # Admitting
            mkXCN(fields, 52, compSep, False)           # Other
        elif seg == 'PV2':                                  # De-identify PV2-22,23
            mkText(fields, 22)                          # Visit Protection Indicator
            mkXON(fields, 23)                           # Clinic Organisation Name
        elif seg == 'NK1':                                  # De-identify NK1-2,3,4,5,6,10,14,15,16,25,26,27,28,30,31,32,35
            pid = random.choice(patients)
            pidFields = pid.split(fieldSep)
            cpid = random.choice(patients)
            cpidFields = cpid.split(fieldSep)
            if (len(fields) > 2) and (fields[2] != ''):         # Name
                fields[2] = pidFields[5]
            mkText(fields, 3)           # Relationship
            if (len(fields) > 4) and (fields[4] != ''):
                fields[4] = pidFields[11]
            mkXTN(fields, 5, True)                      # Phone
            mkXTN(fields, 6, True)                      # Business phone
            mkText(fields, 10)                          # NoK Title
            mkXON(fields, 13)                           # Organisation Name
            if (len(fields) > 14) and (fields[14] != ''):       # Marital Status
                fields[14] = pidFields[16]
            if (len(fields) > 15) and (fields[15] != ''):       # Sex
                fields[15] = pidFields[8]
            if (len(fields) > 16) and (fields[16] != ''):       # DOB
                fields[16] = pidFields[7]
            if (len(fields) > 25) and (fields[25] != ''):       # Religion
                fields[25] = pidFields[17]
            if (len(fields) > 26) and (fields[26] != ''):       # Mother's Maiden Name
                fields[26] = pidFields[6]
            if (len(fields) > 27) and (fields[27] != ''):       # Nationality
                fields[27] = pidFields[28]
            if (len(fields) > 28) and (fields[28] != ''):       # Ethnicity
                fields[28] = pidFields[22]
            mkXPN(fields, 30)                           # Contact Person Name
            mkXTN(fields, 31,True)                      # Contact Person Telephone number
            mkXAD(fields, 32)                           # Contact Person Address
            if (len(fields) > 35) and (fields[35] != ''):       # Race
                fields[35] = cpidFields[10]
        elif seg == 'IAM':                                  # De-identify IAM-18,19
            mkXCN(fields, 18, compSep, True)            # Statused by person
            mkXON(fields, 19)                           # Statused by organisation
        elif seg == 'MRG':                                  # De-identify MRG-1,2,3,4,5,6,7
            for field in range(1, 7):
                if field < 3:                           # ID, Alt ID
                    mkCX(fields, field, True)
                elif field in [3, 5, 6]:                # Account and Visit IDs
                    fields[field] = mkText(fields, field)
                else:
                    mkCX(fields, field, False)          # Prior ID
            mkXPN(fields, 7)                            # Patient's Prior Name
        elif seg == 'PD1':                                  # De-identify PD1-3,4,10,12
            mkXON(fields, 3)                            # Organisation
            mkXCN(fields, 4, compSep, True)             # Primary Care Provider
            mkCX(fields, 10, True)                      # Duplicate Patient
            mkText(fields, 12)                          # Protection Indicator
            mkText(fields, 14)                          # Place of workship
        elif seg == 'DB1':                                  # De-identify DB1-3
            mkCX(fields, 3, True)                       # Disabled Person ID
        elif seg == 'PDA':                                  # De-identify PDA-2,5,8
            mkText(fields, 2)                           # Death location
            mkXCN(fields, 5, compSep, True)             # Death Certified by
            mkXCN(fields, 8, compSep, True)             # Autopsy Performed by
        # Chapter 4 Segments
        elif seg == 'ORC':                                  # De-identify ORC-10,11,12,19,21,22,24
            mkXCN(fields, 10, compSep, True)            # Entered by
            mkXCN(fields, 11, compSep, True)            # Verified by
            mkXCN(fields, 12, compSep, True)            # Ordering Provider
            mkText(fields, 13)                          # Enterer's location
            mkXTN(fields, 14, True)                     # Call-back telephone number
            mkXCN(fields, 19, compSep, True)            # Action by
            mkXON(fields, 21)                           # Ordering Facility name
            mkoXAD(fields, 22)                          # Ordering Facility address
            mkXTN(fields,23,True)                       # Ordering Facility phone number
            mkdXAD(fields, 24)                          # Ordering Provider address
        elif seg == 'OBR':                                  # De-identify OBR-4.2/5,13,16,20,21,28,32,33,34,35
            mkCE(fields, 4, False)                      # Universal Service ID (test)
            mkText(fields, 13)                          # Relevant clinican information
            mkXCN(fields, 16, compSep, True)            # Ordering Provider
            if (len(fields) > 20) and (fields[20] != ''):       # Filler field 1
                bits = fields[20].split(',')
                for j, bit in enumerate(bits):
                    if bit[j][0:3] == 'DR=':
                        if PV1_9 is None:
                            bits[j] = 'DR='
                        else:
                            bits[j] = 'DR=' + PV1_9
                fields[20] = ','.join(bits)
            mkText(fields, 21)                          # Filler field 2
            if (len(fields) > 28) and (fields[28] != ''):       # Results Copies To
                copies = fields[28].split(repSep)
                eachDr = set()
                for eachCopy in copies:
                    bits = eachCopy.split(compSep)
                    if len(bits) > 3:           # Compute DR code
                        eachCode = bits[1] + '~' + bits[2] + '~' + bits[3]
                        eachDr.add(eachCode)    # Assemble unique doctors
                copyDr = ''
                for j in range(len(list(eachDr))):     # Replace each unique doctor
                    mkXCN(fields, 28, compSep, True)
                    if copyDr != '':
                        copyDr += repSep
                    copyDr += fields[28]
                fields[28] = copyDr
            for field in [32, 33, 34,35]:
                # Principal Results Interpreter, Assistant Results Interpreter, Technicial, Transcriptionist
                if subCompSep is not None:
                    mkXCN(fields, field, subCompSep, False)
        elif seg == 'RXO':                                  # De-identify RXO-14,15
            mkXCN(fields, 14, compSep, True)            # Ordering Provider's DEA number
            mkXCN(fields, 15, compSep, True)            # Pharmacist verifier ID
        elif seg == 'RXE':                                  # De-identify RXE-13,14
            mkXCN(fields, 13, compSep, True)            # Ordering PRovider's DEA number
            mkXCN(fields, 14, compSep, True)            # Pharmacist verifier ID
        elif seg == 'RXD':                                  # De-identify RXD-9, 10
            mkText(fields, 9)                           # Dispense notes
            mkXCN(fields, 10, compSep, True)            # Dispensing prover
        # Chapter 5 Segments
        elif seg == 'DSP':                                  # De-identify DSP-3
            mkText(fields, 3)                           # Data line
        # Chapter 6 Segments
        elif seg == 'PR1':                                  # De-identify PR1-4,8,11,12
            mkText(fields, 4)                           # Procedure description
            mkXCN(fields, 8, compSep, True)             # Anaesthesiologisy
            mkXCN(fields, 11, compSep, True)            # Surgeon
            mkXCN(fields, 12, compSep, True)            # Procedure practitioner
        elif seg == 'GT1':                                  # De-identify GT1-3,4,5,6,7,16,17,18
            mkXPN(fields, 3)                            # Guarantor's name
            mkXPN(fields, 4)                            # Guarantors spouse's name
            mkXAD(fields, 5)                            # Guarantor address
            mkXTN(fields, 6, True)                      # Guarantor phone
            mkXTN(fields, 7, True)                      # Guarantor business phone
            mkXPN(fields, 16)                           # Guarantor employer name
            mkXAD(fields, 17)                           # Guarantor employer address
            mkXTN(fields, 18, True)                     # Guarantor employer phone
        elif seg == 'IN1':                                  # De-identify IN1-3,4,5,6,7,16,18,19,30
            mkCX(fields, 3)                             # Insurance company ID
            mkXON(fields, 4)                            # Insurance company name
            mkoXAD(fields, 5)                           # Insurance company address
            mkXPN(fields, 6)                            # Insurance company contact person
            mkXTN(fields, 7, True)                      # Insurance company phone
            mkXPN(fields, 16)                           # Name of insured
            if (len(fields) > 18) and (fields[18] != ''):       # Insured's Date of Birth
                pid = random.choice(patients)
                pidFields = pid.split(fieldSep)
                fields[18] = pidFields[7]
            mkXAD(fields, 19)                           # Insured's address
            mkXCN(fields, 30, compSep, True)            # Verification by
        elif seg == 'IN2':                                  # De-identify IN2-3,7,9,12,13,22,23,39,40,41,42,43,49,50,52,53
            mkXCN(fields, 3, compSep, True)             # Insured Employers ID
            # Medicaid case name, Military sponsor's name, Special converage approval name, Mother's maiden name, Employer Contact person name, Insured's contact person name
            for field in [7, 9, 22, 40, 49, 52]:
                mkXPN(fields, field)
            pid = random.choice(patients)
            pidFields = pid.split(fieldSep)
            if (len(fields) > 43) and (fields[43] != ''):       # Marital Status
                fields[43] = pidFields[16]
            if (len(fields) > 39) and (fields[39] != ''):       # Religion
                fields[39] = pidFields[17]
            if (len(fields) > 40) and (fields[40] != ''):       # Mother's Maiden Name
                fields[40] = pidFields[6]
            if (len(fields) > 41) and (fields[41] != ''):       # Nationality
                fields[41] = pidFields[28]
            if (len(fields) > 42) and (fields[42] != ''):       # Ethnicity
                fields[42] = pidFields[22]
            mkText(fields, 12)                          # Military Organisation
            mkText(fields, 13)                          # Military Station
            mkText(fields, 23)                          # Special coverage approval title
            mkXTN(fields, 50, True)                     # Employer contact person phone
            mkXTN(fields, 53, True)                     # Insured contact person phone
        elif seg == 'IN3':                                  # De-identify IN3-3,8,14,15,16,18,19,25
            for field in [3, 8, 14, 25]:
                # Certified by, Operator, Physician reviewer, Second opinion physician
                mkXCN(fields, field, compSep, True)
            mkText(fields, 15)                          # Certification contact
            mkXTN(fields, 16, True)                     # Certification contact phone
            mkCE(fields, 18, False)                     # Certification agency
            mkXTN(fields, 19, True)                     # Certification agency phone
        elif seg == 'ACC':                                  # De-identify ACC-3,7,8,9
            mkText(fields, 3)                           # Acccident Location
            mkXCN(fields, 7, compSep, True)             # Entered by
            mkText(fields, 8)                           # Accident description
            mkText(fields, 9)                           # Brought in by
        elif seg == 'ABS':                                  # De-identify ABS-1,5,8
            for field in [1, 5, 8]:
                # Discharge care provider, Attested by, Abstracted by
                mkXCN(fields, field, compSep, True)
        # Chapter 7 Segments
        elif seg == 'OBX':                                  # De-identify OBX-3,5,16
            datatype = fields[2]
            if datatype != 'ED':
                mkCE(fields, 3, False)                          # Observation ID
            if (len(fields) > 5) and (fields[5] != ''):         # Observation
                if datatype == 'AD':                            # an address
                    mkXAD(fields, 5)
                elif datatype in ['CE', 'CNE', 'CWE']:          # coded
                    mkCE(fields, 5, False)
                elif datatype == 'CF':                          # coded with FT
                    mkCE(fields, 5, True)
                elif datatype == 'FN':                          # family name
                    pid = random.choice(patients)
                    pidFields = pid.split(fieldSep)
                    comps = pidFields[5].split(compSep)
                    fields[5] = comps[0]
                elif datatype == 'PL':                          # person location
                    mkText(fields, 5)
                elif datatype == 'PN':                          # person name
                    mkXPN(fields, 5)
                elif datatype == 'TN':                          # telephone
                    fields[5] = mkXTN(fields, 5, False)
                elif datatype == 'ST':                          # text
                    fields[5] = textFor(fields[5])
                elif datatype == 'TX':                          # text
                    fields[5] = textFor(fields[5])
                elif datatype == 'FT':                          # formatted text
                    fields[5] = FTfor(fields[5])
                elif datatype == 'ED':                          # encapsulated data
                    comps = fields[5].split(compSep)
                    if comps[3] == 'Base64':
                        if comps[2].upper() == 'PDF':
                            comps[4] = LoremIpsum_PDF
                        elif comps[2].upper() == 'GIF':
                            comps[4] = LoremIpsum_GIF
                        elif comps[2].upper() == 'JPEG':
                            comps[4] = LoremIpsum_JPG
                        elif comps[2].upper() == 'TIFF':
                            comps[4] = LoremIpsum_TIFF
                        elif comps[2].upper() == 'png':
                            comps[4] = LoremIpsum_PNG
                        elif comps[2].upper() == 'HTML':
                            text = '<html><head></head><body>' + '<p>'.join(LoremIpsum['para']) + '</body></html>'
                            comps[4] = base64.b64encode(text.encode('UTF-8'))
                        elif comps[2].upper() == 'XHTML':
                            text = '<html><head></head><body><p>' + '</p><p>'.join(LoremIpsum['para']) + '</p></body></html>'
                            comps[4] = base64.b64encode(text.encode('UTF-8'))
                        else:
                            fields[3] = 'PDF^Display Format in PDF^AUSPDI'
                            comps[2] = 'PDF'
                            comps[4] = LoremIpsum_PDF
                    fields[5] = compSep.join(comps)
                elif datatype == 'XAD':                         # an address
                    fields[5] = mkXAD(fields, 5)
                elif datatype == 'XCN':                         # composite ID and name
                    mkXCN(fields, 5, compSep, False)
                elif datatype == 'XPN':                         # person name
                    fields[5] = mkXPN(fields, 5)
                elif datatype == 'XTN':                         # telephone
                    fields[5] = mkXTN(fields, 5, False)
            mkCE(fields, 15, False)                                    # Producers ID
            mkXCN(fields, 16, compSep, True)
        elif seg == 'PES':                                  # De-identify PES-1,2,3,4,7,8
            mkXON(fields, 1)                            # Sender organisation name
            mkXCN(fields, 2, compSep, True)             # Sender individual name
            mkoXAD(fields, 3)                           # Sender address
            mkXTN(fields, 4, True)                      # Sender telephone
            mkFT(fields, 7)                             # Sender event description
            mkFT(fields, 8)                             # Sender comments
        elif seg == 'PEO':                                  # De-identify PEO-7,13,14,15,16,17,19,20,21
            # Event descriptions from others/original reporter/patient/practitioner/autopsy
            for field in [13, 14, 15, 16, 17]:
                mkFT(fields, field)
            mkXAD(fields, 7)                            # Event location orrcured address
            mkXPN(fields, 19)                           # Primary observer name
            mkXAD(fields, 20)                           # Primary observer address
            mkXTN(fields, 21, True)                     # Primary observer phone
        elif seg == 'FAC':                                  # De-identify FAC-1,3,4,5,7,8
            mkText(fields, 1)                           # Facility ID
            mkoXAD(fields, 3)                           # Facility address
            mkXTN(fields, 4, False)                     # Facility phone
            mkXCN(fields, 5, compSep, True)             # Contact person
            mkdXAD(fields, 7)                           # Contact person address
            mkXTN(fields, 8,True)                       # Contact person phone
        # Chapter 8 Segments
        elif seg == 'OM1':                                  # De-identify OM1-6,8,9,10,11,16,17,27,28,29,32,37,39,40
            # Observation description, other names, preferred report name for the observation, preferred short name for observation,
            # Preferred long name for observation, Interpretation of observations, patient preparation,
            # Factors that may affect the observation, Description of test methods
            for field in [6, 8, 9, 10, 11, 32, 37, 39, 41]:
                mkText(fields, field)
            mkCE(fields, 16)                            # Observation producing department/section
            mkXTN(fields, 17, False)                    # Telephone number of section
            mkCE(fields, 27)                            # Outside Site(s) where observation may be performed
            mkoXAD(fields, 28)                          # Address of outside site(s)
            mkXTN(fields, 29, False)                    # Phone number of outside site(s)
            mkCE(fields, 33)                            # Contraditions to observation
        elif seg == 'OM7':                                  # De-identify OM7-20
            mkXCN(fields, 20, compSep, True)            # Ordered by
        elif seg == 'LOC':                                  # De-identify LOC-1,2,4,5,6
            mkText(fields, 1)                           # Primary Key Value - LOC
            mkText(fields, 2)                           # Location Description
            mkXON(fields, 4)                            # Organisation name
            mkoXAD(fields, 5)                           # Location address
            mkXTN(fields, 6, False)                     # Location telephone
        elif seg == 'LRL':                                  # De-identify LRL-1,4,5,6
            mkText(fields, 1)                           # Primary Key Value - LOC
            mkCE(fields, 4)                             # Location relationship ID
            mkXON(fields, 5)                            # Organisation Location relationship value
            mkText(fields, 6)                           # Patient Location relationship avlue
        elif seg == 'LDP':                                  # De-identify LDP-1,2,11
            mkText(fields, 1)                           # Primary Key Value - LOC
            mkCE(fields, 2)                             # Location department
            mkXTN(fields, 11, False)                    # Contact phone
        elif seg == 'LCC':                                  # De-identify LCC-1
            mkText(fields, 1)                           # Primary Key Value - LOC
        elif seg == 'CM0':                                  # De-identify CM0-5,9,10
            # Chairman of the study, Contact for study
            for field in [5, 9]:
                mkXCN(fields, field, compSep, True)
            mkXTN(fields, 10, False)                    # Contact's telephone number
        # Chapter 9 Segments
        elif seg == 'TXA':                                  # De-identify TXA-5,9,10,11,22,23
            # Primary Activity provider, Originator, Assigned document authenticator, distributed copies
            for field in [5, 9, 10, 11, 23]:
                mkXCN(fields, field, compSep, True)
            if (len(fields) > 22) and (fields[22] != ''):       # Authenticated person with timestamp
                # PPN - preserve the TS data if possible
                comps = fields[22].split(compSep)
                doc = random.choice(doctors)
                docComps = doc.split(compSep)
                for j in range(min(len(comps), len(docComps))):
                    if comps[j] == '':
                        continue
                    comps[j] = docComps[j]
                fields[22] = compSep.join(comps)
        # Chapter 10 Segments
        elif seg == 'ARQ':                                  # De-identify ARQ-15
            mkXCN(fields, 15, compSep, True)            # Placer Contact person
        elif seg == 'SCH':                                  # De-identify SCH-12,13,14,15,16,17,18,19,20,21,22
            # Placer Contact person, Filler Contact person, Entered by person
            for field in [12, 16, 20]:
                mkXCN(fields, field, compSep, True)
            # Placer Contact phone, Filler Contact phone, Entered by person phone
            for field in [13, 17, 21]:
                mkXTN(fields, field, False)
            # Place Contact address, Filler Contact addresss
            for field in [14, 18]:
                mkXAD(fields, field)
            # Placer Contact location, Filler Contact location, Entered by location
            for field in [15, 19, 22]:
                mkText(fields, field)
        elif seg == 'AIL':                                  # De-identify AIL-3
            mkText(fields, 3)                           # Location Resource
        elif seg == 'AIP':                                  # De-identify AIP-3
            mkXCN(fields, 3, compSep, True)             # Personal resource
        # Chapter 11 Segments
        elif seg == 'PRD':                                  # De-identify PRD - replace whole segment
            newPRD = random.choice(providers)
            segments[i] = newPRD
            continue
        elif seg == 'CTD':                                  # De-identify CTD-2,3,4,5
            mkXPN(fields, 2)                            # Contact Name
            mkXAD(fields, 3)                            # Contact address
            mkText(fields, 4)                           # Contact location
            mkXTN(fields, 5,True)                       # Contact phone
        # Chapter 12 Segments
        elif seg == 'ROL':                                  # De-identify ROL-4,10,11,12
            mkXCN(fields, 4, compSep, True)             # Role person
            mkCE(fields, 10)                            # Organisation Unit
            mkXAD(fields, 11)                           # address
            mkXTN(fields, 12, True)                     # phone
        elif seg == 'VAR':                                  # De-identify VAR-4,6
            mkXCN(fields, 4, compSep, True)             # Variance originator
            mkText(fields, 6)                           # Variance description
        # Chapter 13 Segments - none (Clinical Laboratory Automation)
        # Chapter 14 Segments - none (Application Management)
        # Chapter 15 Segments
        elif seg == 'AFF':                                  # De-identify AFF-2,3
            mkXON(fields, 2)                            # Professional organisation
            mkXAD(fields, 3)                            # Professional organisation address
        elif seg == 'EDU':                                  # De-identify EDU-6-8
            mkXON(fields, 6)                            # School
            # an organisation name ending in Medical/Medical Clinic/Medical Centre
            if fields[6].endswith('Medical'):
                fields[6] = fields[6][0:-7] + 'School'
            elif fields[6].endswith('Medical Clinic'):
                fields[6] = fields[6][0:-14] + 'School'
            elif fields[6].endswith('Medical Centre'):
                fields[6] = fields[6][0:-14] + 'School'
            mkXAD(fields, 8)                            # School address
        elif seg == 'STF':                                  # De-identify SFT-3,5,6,8.9.10,11
            pid = random.choice(patients)
            pidFields = pid.split(fieldSep)
            fields[3] = pidFields[5]                    # Staff name
            fields[5] = pidFields[8]                    # Staff sex
            fields[6] = pidFields[7]                    # Staff DOB
            mkCE(fields, 8)                             # Department
            mkCE(fields, 9)                             # Hospital service
            mkXTN(fields, 10, True)                     # Staff phone
            fields[11] = pidFields[11]                  # Staff address
            reps = pidFields[13].split(repSep)
            for rep in reps:
                comps = rep.split(compSep)
                if ((comps[1] == 'NET') and (comps[2] == 'Internet')):
                    fields[15] = comps[3]               # E-Mail address
                    break
            fields[17] = pidFields[16]                  # Marital status
            mkText(fields, 18)                          # Job title
            fields[22] = pidFields[20]                  # Driver's license no
            fields[27] = pidFields[10]                  # Race
            fields[28] = pidFields[22]                  # Ethnic Group

        segments[i] = fieldSep.join(fields)
    return segments

def textFor(text):
    # Return random Latin text of about the same length
    if len(text) <= allText[0]:
        return random.choice(LoremIpsum['text'][allText[0]])
    elif len(text) >= allText[-1]:
        return random.choice(LoremIpsum['text'][allText[-1]])
    textLen = len(text)
    nearestLen = min(allText, key=lambda x: abs(x - textLen))
    return random.choice(LoremIpsum['text'][nearestLen])

def FTfor(FT):
    # Return Formatted random Latin text of about the same length
    if len(FT) <= allFT[0]:
        return random.choice(LoremIpsum['FT'][allFT[0]])
    elif len(FT) >= allFT[-1]:
        return random.choice(LoremIpsum['FT'][allFT[-1]])
    FTlen = len(FT)
    nearestLen = min(allFT, key=lambda x: abs(x - FTlen))
    return random.choice(LoremIpsum['FT'][nearestLen])

def mkText(fields, field):
    # Replace all components and subcomponents with random Latin text of about the same lenth
    global compSep, subCompSep
    if (len(fields) <= field) or (fields[field] == ''):
        return
    comps = fields[field].split(compSep)
    for i in range(len(comps)):
        if subCompSep is not None:
            subComps = comps[i].split(subCompSep)
            for j in range(len(subComps)):
                if subComps[j] != '':
                    subComps[j] = textFor(subComps[j])
            comps[i] = subCompSep.join(subComps)
        else:
            if comps[i] != '':
                comps[i] = textFor(comps[i])
    fields[field] = compSep.join(comps)
    return

def mkFT(fields, field):
    # Replace the field contents with Formatted random Latin text of about the same length
    if (len(fields) <= field) or (fields[field] == ''):
        return
    fields[field] = FTfor(fields[field])
    return

def mkXCN(fields, field, sep, withRepeats):
    # Replace the field with a randomly selected doctor with one or more identifier
    global compSep, repSep
    if (len(fields) <= field) or (fields[field] == ''):
        return
    if sep != compSep:
        withRepeats = False
    doc = random.choice(doctors)
    doctor = ''
    if doc['Provider No'] != '':
        drBits = [doc['Provider No'], doc['Surname'], doc['First Name'], '', '', doc['Title'], '', '', 'AUSHICPR']
        doctor += sep.join(drBits)
    if withRepeats or ((doctor == '') and (doc['Prescriber No'] != '')):
        drBits = [doc['Prescriber No'], doc['Surname'], doc['First Name'], '', '', doc['Title'], '', '', 'AUSHIC' + '' + '' + '' +'PRES']
        if doctor != '':
            doctor += repSep
        doctor += sep.join(drBits)
    if withRepeats or ((doctor == '') and (doc['HPI-I'] != '')):
        drBits = [doc['HPI-I'], doc['Surname'], doc['First Name'], '', '', doc['Title'], '', '', 'AUSHIC' + '' + '' + '' +'NPI']
        if doctor != '':
            doctor += repSep
        doctor += sep.join(drBits)
    if sep == compSep:
        thisDoctorIDs = fields[field].split(repSep)
        for i in range(len(thisDoctorIDs)):
            thisIDbits = thisDoctorIDs[i].split(compSep)
            if (len(thisIDbits) > 8) and (thisIDbits[8] == 'AUSHICPR'):
                continue
            if (len(thisIDbits) > 11) and (thisIDbits[8] == 'AUSHIC') and (thisIDbits[11] in ['NI', 'PRES']):
                continue
            thisIDbits[0] = textFor(thisIDbits[0])
            if doctor != '':
                doctor += repSep
            doctor += compSep.join(thisIDbits)
        fields[field] = doctor
        return
    else:       # A doctor as the first 'component' in field
        comps = fields[field].split(compSep)
        comps[0] = doctor
        fields[field] = compSep.join(comps)
    return

def mkXON(fields, field):
    # Replace the field with a randomly selected organisation with one or more identifier
    global compSep, repSep
    if (len(fields) <= field) or (fields[field] == ''):
        return
    org = random.choice(organisations)
    fields[field] = org['Name'] + '^L^' + org['HPI-O'] + '^^^AUSHIC^NOI'
    return

def mkXTN(fields, field, withRepeats):
    # Replace the field with a randomly selected phone number or numbers trying to maintain like for like
    global repSep, compSep
    if (len(fields) <= field) or (fields[field] == ''):
        return
    pid = random.choice(patients)
    pidFields = pid.split(fieldSep)
    if pidFields[13] != '':
        allXTN += pidFields[13].split(repSep)
    if pidFields[14] != '':
        allXTN += pidFields[14].split(repSep)
    theseXTNs = fields[field].split(repSep)
    foundXTNs = []
    for i in range(len(theseXTNs)):
        theseComps = theseXTNs[i].split(compSep)
        if len(theseComps) <= 2:
            continue
        for j in range(len(allXTN)):
            allComps = allXTN[j].split(compSep)
            if len(allComps) <= 2:
                continue
            if theseComps[2] == allComps[2]:        # We have a match
                if not withRepeats:
                    fields[field] = allXTN[j]
                    return
                theseXTNs[i] =allXTN[j]
                foundXTNs.append(i)
    if not withRepeats:
        fields[field] = allXTN[0]
        return
    for i in range(len(theseXTNs)):
        if i in foundXTNs:
            continue
        theseComps = theseXTNs[i].split(compSep)
        theseComps[0] = textFor(theseComps[0])
        theseComps[4] = textFor(theseComps[4])
        theseComps[7] = textFor(theseComps[7])
        theseXTNs[i] = compSep.join(theseComps)   
    fields[field] = repSep.join(theseXTNs)
    return

def mkCX(fields, field, withRepeats):
    # Replace the field with a randomly selected person id or ids trying to maintain like for like
    global repSep, compSep
    if (len(fields) <= field) or (fields[field] == ''):
        return
    pid = random.choice(patients)
    pidFields = pid.split(fieldSep)
    theseIDs = fields[field].spit(repSep)
    newIDs = pidFields[3].split(repSep)
    foundIDs = []
    for i in range(len(theseIDs)):
        theseComps = theseIDs[i].split(compSep)
        if len(theseComps) <= 5:
            continue
        for j in range(len(newIDs)):
            newComps = newIDs[j].split(compSep)
            if len(newComps) <= 5:
                continue
            if ((theseComps[4] == newComps[4]) and (theseComps[5] == newComps[5])):
                if not withRepeats:
                    fields[fields] = newIDs[j]
                    return
                theseIDs[i] = newIDs[j]
                foundIDs.append(i)
                break
    if not withRepeats:
        fields[field] = newIDs[0]
        return
    for i in range(len(theseIDs)):
        if i in foundIDs:
            continue
        theseComps = theseIDs[i].split(compSep)
        theseComps[0] = textFor(theseComps[0])
        theseIDs[i] = compSep.join(theseComps)
    fields[fields] = repSep.join(theseIDs)
    return

def mkXPN(fields, field):
    # Replace the field with a randomly selected person name
    if (len(fields) <= field) or (fields[field] == ''):
        return
    pid = random.choice(patients)
    pidFields = pid.split(fieldSep)
    fields[field] = pidFields[5]
    return

def mkXAD(fields, field):
    # Replace the field with a randomly selected patient address
    if (len(fields) <= field) or (fields[field] == ''):
        return
    pid = random.choice(patients)
    pidFields = pid.split(fieldSep)
    fields[field] = pidFields[11]
    return

def mkdXAD(fields, field):
    # Replace the field with a randomly selected doctor address
    mkoXAD(fields, field)           # Doctors work at organisations

def mkoXAD(fields, field):
    # Replace the field with a randomly selected organisation address
    global compSep
    if (len(fields) <= field) or (fields[field] == ''):
        return
    org = random.choice(organisations)
    fields[field] = compSep.join([org['Street No.'] + ' ' + org['Street Name'], org['Street Type'], org['Suburb'],  org['State'], org['Postcode']])

def mkCE(fields, field, withFT):
    # Replace code and description with random text
    global compSep
    if (len(fields) <= field) or (fields[field] == ''):
        return
    comps = fields[field].split(compSep)
    if (len(comps) > 0) and (comps[0] != ''):
        if withFT:
            comps[0] = FTfor(comps[0])
        else:
            comps[0] = textFor(comps[0])
    if (len(comps) > 1) and (comps[1] != ''):
        if withFT:
            comps[1] = FTfor(comps[1])
        else:
            comps[1] = textFor(comps[1])
    if (len(comps) > 3) and (comps[3] != ''):
        if withFT:
            comps[3] = FTfor(comps[3])
        else:
            comps[3] = textFor(comps[3])
    if (len(comps) > 4) and (comps[4] != ''):
        if withFT:
            comps[4] = FTfor(comps[4])
        else:
            comps[4] = textFor(comps[4])
    fields[field] = compSep.join(comps)
    return


# End of deIdentifyHL7message() function and associated data/functions


# Define a logging Formatter class
# To suppress program/level/datetime at the start of a logging record use
# logger.xxxx('message', extra={'raw_message':True})
class ConditionalFormatter(logging.Formatter):
    def format(self, record):
        if hasattr(record, 'raw_message') and record.raw_message:
            return record.getMessage()
        else:
            return super().format(record)


# This next section is plagurised from /usr/include/sysexits.h
EX_OK = 0               # successful termination
EX_WARN = 1             # non-fatal termination with warnings

EX_USAGE = 64           # command line usage error
EX_DATAERR = 65         # data format error
EX_NOINPUT = 66         # cannot open input
EX_NOUSER = 67          # addressee unknown
EX_NOHOST = 68          # host name unknown
EX_UNAVAILABLE = 69     # service unavailable
EX_SOFTWARE = 70        # internal software error
EX_OSERR = 71           # system error (e.g., can't fork)
EX_OSFILE = 72          # critical OS file missing
EX_CANTCREAT = 73       # can't create (user) output file
EX_IOERR = 74           # input/output error
EX_TEMPFAIL = 75        # temp failure; user is invited to retry
EX_PROTOCOL = 76        # remote error in protocol
EX_NOPERM = 77          # permission denied
EX_CONFIG = 78          # configuration error


if __name__ == '__main__':
    '''
    The main code
    '''

    # Save the program name
    progName = (sys.argv[0])[0:-3]

    parser = argparse.ArgumentParser()
    parser.add_argument('-I', '--inputDir', metavar='inputDir', action='store', default="./input/.", help='The name of input directory (default "./input/.")')
    parser.add_argument('-O', '--outputDir', metavar='outputDir', action='store', default="./output/.", help='The name of the output directory (default "./output/.")')
    parser.add_argument('-D', '--dataDir', metavar='dataDir', action='store', default="./data/.", help='The name of the data directory (default "./data/.")')
    parser.add_argument('-v', '--verbose', metavar='loggingLevel', type=int, choices=range(0, 5), help='The level of logging\n\t0=CRITICAL,1=ERROR,2=WARNING,3=INFO,4=DEBUG')
    parser.add_argument('-T', '--testData', metavar='testData', action='store', default="testHealthPopulation.xlsx", help='The name of the test data Excel Workbook (default "testHealthPopulation.xlsx")')
    parser.add_argument('-l', '--logfile', metavar='logfile', action='store', help='The name of the log file')
    parser.add_argument('-L', '--logDir', metavar='logDir', action='store', default=".", help='The name of the logging directory (default ".")')
    args = parser.parse_args()

    # Set up logging
    loggingLevels = {0:logging.CRITICAL, 1:logging.ERROR, 2:logging.WARNING, 3:logging.INFO, 4:logging.DEBUG}
    logger = logging.getLogger(__name__)
    if args.verbose:
        logger.setLevel(loggingLevels[args.verbose])
    else:
        logger.setLevel(logging.WARNING)
    if args.logfile:
        handler = logging.FileHandler(os.path.join(args.logDir, args.logfile), mode='w')
    else:
        handler = logging.StreamHandler()
    logformat = progName + ' %(levelname)s[%(asctime)s]: %(message)s'
    dateformat = '%d/%m/%y'
    formatter = ConditionalFormatter(logformat, dateformat)
    handler.setFormatter(formatter)
    logger.addHandler(handler)

    # Parse the optional arguments
    inputDir = args.inputDir
    outputDir = args.outputDir
    dataDir = args.dataDir
    testHealthPopulation = args.testData

    # De-identify all the HL7 message files in the inputDir and write the de-identified messages out to the outputDir
    HL7files = glob.glob(os.path.join(inputDir, '*'))
    for HL7file in HL7files:
        with open(os.path.join(outputDir, os.path.basename(HL7file)), 'w', newline='\r') as outFile:
            with open(HL7file, 'r', newline='\r') as inFile:
                segments = []
                for line in inFile:
                    line = line.strip()
                    if line != '':
                        segments.append(line)
                deidentifyHL7message(segments)
                print('\r'.join(segments), file=outFile)



                   