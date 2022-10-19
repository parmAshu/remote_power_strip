#!/usr/bin/python3
import os, sys, platform, json, getpass, serial, time, traceback

# Modify this for proper functionality 
import py_simple_serial.simpleSerial as ss

# Detect the operating system and abort if not Linux 
if platform.system() != "Linux": 
    print( "RPS works only on linux!" ) 
    exit() 

# -------------------------------------------------------------------------------------------------------





# CONSTANTS ---------------------------------------------------------------------------------------------

# This is a list of all valid commands
VALID_COMMANDS_CONST = [ "info", "getOne", "getAll", "setOne", "addUser", "removeUser", "removeAllUsers" ]

# This is the device baudrate
DEVICE_BAUDRATE_CONST = 115200

INITIAL_CONFIGURATION_CONST = "{ }" 
CONFIGURATION_FILE_DIR_CONST="/etc/rps"
CONFIGURATION_FILE_PATH_CONST= CONFIGURATION_FILE_DIR_CONST + "/rps.conf"
#CONFIGURATION_FILE_DIR_CONST="./" 
#CONFIGURATION_FILE_PATH_CONST = "rps.conf"

# The time period within which a valid response must be received
RESPONSE_WAIT_DELAY_CONST = 0.5

# -------------------------------------------------------------------------------------------------------





# GLOBAL VARIABLES --------------------------------------------------------------------------------------

# Variable to store the configuration data read from configuration file.
CONFIGURATION_DATA=None

# This variable will hold all the command line arguments passed to the script
CMD_ARGUMENT = { "other" : [] } 

# This variable will hold the device port
DEVICE_PORT = ""

# This structure will hold data received from Device 
DEVICE = {
    "version" : "",
    "num_channels" : 0,
    "channel_state" : []
}

# -------------------------------------------------------------------------------------------------------





# UTILITY FUNCTIONS -------------------------------------------------------------------------------------

def create_conf_file():
    """This function creates the configuration file if not already present.

    Returns:
        Boolean : True if file got created, False otherwise
    """
    global CONFIGURATION_FILE_DIR_CONST, CONFIGURATION_FILE_PATH_CONST, INITIAL_CONFIGURATION_CONST

    try:
        if not os.path.exists( CONFIGURATION_FILE_DIR_CONST ):
            os.mkdir( CONFIGURATION_FILE_DIR_CONST )
        with open( CONFIGURATION_FILE_PATH_CONST, "w" ) as fl: 
            fl.write(INITIAL_CONFIGURATION_CONST) 
        return True 
    except PermissionError:
        msg = """Could not create configuration file!""" 
        print( msg ) 
        return False
    
def validate_cmd_arguments():
    """This function validates the command-line arguments passed to the script.
    This function scans the global variable CMD_ARGUMENT for command-line arguments.

    Returns:
        Boolean : True when all arguments are valid, False otherwise
    """
    global CMD_ARGUMENT 

    # There should only be one non-option argument i.e. the serial port name
    if len( CMD_ARGUMENT['other'] ) < 1:
        print( "Too few arguments, provide the serial port!" )
        return False
    if len( CMD_ARGUMENT['other'] ) > 2:
        print( "Too many arguments, provide only the serial port!" )
        return False

    # Make sure that there is only one value associated with any option except for ch/channel
    flag = False
    for k in CMD_ARGUMENT.keys():
        if k != "other" and k!="ch" and k!="channel" and len( CMD_ARGUMENT[k] ) !=1:
            flag = True
            break
    if flag==True:
        print( "Invalid options!" )
        return False

    # Make sure that the command option is available
    command_option = ""
    if "command" in CMD_ARGUMENT:
        command_option = "command"
    elif "c" in CMD_ARGUMENT:
        command_option = "c"
    if command_option == "":
        print( "Command option is required!" )
        return False

    # Make sure that the command provided is a valid command
    if CMD_ARGUMENT[ command_option ][0] not in VALID_COMMANDS_CONST:
        print( "Invalid command!" )
        return False 

    return True

def device_ack( resp ):
    """Function to check if device responded with ACK or NACK.

    Args:
        resp (dict): The received simple serial response object.

    Returns:
        boolean : True for ACK, False for NACK
    """
    if (resp["title"] & 128) > 0:
        return False
    else:
        return True

