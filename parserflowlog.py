import csv
from collections import defaultdict
import logging

# Configure logging
logging.basicConfig(
    filename='flowLogParser.log',  # Log file name
    level=logging.INFO,                # Log level
    format='%(asctime)s - %(levelname)s - %(message)s'  # Log format
)

def loadLookupTable():
    '''
    loads a lookup table from CSV file
    reads csv file and iterates the row to form key (dstport, protocol) value (tag)
    input: csv file
    returns: lookuptable mapping (dstport, protocol) to tags.
    '''
    lookupTable = {}
    filename = 'lookuptable.cvs'
    try:
        with open(filename, mode='r', newline='', encoding='ascii') as file:
            reader = csv.DictReader(file)
            print(reader)
            try:
                for row in reader:
                    key = (row['dstport'], row['protocol'].lower()) # converted to lower case for case insensitive matching
                    tag =  row['tag']
                    lookupTable[key] = tag
            except KeyError as e:
                        logging.warning(f"""Missing expected column: {e}""")
        logging.info(f"Successfully loaded lookup table from '{filename}'.")
    except FileNotFoundError:
        logging.error(f"File '{filename}' not found.")
        raise
    except Exception as e:
        logging.error(f"Error loading lookup table: {e}")
        raise
    return lookupTable

def readFlowLogs(filename):
    '''
        loads flowlogfile and strip each line
    '''
    try:
        with open(filename, mode='r', newline='', encoding='ascii') as file:
            while True:
                line = file.readline()
                if not line:
                    break
                yield line.strip()
    except FileNotFoundError:
        logging.error(f"File '{filename}' not found.")
        raise
    except Exception as e:
        logging.error(f"Error loading flow log file: {e}")
        raise

def parseFlowLogs(readFlowLogfile, lookupTable):
    '''
    reads line by line and extracting destination port and protocol numbers and mapping with protocol names and counting their occurrences. 
    Each portProtocol pair maps with tag using lookup table and counts tag occurrences.
    For ICMP protocol is setting to zero destination port. 
    input: flowlog file
    returns: tuple containing two dictionaries. First one maps (dstport, protocol) tuples to (dstport, protocol) counts
    and second one maps tags to Tag counts
    '''
    tagCounts = defaultdict(int)
    portProtocolCounts = defaultdict(int)
    try:
        for line in readFlowLogfile:
            
            parts = line.split() # 
            if len(parts) < 11:
                continue  # Skip malformed lines
            
            # Extract relevant fields
            dstport = parts[6]
            protocolMapping = {
                '6': 'tcp', 
                '17': 'udp', 
                '1': 'icmp'
            }

            protocol = protocolMapping.get(parts[7])  # Default to 'icmp'
            if(protocol == 'icmp'):
                dstport = 0
            
            key = (dstport, protocol)

            print(key)

            # Update port/protocol counts
            portProtocolCounts[key] = portProtocolCounts.get(key, 0) + 1

            # not match any of the mappings would be considered "untagged."
            tag = lookupTable.get(key, 'Untagged')

            # Update tag counts
            tagCounts[tag] = tagCounts.get(tag, 0) + 1
    except ValueError as e:
        logging.error(f"ValueError: {e}, Line: {line.strip()}")
        raise
    return tagCounts, portProtocolCounts, 

def writeOutput(tagCounts, portProtocolCounts, outputFilename):
    '''
    writes output txt file for counts of tags and portProtocol pairs counts
    '''
    try:
        with open(outputFilename, mode='w', newline='', encoding='ascii') as outputfile:

            #Count of matches for  each tag
            #taged count
            outputfile.write("Tag Counts: \nTag, Count\n")
            for tag, count in tagCounts.items():
                outputfile.write(f"{tag},{count}\n")
            
            #Count of matches for each port/protocol combination 
            # Port/Protocal Counts
            outputfile.write("\n dstport Protocal combination Counts: \ndstport, Protocal, Count\n")
            for (dstport, protocol), count in portProtocolCounts.items():
                outputfile.write(f"{dstport},{protocol},{count}\n")
    
    except Exception as e:
        logging.error(f"""Write to file failed: {e}""")

def main():
    lookupTable = loadLookupTable()
    readFlowLogfile = readFlowLogs('flowlogs.txt')
    tagCounts, portProtocolCounts = parseFlowLogs(readFlowLogfile, lookupTable)
    writeOutput(tagCounts, portProtocolCounts, 'output.txt')

if __name__ == "__main__":
    main()