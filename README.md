# De-identify-HL7-messages

Replace patient, provider, prescriber, practitioner, organisation and location data in HL7 messages

## Outline

Data is replaced , on a field by field basis, for each segment from two sources. Patients, providers, prescribers, practtitioners and organisatins are replaces with test patient/provider/practitioner/organisation data created by [mkHealth Population Australia](https://github.com/russellmcdonell/mkHealth_Population-Australia). This includes test identifiers, test addresses and test telephone numbers/mobile numbers/email addressees. By default, this data is in an Excel Workbook called 'testHealthPopulation.xlsx' in the data folder.

The second source is a number of paragraths of sentences constructed of random latin works - [Lorum Ipsum](https://www.lipsum.com/). The words are used where identifying codes need to be replaced. Shorter sentences are used where identifying code descriptions need to be repleaced. The whole text has also been convereted into a PDF document plus PNG/TIF/GIF/JPEG images for where Base64 encoded data of these types needs to be replaced. These files can be found, and must exist, in the data folder.

## Usage

Most of this code in DeidentifyHL7messages.py is functionality that is intended to be cut and pasted into other Python scrips. For instance you may have a script to extract HL7 messages from log files and you want to offer the option of de-identifying them on the fly.

There is an \_\_main\_\_ section which means that this can also be run as a standalone script. By default, it will read all the HL7 messages in the input folder and create de-identifyied version in the output folder.

## WARNING - DO NOT TRUST THIS CODE

It is impossible to create a full set of production HL7 messages which cover erery possible usage of every HL7 segment. Hence much of this code is untested; much of this code may not fit with the way you are using HL7. Certainly, Z-segments and site specific extensions to standard segments/fields etc are not covered. Fortunately the code is relatively easy to read, so it is easy to see which fields, in which segments are being processes and how they are being processed.

## What to de-identify

There is a lot, but you can choose which bits you want de-identified.

deidentify[] - This is a list of segments and/or fields to deidentify  
By default, deidentifyHL7message() will deidentify person and organisation related data (XCN and XON datatypes)
or potentially person related data, such as OBX-5 for FT/ED etc. datatypes, when the matching segment is listed in deidentify[].  
For other fields you'll need to specify both the segment and the field. e.g. to deidentify MSH-3 you would need ['MSH', 'MSH-3']

Fields not deidentified if just the segment is in deidentify[]  
MSH-3, MSH-4, MSH-5, MSH-6, MSA-3, NTE-3, PV1-3, PV1-6, PV1-11, PV1-14, PV1-15, PV1-16, PV1-42, PV1-43, PV2-22,
NK1-3, MRG-1, MRG-2, MRG-3, MRG-4, MRG-5, MRG-6, PD1-12, PD1-14, PDA-2, ORC-13, OBR-4, OBR-13, OBR-20, OBR-21,
RXD-9, ACC-3, OBX-5 [for CE, CNE, CWE and CF datatypes - all other datatype are deidentified if you select 'OBX'],
PES-7, PES-8, FAC-1, OM1-6, OM1-8, OM1-9, OM1-10, OM1-11, OM1-16, OM1-27, OM1-32, OM1-33, OM1-37, OM1-39, OM1-41,
LOC-1, LRL-1, LRL-4, LRL-5, LRL-6, LDP-1, VAR-6

So, what is deidentified, by default, when you specify a segment  
MSH, MSA, NTE - nothing  
EVN-5  
PID everything; the whole segment, but the MR number can be preserved and you can specify individual fields that are to be preserved  
PV1-7,8,9 17, 52  
PV2-23  
NK1-2,4,5,6,10,13,14,15,16,25,26,27,27,30,31,32,35, IAM-18,19  
MRG-7  
PD1-3,4,10  
DB1-3  
PDA-5,6  
ORC-10,11,12,14,19,21,22,23,24  
OBR-4,13,16,20[with DR=value copied from PV1-9],28,32,33,34,35  
RXO-14,15  
RXE-13,14  
RXD-10  
DSP-3  
PRA-8,11,12  
GT1-3,4,5,6,7,16,17,18  
IN1-3,4,5,6,7,16,18,19,30  
IN2-3,7,9,12,13,22,23,39,40,41,42,43,49,50,52,53  
IN3-3,8,14,15,16,18,19,25  
ACC-7,8,9  
ABS-1,5,8  
OBX-5[except CE,CNE,CWE and CF datatypes]  
PES-1,2,3,4  
PEO-7,13,14,15,16,17,19,20,21  
FAC-3,4,5,7,8  
OM1-17,28,29  
OM7-20  
LOC-2,4,5,6  
LRL - nothing  
LDP-2,11  
LCC-1  
CM0-5,9,10  
TXA-5,9,10,11,23,22  
ARQ-15  
SCH-12,13,14,15,16,17,18,19,20,21,22  
AIL-3  
PRD everything, but you can specify individual fields that are to be preserved  
CTD-2,3,4,5  
ROL-10,11,12  
VAR-6  
AFF-2,3  
EDU-6,8  
STF-3,5,6,8,10,11,15,17,18,22,27,28

## Synopsis

When run as  
$ python DeIdentifyHL7message.py [-I inputDir|--inputDir=inputDir] [-O outputDir|--outputDir=outputDir] [-D dataDir|--dataDir=dataDir] [-T testData|--testData=testData] [-v level|--verbose=level] [-L logDir|--logDir=logDir] [-l logFile|--logFile=logFile]

PARAMETERS  
-I inputDir|--inputDir=inputDir  
The folder where the messages to be deidentified will be found (default='./input')

-O outputDir|--outputDir=outputDir  
The folder where the deidentified message will be saved (default='./output')

-D dataDir|--dataDir=dataDir  
The folder where the data files and population health files will be found (default='./data')

-T testData|--testData=testData  
The Excel Workbook of demographic data to be used for person deidentification (default='./data/testHealthPopulation.xlsx')

-p PIDfieldsToPreserve|--preservePID=PIDfieldsToPreserve  
A comma separated list of PID fields not to be de-identified

-d PRD|--preservePRD=PRDfieldsToPreserve  
A comma separated list of PRD fields not to be de-identified

-v level|--vervose=level  
The debug level of detail in the debug log file

-L logDir|--logDir=logDir  
The folder where the log file will be created (default='logs')

-l logFile|--logFile=logFile  
The name of the file of log messages. If not specified, log message will be sent to the screen
