// Picomotor_server.cs
// Part of the AQuA control software by Martin Lichtman.

// This is a simple server to allow control of Newport Picomotors via TCP.
// Written in C# because the Picomotor drivers are .NET assemblies, which means either using
// .NET for python (which I was unable to install), or IronPython (which is slower and because of
// parameters passed as ref is not exactly the same syntax as python anyway, and so does not have an
// advantage), or in a .NET language such as C# (which was advantageous because of the examples available.)
// Based on RelativeMove.cs example from Newport, and on the Synchronous Socket Server Example 
// from Microsoft at http://msdn.microsoft.com/en-us/library/6y0e13d3(v=vs.110).aspx

// Note this project must be set to compile with .NET 4, not .NET 4.5, otherwise it will not find any devices.

// author = Martin Lichtman
// created = 2014.06.26
// modified >= 2014.07.09

using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Net;
using System.Net.Sockets;
using NewFocus.Picomotor;

class PicomotorServer
{


    static void ServerLoop()
    {
        // First check to see if there are any motors present.
        // Then wait for a TCP connection.
        // Execute any commands that come in.
        // Repeat.


        Socket listener = null;
        Socket handler = null;
        CmdLib8742 cmdLib = null;
        string[] strDeviceKeys = null;

        while (true)
        {
            try
            {

                Console.WriteLine("Waiting for device discovery...\r\n");
                cmdLib = new CmdLib8742(true, 5000, ref strDeviceKeys);
                if (strDeviceKeys == null)
                {
                    // If no devices were discovered
                    Console.WriteLine("No devices discovered.");
                    continue;
                }
                // For each device key in the list
                for (int i = 0; i < strDeviceKeys.Length; i++)
                {
                    string strDeviceKey = strDeviceKeys[i];
                    Console.WriteLine("Device Key[{0}] = {1}", i, strDeviceKey);
                    cmdLib.WriteLog("Device Key[{0}] = {1}", i, strDeviceKey);

                    // If the device was opened
                    if (cmdLib.Open(strDeviceKey))
                    {
                        string strID = string.Empty;
                        cmdLib.GetIdentification(strDeviceKey, ref strID);
                        Console.WriteLine("Device ID[{0}] = '{1}'\r\n", i, strID);
                        cmdLib.WriteLog("Device ID[{0}] = '{1}'", i, strID);
                    }
                }

                // wait for TCP connection

                // Establish the local endpoint for the socket.
                // Dns.GetHostName returns the name of the 
                // host running the application.
                //IPHostEntry ipHostInfo = //Dns.GetHostName()); //or "localhost"? //Dns.Resolve("locahost");
                IPAddress ipAddress = IPAddress.Any; //ipHostInfo.AddressList[0]; 
                IPEndPoint localEndPoint = new IPEndPoint(ipAddress, 11000);

                // Create a TCP/IP socket.
                listener = new Socket(AddressFamily.InterNetwork, SocketType.Stream, ProtocolType.Tcp);
                listener.Blocking = true;

                // Bind the socket to the local endpoint and 
                listener.Bind(localEndPoint);

                // listen for incoming connections.
                listener.Listen(10);

                // Start listening for connections.
                Console.WriteLine("Waiting for a connection...");

                // Program is suspended while waiting for an incoming connection.
                handler = listener.Accept();

                // set timeout to 10 seconds
                handler.Blocking = true;
                //handler.ReceiveTimeout = 10000;

                // Incoming data from the client.
                string data = null;
                byte[] bytes = null;
                int bytesRec = 0;

                // Loop looking for incoming messages
                while (true)
                {
                    // check for the message header to start with "MESG"

                    bytes = new Byte[4];
                    bytesRec = handler.Receive(bytes);
                    if (bytesRec != 4)
                    {
                        // The message header was bad.  Close socket and start over, requiring new connection
                        handler.Shutdown(SocketShutdown.Both);
                        handler.Close();
                        break;
                    }
                    data = Encoding.ASCII.GetString(bytes);
                    Console.WriteLine(data);
                    if (data != "MESG")
                    {
                        // The message header was bad.  Close socket and start over, requiring new connection
                        Console.WriteLine("Bad message header.  Should start with MESG.  Shutting down socket.");
                        handler.Shutdown(SocketShutdown.Both);
                        handler.Close();
                        break;
                    }

                    // read the next 4 bytes to get the message size

                    bytes = new Byte[4];
                    bytesRec = handler.Receive(bytes);
                    if (bytesRec != 4)
                    {
                        // The message header was bad.  Close socket and start over, requiring new connection
                        Console.WriteLine("Bad message header length, should be 4 byte uint.  Shutting down socket.");
                        handler.Shutdown(SocketShutdown.Both);
                        handler.Close();
                        break;
                    }
                    Array.Reverse(bytes); // Correct for endian-ness
                    UInt32 length = BitConverter.ToUInt32(bytes, 0);
                    Console.WriteLine(length.ToString());

                    // now read the number of bytes of the rest of the message                            
                    bytes = new Byte[length];
                    bytesRec = handler.Receive(bytes);
                    if (bytesRec != length)
                    {
                        // The message length was bad.  Close socket and start over, requiring new connection
                        Console.WriteLine("Bad message length.  Shutting down socket.");
                        Console.WriteLine(bytesRec.ToString());
                        //Console.WriteLine(Encoding.ASCII.GetString(bytes));
                        handler.Shutdown(SocketShutdown.Both);
                        handler.Close();
                        break;
                    }
                    // convert to ASCII
                    data = Encoding.ASCII.GetString(bytes);

                    // execute the received command to picomotors
                    string[] commandStrings = data.Split(new Char[] { ',' });

                    // Perform a relative move
                    string strDeviceKey = "8742 " + commandStrings[0];
                    int nMotor = Convert.ToInt16(commandStrings[1]);
                    int nSteps = Convert.ToInt16(commandStrings[2]);
                    bool bStatus = cmdLib.RelativeMove(strDeviceKey, nMotor, nSteps);

                    // check if command was okay
                    if (!bStatus)
                    {
                        Console.WriteLine("I/O Error:  Could not perform relative move.");
                        break;
                    }

                    bool bIsMotionDone = false;

                    // wait until motion finishes
                    while (bStatus && !bIsMotionDone)
                    {
                        // Check for any device error messages
                        string strErrMsg = string.Empty;
                        bStatus = cmdLib.GetErrorMsg(strDeviceKey, ref strErrMsg);
                        if (!bStatus)
                        {
                            Console.WriteLine("I/O Error:  Could not get error status.");
                            break;
                        }

                        string[] strTokens = strErrMsg.Split(new string[] { "," }, StringSplitOptions.RemoveEmptyEntries);

                        // If the error message number is not zero
                        if (strTokens[0] != "0")
                        {
                            Console.WriteLine("Device Error:  {0}", strErrMsg);
                            break;
                        }

                        // Get the motion done status
                        bStatus = cmdLib.GetMotionDone(strDeviceKey, nMotor, ref bIsMotionDone);

                        if (!bStatus)
                        {
                            Console.WriteLine("I/O Error:  Could not get motion done status.");
                        }
                        else
                        {
                            int nPosition = 0;
                            // Get the current position
                            bStatus = cmdLib.GetPosition(strDeviceKey, nMotor, ref nPosition);

                            if (!bStatus)
                            {
                                Console.WriteLine("I/O Error:  Could not get the current position.");
                            }
                            else
                            {
                                Console.WriteLine("Position = {0}", nPosition);
                            }
                        }
                        // continue to loop until motion is done
                    }
                    // loop and look for next command
                }

            }
            catch (Exception e)
            {
                Console.WriteLine(e.ToString());
            }

            //close socket and retry
            if (!(handler == null))
            {
                handler.Shutdown(SocketShutdown.Both);
                handler.Close();
                handler = null;
            }
            if (!(listener == null))
            {
                //listener.Shutdown(SocketShutdown.Both);
                listener.Close();
                listener = null;
            }

            if (!(cmdLib == null))
            {
                // Close the devices
                for (int i = 0; i < strDeviceKeys.Length; i++)
                {
                    string strDeviceKey = strDeviceKeys[i];
                    cmdLib.Close(strDeviceKey);
                }
                // Shut down device communication
                Console.WriteLine("Shutting down.");
                cmdLib.Shutdown();
                cmdLib = null;
            }

        }
    }

    public static int Main(String[] args)
    {
        ServerLoop();
        return 0;
    }
}