def device_send_recv( dev, msg ):
    """This function is used to achieve one transaction with the device.

    Args:
        dev (py_simple_serial.simpleSerial.simpleSerialDevice): simpleSerialDevice object
        msg (dict): The message to be sent 

    Returns:
        None/dict: When a valid response is received, it is stored in a dictionary and returned
    """
    dev.flush()
    dev.send_message( msg )
    time.sleep( RESPONSE_WAIT_DELAY_CONST )
    resp = dev.recv()
    return resp

def info_command( dev ):
    """This function is used to invoke the info command.

    Args:
        dev (py_simple_serial.simpleSerial.simpleSerialDevice): simple serial object for the device

    Returns:
        None/dict : If there is a valid response from the device, that response is returned.
    """
    msg = {
        "version" : "1",
        "title" : 1,
        "message" : b''
    }
    resp = device_send_recv( dev, msg )

    if resp:
        if device_ack(resp):
            return resp
        else:
            return None
    else:
        return None

def get_all_command( dev ):
    """This function is used to invoke the status all command.

    Args:
        dev (py_simple_serial.simpleSerial.simpleSerialDevice): simple serial object for the device

    Returns:
        None/dict : If there is a valid response from the device, that response is returned.
    """

    msg = {
        "version" : "1",
        "title" : 2,
        "message" : b''
    }
    resp = device_send_recv( dev, msg )

    if resp:
        if device_ack( resp ):
            return resp
        else:
            return None
    else:
        return None

def get_one_command( dev, channel ):
    """This function is used to invoke the status one command.

    Args:
        dev (py_simple_serial.simpleSerial.simpleSerialDevice): simple serial object for the device
        channel (Number) : Channel number, the status of which is required

    Returns:
        None/dict : If there is a valid response from the device, that response is returned.
    """
    channel = int(channel)    
    if channel >= DEVICE['num_channels']:
        return None

    msg = {
        "version" : "1",
        "title" : 3,
        "message" : channel.to_bytes( 1, 'little' )
    }
    resp = device_send_recv( dev, msg )

    if resp:
        if device_ack( resp ):
            return resp
        else:
            return None
    else:
        return None

def set_one_command( dev, channel, state ):
    """This function is used to invoke the set one command.

    Args:
        dev (py_simple_serial.simpleSerial.simpleSerialDevice): simple serial object for the device
        channel (Number) : The channel number that is to be controlled.
        state (Number) : The channel state 0/1.

    Returns:
        None/dict : If there is a valid response from the device, that response is returned.
    """
    global CONFIGURATION_DATA

    channel = int(channel)
    state = int(state)

    if len(CONFIGURATION_DATA[ DEVICE_PORT ][ "channel_permissions" ][ channel ])==0 or \
        os.getlogin() != CONFIGURATION_DATA[ DEVICE_PORT ][ "channel_permissions" ][ channel ][0]:
        
        print( "Permission Denied : Invalid User")
        return None

    msg = {
        "version" : "1",
        "title" : 4,
        "message" : channel.to_bytes( 1, 'little' ) + state.to_bytes( 1, 'little' )
    }
    resp = device_send_recv( dev, msg )

    if resp:
        if device_ack( resp ):
            return resp
        else:
            return None
    else:
        return None

