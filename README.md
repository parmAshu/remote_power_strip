# Remote Power Strip Controller

This repository contains source code of the controller software for remote power strip device.

Currently the script works only on Linux Platform.

## Usage

python3 rps.py [arguments] [serialPort]


### List of Commands

`info`

Get information about the connected device.

`getAll`

Get state of all channels.

`getOne`

Get state of one channel. You will have to pass the channel number as another argument.

`setOne`

Set the state of one channel. You will have to pass the channel number and state as other aguments.

`addUser`

Associate a user with a channel. This command requires sudo permissions.

`removeUser`

Remove User from a channel. This command requires sudo permissions.

### Arguments

`--command [command]`

`-c [command]`

The command to execute, find the list of commands below (this argument is always required)

`--channel [channel number]`

`-ch [channel number]`

The channel to access, its a number in the range 0,N-1 (N being the number of channels)

`--state [state]`
`-s [state]`

The state to set

`--user [username]`

`-u [username] `

The linux username

## Examples

For all the following examples, assume that device is connected to port /dev/ttyUSB0

### Get the information

`rps --command info /dev/ttyUSB0`

OR

`rps -c info /dev/ttyUSB0`

### Get the state of all channels

`rps --command getAll /dev/ttyUSB0`

OR

`rps -c getAll /dev/ttyUSB0`

### Get the state of one channel

`rps --command getOne --channel 3 /dev/ttyUSB0`

OR

`rps -c getOne -ch 3 /dev/ttyUSB0`

### Set the state of one channel

`rps --command setOne --channel 3 /dev/ttyUSB0`

OR

`rps -c setOne -ch 3 /dev/ttyUSB0`

## Install instructions

1. Clone the repository in **/opt**. You will need sudo permissions for this.

`git clone https://github.com/parmAshu/remote_power_strip.git`

2. Initialize the submodule by navigating into the cloned repository and executing the following commands.

`git submodule init`

`git submodule update`

3. Add the alias to the script in .bashrc file(s)

`alias rps="/opt/remote_power_strip/rps.py"`

## Notes

1. This script currently works only on linux system.
2. This script stores configuration file in /etc/rps; sudo permissions are required when you want for operations/commands that require modifying configuration file.

