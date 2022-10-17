# Remote Power Strip Controller

This repository contains source code of the controller software for remote power strip device.

Currently the script works only on Linux Platform.

## Usage

python3 rps.py [arguments] [serialPort]


### List of Commands

To be added..

### Arguments

`--command [command]`

`-c [command]`

The command to execute, find the list of commands below (this argument is always required)

`--channel [channel number]`

`-ch [channel number]`

The channel to access, its a number in the range 0,N-1 (N being the number of channels)

`--user [username]`

`-u [username] `

The linux username

