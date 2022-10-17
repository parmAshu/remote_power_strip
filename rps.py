#!/usr/bin/python3
import os, sys, platform, json, getpass, serial, time

# Modify this for proper functionality 
import py_simple_serial.simpleSerial as ss

# Detect the operating system and abort if not Linux 
if platform.system() != "Linux": 
    print( "RPS works only on linux!" ) 
    exit() 
  
INITIAL_CONFIGURATION = "{ }" 
CONFIGURATION_FILE_DIR="/etc/rps"
CONFIGURATION_FILE_PATH= CONFIGURATION_FILE_DIR + "/rps.conf" 
CONFIGURATION_DATA=None
  
VALID_OPTIONS = [ "" ] 
CMD_ARGUMENT = { "other" : [] } 
VALID_COMMANDS = [ "info", "getOne", "getAll", "setOne", "addUser", "removeUser", "removeAllUsers" ]
DEVICE_BAUDRATE = 115200

DEVICE_PORT = ""

EXECUTION_MODE = None

DEVICE = {
    "verion" : "",
    "num_channels" : 0,
    "channel_state" : []
}

RESPONSE_WAIT_DELAY = 0.5

def create_conf_file(): 
    try:
        if not os.path.exists( CONFIGURATION_FILE_DIR ):
            os.mkdir( CONFIGURATION_FILE_DIR )
        with open( CONFIGURATION_FILE_PATH, "w" ) as fl: 
            fl.write(INITIAL_CONFIGURATION) 
        return True 
    except PermissionError:
        msg = """Could not create configuration file!""" 
        print( msg ) 
        return False
    
def validate_cmd_arguments():

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
    if CMD_ARGUMENT[ command_option ][0] not in VALID_COMMANDS:
        print( "Invalid command!" )
        return False 

    return True

def device_ack( resp ):
    if (resp["title"] & 128) > 0:
        return False
    else:
        return True

def device_send_recv( dev, msg ):
    dev.send_message( msg )
    time.sleep( RESPONSE_WAIT_DELAY )
    resp = dev.recv()
    return resp

