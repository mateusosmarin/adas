# ADAS

Advanced Driver-Assistance System with XWR18XX mmWave radar (_Texas Instruments_).

# About

Python library providing an interface to XWR18XX mmWave radar demo software. It's based on mmWave SDK 3.4.

The communication is performed over the serial CLI and DATA ports (usually /dev/ttyACM0 and /dev/ttyACM1 on linux and COM9 and COM11 on windows).

It provides implementations of parsers for the configuration files and the TLV messages which the board transmits.

The library is not finished yet, missing some advanced features like subframe configurations.

It is meant to be used for further processing algorithms to build an ADAS (Advanced Driver-Assistance System).

The sklearn toolkit is being used to perform clustering algorithms, and it is expected to implement the normalized LMS filter to track the clusters.

# How to use it

Connect the XWR18XX module and determine the serial ports to be used. The tools provided by the pyserial module can be used to list the available ports.

```
python -m serial.tools.list_ports
python -m serial.tools.miniterm
```

The miniterm tool can be used to communicate directly with the board.

To instantiate an XWR18XX you provide the configuration filename and serial ports to use. If the serial ports are not provided, /dev/ttyACM0 and /dev/ttyACM1 are assumed.

After the object is created, you have to load_config() to load the configuration file onto the board. For then on, you can receive the packets through the read() or read_raw() methods.

The packet is returned as a dictionary with keys given by the enum xwr18xx.tlv.MmwDemoOutputMessageType. Most of the messages are returned as np.ndarray. Check the samples for further instructions.