def execute_command( dev, *args, **kwargs ):
    global CONFIGURATION_DATA, DEVICE, DEVICE_PORT, CMD_ARGUMENT

    #print( CMD_ARGUMENT )
    # Get the command
    if "command" in CMD_ARGUMENT:
        command = CMD_ARGUMENT["command"][0]
    elif "c" in CMD_ARGUMENT:
        command = CMD_ARGUMENT["c"][0]
    else:
        command = ""

    if command == "info":
        response = info_command( dev )
        #print( response )
        if response:
            DEVICE["version"] = str(response["message"][0]) + "." + str(response["message"][1]) + "." + str(response["message"][2]) 
            DEVICE["num_channels"] = response["message"][3]
            DEVICE["channel_state"] = []
            for state in response["message"][4:]:
                DEVICE["channel_state"].append(state)
            #print( DEVICE )
            print( "Version : ", DEVICE["version"] )
            print( "Number of channels : ", DEVICE["num_channels"] )
            print( """Channel   State   User""" )

            for i in range( DEVICE["num_channels"] ) :
                if len(CONFIGURATION_DATA[ DEVICE_PORT ]["channel_permissions"][i]) == 0 :
                    permission = "None"
                else:
                    permission = CONFIGURATION_DATA[ DEVICE_PORT ]["channel_permissions"][i][0]

                print( i, '\t', DEVICE["channel_state"][i], '\t', permission )

    elif command == "getOne":
        if "channel" in CMD_ARGUMENT:
            DEVICE_CHANNEL = CMD_ARGUMENT[ "channel" ][0]
        elif "ch" in CMD_ARGUMENT:
            DEVICE_CHANNEL = CMD_ARGUMENT[ "ch" ][0]
        else:
            DEVICE_CHANNEL=""
            print( "Channel not provided." )
        
        if len(DEVICE_CHANNEL) > 0:    
            response = get_one_command( dev, DEVICE_CHANNEL )
            if response:
                print( "State : ", response["message"][1] )
    
    elif command == "getAll":
        response = get_all_command( dev )
        if response:
            print( """Channel   State""" )
            for i in range( CONFIGURATION_DATA[ DEVICE_PORT ][ "num_channels" ] ):
                print( i, '\t', response["message"][i+1] )
    
    elif command == "setOne":
        if "channel" in CMD_ARGUMENT:
            DEVICE_CHANNEL = CMD_ARGUMENT[ "channel" ][0]
        elif "ch" in CMD_ARGUMENT:
            DEVICE_CHANNEL = CMD_ARGUMENT[ "ch" ][0]
        else:
            DEVICE_CHANNEL=""
            print( "Channel not provided." )

        if "state" in CMD_ARGUMENT:
            CHANNEL_STATE = CMD_ARGUMENT["state"][0]
        elif "s" in CMD_ARGUMENT:
            CHANNEL_STATE = CMD_ARGUMENT["s"][0]
        else:
            CHANNEL_STATE=""
            print( "State not provided." )

        if len(DEVICE_CHANNEL) > 0 and len(CHANNEL_STATE) > 0:
            response = set_one_command( dev, DEVICE_CHANNEL, CHANNEL_STATE )
            if response:
                print( "Done!" )
    
    elif command == "addUser":
        if "channel" in CMD_ARGUMENT:
            DEVICE_CHANNEL = CMD_ARGUMENT[ "channel" ][0]
        elif "ch" in CMD_ARGUMENT:
            DEVICE_CHANNEL = CMD_ARGUMENT[ "ch" ][0]
        else:
            DEVICE_CHANNEL=""
            print( "Channel not provided." )

        if "user" in CMD_ARGUMENT:
            CHANNEL_USER = CMD_ARGUMENT[ "user" ][0]
        elif "u" in CMD_ARGUMENT:
            CHANNEL_USER = CMD_ARGUMENT[ "u" ][0]
        else:
            CHANNEL_USER=""
            print( "User not provided." )

        if len( CHANNEL_USER )>0 and len( DEVICE_CHANNEL )>0:
            DEVICE_CHANNEL = int( DEVICE_CHANNEL )
            CONFIGURATION_DATA[ DEVICE_PORT ][ "channel_permissions" ][ DEVICE_CHANNEL ]=[CHANNEL_USER]

            with open( CONFIGURATION_FILE_PATH_CONST, 'w' ) as fl:
                fl.write( json.dumps( CONFIGURATION_DATA ) )
            
            print( "Done!" )
    
    elif command == "removeUser" :

        if "channel" in CMD_ARGUMENT:
            DEVICE_CHANNEL = CMD_ARGUMENT[ "channel" ][0]
        elif "ch" in CMD_ARGUMENT:
            DEVICE_CHANNEL = CMD_ARGUMENT[ "ch" ][0]
        else:
            DEVICE_CHANNEL=""
            print( "Channel not provided." )

        if len( DEVICE_CHANNEL ) > 0:
            DEVICE_CHANNEL = int( DEVICE_CHANNEL )

            CONFIGURATION_DATA[ DEVICE_PORT ][ "channel_permissions" ][ DEVICE_CHANNEL ]=[]
            
            with open( CONFIGURATION_FILE_PATH_CONST, 'w' ) as fl:
                fl.write( json.dumps( CONFIGURATION_DATA ) )

            print( "Done!" )
    
    elif command == "removeAllUsers" :
        CONFIGURATION_DATA[ DEVICE_PORT ][ "channel_permissions" ]=[[]]*CONFIGURATION_DATA[ DEVICE_PORT ][ "num_channels" ]

        with open( CONFIGURATION_FILE_PATH_CONST, 'w' ) as fl:
            fl.write( json.dumps( CONFIGURATION_DATA ) )

        print( "Done!" )
    
    else:
        print( "Not a valid command!" )