def info_command( dev ):
    msg = {
        "version" : 1,
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
    msg = {
        "version" : 1,
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
    
    if channel >= DEVICE['num_channels']:
        return None

    msg = {
        "version" : 1,
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
    msg = {
        "version" : 1,
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

def execute_command( dev, command, *args, **kwargs ):
    global CONFIGURATION_DATA

    DEVICE_PORT = CMD_ARGUMENT["other"][0]
    if command == "info":
        resp = info_command( dev )
        if resp:
            DEVICE["version"] = str(resp["message"][0]) + "." + str(resp["message"][1]) + "." + str(resp["message"][2]) 
            DEVICE["num_channels"] = resp["message"][3]
            DEVICE["channel_state"] = []
            for state in resp["message"][4:]:
                DEVICE["channel_state"].append(state)
            print( "Version : ", DEVICE["version"] )
            print( "Number of channels : ", DEVICE["num_channels"] )
            print( """Channel   State   User""" )
            i=0
            for ch in DEVICE["channel_state"]:
                print( i, '\t', ch, '\t', CONFIGURATION_DATA[ DEVICE_PORT ]["channel_permissions"][i][0] )
                i+=1
    elif command == "getOne":
        resp = get_one_command( dev )
        if resp:
            print( "State : ", resp["message"][1] )
    elif command == "getAll":
        resp = get_all_command( dev )
        if resp:
            print( """Channel   State""" )
            for i in range( CONFIGURATION_DATA[ DEVICE_PORT ][ "num_channels" ] ):
                print( i, '\t', resp["message"][i+1] )
    elif command == "setOne":
        resp = set_one_command( dev )
        if resp:
            print( "Done!" )
    elif command == "addUser":
        if "channel" in CMD_ARGUMENT:
            DEVICE_CHANNEL = CMD_ARGUMENT[ "channel" ]
        elif "ch" in CMD_ARGUMENT:
            DEVICE_CHANNEL = CMD_ARGUMENT[ "ch" ]
        else:
            DEVICE_CHANNEL=""
            print( "Channel not provided." )

        if "user" in CMD_ARGUMENT:
            CHANNEL_USER = CMD_ARGUMENT[ "user" ]
        elif "u" in CMD_ARGUMENT:
            CHANNEL_USER = CMD_ARGUMENT[ "u" ]
        else:
            CHANNEL_USER=""
            print( "User not provided." )

        if len( CHANNEL_USER )>0 and len( DEVICE_PORT ) > 0:
            CONFIGURATION_DATA[ DEVICE_PORT ][ "channel_permissions" ][ DEVICE_CHANNEL ][0]=CHANNEL_USER

            with open( CONFIGURATION_FILE_PATH, 'w' ) as fl:
                fl.write( json.dumps( CONFIGURATION_DATA ) )
    elif command == "removeUser" :
        DEVICE_PORT = CMD_ARGUMENT["other"][0]
        if "channel" in CMD_ARGUMENT:
            DEVICE_CHANNEL = CMD_ARGUMENT[ "channel" ]
        elif "ch" in CMD_ARGUMENT:
            DEVICE_CHANNEL = CMD_ARGUMENT[ "ch" ]
        else:
            DEVICE_CHANNEL=""
            print( "Channel not provided." )

        if len( CHANNEL_USER )>0 and len( DEVICE_PORT ) > 0:
            CONFIGURATION_DATA[ DEVICE_PORT ][ "channel_permissions" ][ DEVICE_CHANNEL ]=[]
            
            with open( CONFIGURATION_FILE_PATH, 'w' ) as fl:
                fl.write( json.dumps( CONFIGURATION_DATA ) )
    elif command == "removeAllUsers" :
        CONFIGURATION_DATA[ DEVICE_PORT ][ "channel_permissions" ]=[[]]*CONFIGURATION_DATA[ DEVICE_PORT ][ "num_channels" ]

        with open( CONFIGURATION_FILE_PATH, 'w' ) as fl:
                fl.write( json.dumps( CONFIGURATION_DATA ) )
    else:
        print( "No valid command!" )

# --------------------------------------------------------------------------------------------------------------------------------------------------------
# Main logic starts from here
# --------------------------------------------------------------------------------------------------------------------------------------------------------
if __name__ == "__main__":


    # Open the configuration file; create one if not already present. 
    try: 
        with open( CONFIGURATION_FILE_PATH ) as fl: 
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

    
    # Open the serial port and connect to the device
    dev = ss.simpleSerialDevice( port = CMD_ARGUMENT[ 'other' ][0], baudrate = DEVICE_BAUDRATE )
    try:
        dev.connect()
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

        DEVICE_PORT = CMD_ARGUMENT["other"][0]
        if DEVICE_PORT not in CONFIGURATION_DATA:
            CONFIGURATION_DATA[ DEVICE_PORT ] = {
                "num_channels" : DEVICE[ "num_channels" ],
                "channel_permissions" : [[]]*DEVICE[ "num_channels" ]
            }
            with open( CONFIGURATION_FILE_PATH, "w" ) as fl:
                fl.write( json.dumps( CONFIGURATION_DATA ) )

        if len( CONFIGURATION_DATA[ DEVICE_PORT ]["channel_permissions"] ) < CONFIGURATION_DATA[ DEVICE_PORT ][ "num_channels"] :
            print( "Some channels are not configured, associate users with each channel!" )

        if "command" in CMD_ARGUMENT:
            command = CMD_ARGUMENT["command"]
        elif "c" in CMD_ARGUMENT:
            command = CMD_ARGUMENT["c"]
        else:
            command = ""


    except PermissionError:
        print( "Permission Denied, try with elevated permission!" )
    except:
        print( "Something went wrong :(" )
    finally:
        dev.disconnect()