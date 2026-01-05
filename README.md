# De-identify-HL7-messages
Replace patient, provider, prescriber, practitioner, organisation and location data in HL7 messages

# Outline
Data is replaced , on a field by field basis, for each segment from two sources. Patients, providers, prescribers, practtitioners and organisatins are replaces with test patient/provider/practitioner/organisation data created by [mkHealth Population Australia](https://github.com/russellmcdonell/mkHealth_Population-Australia). This includes test identifiers, test addresses and test telephone numbers/mobile numbers/email addressees. By default, this data is in an Excel Workbook called 'testHealthPopulation.xlsx' in the data folder.

The second source is a number of paragraths of sentences constructed of random latin works - [Lorum Ipsum](https://www.lipsum.com/). The words are used where identifying codes need to be replaced. Shorter sentences are used where identifying code descriptions need to be repleaced. The whole text has also been convereted into a PDF document plus PNG/TIF/GIF/JPEG images for where Base64 encoded data of these types needs to be replaced. These files can be found, and must exist, in the data folder.

# Usage
Most of this code in DeidentifyHL7messages.py is functionality that is intended to be cut and pasted into other Python scrips. For instance you may have a script to extract HL7 messages from log files and you want to offer the option of de-identifying them on the fly.

There is an \_\_main\_\_ section which means that this can also be run as a standalone script. By default, it will read all the HL7 messages in the input folder and create de-identifyied version in the output folder.

# WARNING - DO NOT TRUST THIS CODE
It is impossible to create a full set of production HL7 messages which cover erery possible usage of every HL7 segment. Hence much of this code is untested; much of this code may not fit with the way you are using HL7. Certainly, Z-segments and site specific extensions to standard segments/fields etc are not covered. Fortunately the code is relatively easy to read, so it is easy to see which fields, in which segments are being processes and how they are being processed.
