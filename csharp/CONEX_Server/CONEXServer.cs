// CONEXServer.cs
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

using Newport.CONEXCC;

class ConexServer
{

    static void ServerLoop()
    {
        // First check to see if there are any motors present.
        // Then wait for a TCP connection.
        // Execute any commands that come in.
        // Repeat.

        
        int retcode;
        Socket listener = null;
        Socket handler = null;

        while (true)
        {
            try
            {
                CommandInterfaceConexCC.ConexCC CC = new CommandInterfaceConexCC.ConexCC();
                
             
                

                // wait for TCP connection

                // Establish the local endpoint for the socket.
                // Dns.GetHostName returns the name of the 
                // host running the application.
                //IPHostEntry ipHostInfo = //Dns.GetHostName()); //or "localhost"? //Dns.Resolve("locahost");
                IPAddress ipAddress = IPAddress.Any; //ipHostInfo.AddressList[0]; 
                IPEndPoint localEndPoint = new IPEndPoint(ipAddress, 11009);

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
                    Console.WriteLine(data);

                    // execute the received command to picomotors
                    string[] commandStrings = data.Split(new Char[] { ',' });
                    
                    //Use commandStrings[0] to decide which function to run with what arguments...
                    
                    switch (commandStrings[0])
                    {
                        case "Init":
                            if (commandStrings.Length == 2)
                            {
                                /*Argument list (element 0 is 'Init'):
                                    instrumentKey String
                                */
                                retcode = init(commandStrings, CC);
                                if (retcode == -1)
                                {
                                    Console.WriteLine("Return code from init: -1");
                                    String message = "Failed to Initialize CONEX Server";
                                    handler.Send(Encoding.ASCII.GetBytes("MESG"));
                                    Byte[] len = BitConverter.GetBytes(message.Length);
                                    Array.Reverse(len);
                                    Console.Write("Array length: ");
                                    Console.WriteLine(len.Length);
                                    handler.Send(len);
                                    handler.Send(Encoding.ASCII.GetBytes(message));
                                }
                                else
                                {
                                    Console.WriteLine("Return code from init: 0");
                                    String message = "Success";
                                    Byte[] len = BitConverter.GetBytes(message.Length);
                                    Array.Reverse(len);
                                    handler.Send(Encoding.ASCII.GetBytes("MESG"));
                                    handler.Send(len);
                                    handler.Send(Encoding.ASCII.GetBytes(message));
                                }
                            }
                            else
                            {
                                //invalid argument list length
                                Console.WriteLine("Incorrect number of arguments for init.");
                            }
                            break;
                            
                        case "SetPosition":
                            if (commandStrings.Length == 2)
                            {
                                /*Argument list (element 0 is 'Init'):
                                    instrumentKey String
                                */
                                retcode = SetPosition(commandStrings, CC);
                            }
                            else
                            {
                                //invalid argument list length
                                Console.WriteLine("Incorrect number of arguments for SetPosition.");
                            }
                            break;

                        case "SetVelocity":
                            if (commandStrings.Length == 2)
                            {
                                /*Argument list (element 0 is 'Init'):
                                    instrumentKey String
                                */
                                retcode = SetVelocity(commandStrings, CC);
                            }
                            else
                            {
                                //invalid argument list length
                                Console.WriteLine("Incorrect number of arguments for SetVelocity.");
                            }
                            break;

                        case "SetPositionVelocity":
                            if (commandStrings.Length == 3)
                            {
                                /*Argument list (element 0 is 'Init'):
                                    instrumentKey String
                                */
                                String[] posst = new String[] {commandStrings[0],commandStrings[1]};
                                retcode = SetPosition(posst, CC);
                                String[] velst = new String[] { commandStrings[0], commandStrings[2] };
                                retcode = SetVelocity(velst, CC);
                            }
                            else
                            {
                                //invalid argument list length
                                Console.WriteLine("Incorrect number of arguments for SetPositionVelocity.");
                            }
                            break;


                        case "GetPosition":
                            double pos = GetPosition(commandStrings, CC);
                            sendmessage(pos.ToString(),handler);
                            break;
                        
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
                    listener = null;
                }
            }


        }
    }
    
    public static void sendmessage (String message, Socket handler)
    {
        Byte[] len = BitConverter.GetBytes(message.Length);
        Array.Reverse(len);
        handler.Send(Encoding.ASCII.GetBytes("MESG"));
        handler.Send(len);
        handler.Send(Encoding.ASCII.GetBytes(message));
    }

    public static int Main(String[] args)
    {
        ServerLoop();
        return 0;
    }
    
    static int init(String[] commandStrings, CommandInterfaceConexCC.ConexCC myController)
    {
        Console.WriteLine("Connecting to controller...\r\n");
        return myController.OpenInstrument(commandStrings[1]);  
    }

    static int SetPosition(String[] commandStrings, CommandInterfaceConexCC.ConexCC myController)
    {
        string errs = "";
        double position = Convert.ToDouble(commandStrings[1]);
        int address = 1;
        int err = myController.PA_Set(address, position, out errs);
        return err;
    }

    static double GetPosition(String[] commandStrings, CommandInterfaceConexCC.ConexCC myController)
    {
        string errs = "";
        double position = 0;
        int address = 1;
        int err = myController.PA_Get(address, out position, out errs);
        return position;
    }

    static int SetVelocity(String[] commandStrings, CommandInterfaceConexCC.ConexCC myController)
    {
        string errs = "";
        double velocity = Convert.ToDouble(commandStrings[1]);
        int address = 1;
        int err = myController.VA_Set(address, velocity, out errs);
        return err;
    }
    
}