# -------------------------------------------------------------------------------------------------------





# -------------------------------------------------------------------------------------------------------
# Main logic starts from here
# -------------------------------------------------------------------------------------------------------
if __name__ == "__main__":


    # Open the configuration file; create one if not already present. 
    try: 
        with open( CONFIGURATION_FILE_PATH_CONST ) as fl: 
            CONFIGURATION_DATA = json.loads( fl.read() ) 
    except json.decoder.JSONDecodeError: 
        msg = """ 
        Invalid configuration file or corrupted. 
        Creating a fresh one, all the existing configurations will be lost! 
        """ 
        print( msg ) 
        if create_conf_file() == False: 
            exit() 
    except PermissionError:
        msg = """
        Permission Error, try with elevated permission
        """
        print( msg )
        exit()
    except:
        msg = """
        Configuration file does not exist.
        Creating a fresh one!
        """ 
        print( msg ) 
        if create_conf_file() == False: 
            exit() 
    

    # Parse the command line arguments 
    parser_state = 0 
    prev_arg = "" 
    arg_type = "" 
    for arg in sys.argv[1:]: 
        if arg.startswith( "--" ):
            arg = arg[2:]
            arg_type = "option"
        elif arg.startswith( "-" ): 
            arg = arg[1:] 
            arg_type = "option" 
        else: 
            arg_type = "value" 
        
        if parser_state == 0: 
            if arg_type == "option": 
                if ( arg not in CMD_ARGUMENT ) == True: 
                    CMD_ARGUMENT[ arg ]=[] 
                parser_state = 1 
            else: 
                CMD_ARGUMENT[ "other" ].append( arg ) 
        elif parser_state == 1: 
            if ( arg_type == "option" and (arg not in CMD_ARGUMENT) ) == True: 
                CMD_ARGUMENT[ arg ]=[] 
            else: 
                CMD_ARGUMENT[ prev_arg ].append( arg ) 
                parser_state = 0 
        prev_arg = arg

    
    # Validate the command line arguments
    if validate_cmd_arguments() == False:
        exit()

    # Get the device port
    DEVICE_PORT = CMD_ARGUMENT["other"][0]
    
    # Open the serial port and connect to the device
    dev = ss.simpleSerialDevice( DEVICE_PORT, DEVICE_BAUDRATE_CONST )
    try:
        dev.connect()
        #time.sleep( 5 )
    except:
        print( "Connection failed!" )
        exit()


    try:
        # Validate the connected device using info command
        resp = info_command( dev )
        if not resp:
            raise Exception

        # Saving the device information locally
        DEVICE["version"] = str(resp["message"][0]) + "." + str(resp["message"][1]) + "." + str(resp["message"][2]) 
        DEVICE["num_channels"] = resp["message"][3]
        DEVICE["channel_state"] = []
        for state in resp["message"][4:]:
            DEVICE["channel_state"].append(state)

        # Check if some configuration for current device exists in the existing configuration data
        # If not, then create an entry for it in the configuration data file
        if DEVICE_PORT not in CONFIGURATION_DATA:
            #print( "Creating device record..." )
            CONFIGURATION_DATA[ DEVICE_PORT ] = {
                "num_channels" : DEVICE[ "num_channels" ],
                "channel_permissions" : [[]]*DEVICE[ "num_channels" ]
            }
            with open( CONFIGURATION_FILE_PATH_CONST, "w" ) as fl:
                fl.write( json.dumps( CONFIGURATION_DATA ) )

        # Now, check whether channels are associated with users or not
        for i in range( DEVICE["num_channels"] ):
            if len( CONFIGURATION_DATA[ DEVICE_PORT ]["channel_permissions"][i] ) == 0:
                print( "Warning : Channel ", i, " is not associated with any user! " )
        print()

        # Execute the command
        execute_command( dev )

    except PermissionError:
        print( "Permission Denied, try with elevated permission!" )
    except:
        #traceback.print_exc()
        print( "Something went wrong :(" )
    finally:
        dev.disconnect()