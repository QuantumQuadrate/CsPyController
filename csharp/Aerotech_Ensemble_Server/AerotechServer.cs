// AerotechServer.cs
// Part of the AQuA control software by Martin Lichtman.

// This is a simple server to allow control of Aerotech Ensemble translation stages via TCP.
// Written in C# because the Aerotech drivers are .NET assemblies.
// Based on Picomotor_server.cs by Martin Lichtman.

// author = Donald Booth
// created = 2015.06.22
// modified >= 2015.06.22

using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Net;
using System.Net.Sockets;

using Aerotech.Ensemble;
using Aerotech.Ensemble.Communication;
using Aerotech.Ensemble.Status;
using Aerotech.Ensemble.Exceptions;
using Aerotech.Ensemble.Parameters;
using Aerotech.Common;
using Aerotech.Ensemble.Information;
using Aerotech.Ensemble.Commands;

class AerotechServer
{


    static void ServerLoop()
    {
        // First check to see if there are any motors present.
        // Then wait for a TCP connection.
        // Execute any commands that come in.
        // Repeat.


        Socket listener = null;
        Socket handler = null;

        while (true)
        {
            try
            {

                Console.WriteLine("Connecting to controller...\r\n");
                Controller myController = Controller.Connect()[0];

                if (!(handler == null))
                {
                    handler.Shutdown(SocketShutdown.Both);
                    handler.Close();
                    handler = null;
                }
                if (!(listener == null))
                {
                    listener.Shutdown(SocketShutdown.Both);
                    listener.Close();
                    listener = null;
                }

                // wait for TCP connection

                // Establish the local endpoint for the socket.
                // Dns.GetHostName returns the name of the 
                // host running the application.
                //IPHostEntry ipHostInfo = //Dns.GetHostName()); //or "localhost"? //Dns.Resolve("locahost");
                IPAddress ipAddress = IPAddress.Any; //ipHostInfo.AddressList[0]; 
                IPEndPoint localEndPoint = new IPEndPoint(ipAddress, 11002);

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
                    
                    //Use commandStrings[0] to decide which function to run with what arguments...
                    
                    if (commandStrings[0] == "UpdateGlobals")
                    {
                            
                            if (commandStrings.Length == 10)
                            {
                                /*Argument list (element 0 is 'UpdateGlobals'):
                                    Xi           1    Double
                                    Xend         2    Double
                                    Xvmx         3    Double
                                    Xamx         4    Double
                                    Zi           5    Double
                                    Zend         6    Double
                                    Zvmx         7    Double
                                    Zamx         8    Double
                                    XrelTrig     9    Int
                                */
                                updateGlobals(commandStrings, myController);
                            }
                            else
                            {
                                //invalid argument list length
                                Console.WriteLine("Incorrect number of arguments for UpdateGlobals.");
                            }
                    }
                    else if (commandStrings[0] == "WaitForGlobals")        
                    {
                            waitForGlobals(myController);
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
                try
                {
                    handler.Shutdown(SocketShutdown.Both);
                    handler.Close();
                    handler = null;
                }
                catch (Exception e)
                {
                    handler = null;
                }
            }
            if (!(listener == null))
            {
                try
                {
                    listener.Shutdown(SocketShutdown.Both);
                    listener.Close();
                    listener = null;
                }
                catch (Exception e)
                {
                    handler = null;
                }
            }


        }
    }

    public static int Main(String[] args)
    {
        ServerLoop();
        return 0;
    }
    
    static void updateGlobals(String[] commandStrings, Controller myController)
    {
        for (int i = 0; i < 8; i++)
        {   //Update DGlobal parameters
            myController.Commands.Register.WriteDoubleGlobal(i, Convert.ToDouble(commandStrings[i+1]));
        }
        
        //Update IGlobal parameter(s)
        myController.Commands.Register.WriteIntegerGlobal(0, Convert.ToInt32(commandStrings[9]));
        
        //Set UserInteger0 to 1...
        ControllerParameters controllerParameters = myController.Parameters;
        controllerParameters.System.User.UserInteger0.Value = 1;

        //pause 1000 ms to sync
        //System.Threading.Thread.Sleep(1000);
        
    }
    
    static void waitForGlobals(Controller myController)
    {
        //Set UserInteger0 to -1...
        ControllerParameters controllerParameters = myController.Parameters;
        controllerParameters.System.User.UserInteger0.Value = -1;
        
    }
    
}

