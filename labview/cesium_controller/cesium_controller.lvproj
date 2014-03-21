<?xml version='1.0' encoding='UTF-8'?>
<Project Type="Project" LVVersion="13008000">
	<Property Name="NI.LV.All.SourceOnly" Type="Bool">true</Property>
	<Property Name="NI.Project.Description" Type="Str"></Property>
	<Item Name="My Computer" Type="My Computer">
		<Property Name="NI.SortType" Type="Int">3</Property>
		<Property Name="server.app.propertiesEnabled" Type="Bool">true</Property>
		<Property Name="server.control.propertiesEnabled" Type="Bool">true</Property>
		<Property Name="server.tcp.enabled" Type="Bool">false</Property>
		<Property Name="server.tcp.port" Type="Int">0</Property>
		<Property Name="server.tcp.serviceName" Type="Str">My Computer/VI Server</Property>
		<Property Name="server.tcp.serviceName.default" Type="Str">My Computer/VI Server</Property>
		<Property Name="server.vi.callsEnabled" Type="Bool">true</Property>
		<Property Name="server.vi.propertiesEnabled" Type="Bool">true</Property>
		<Property Name="specify.custom.address" Type="Bool">false</Property>
		<Item Name="Andor" Type="Folder">
			<Item Name="Andor_settings.ctl" Type="VI" URL="../Camera/Andor/Andor_settings.ctl"/>
			<Item Name="move_andor_files.vi" Type="VI" URL="../Camera/Andor/move_andor_files.vi"/>
			<Item Name="Andor_load_xml.vi" Type="VI" URL="../config_file_io/Andor_load_xml.vi"/>
		</Item>
		<Item Name="config" Type="Folder">
			<Item Name="string_to_boolean.vi" Type="VI" URL="../config_file_io/string_to_boolean.vi"/>
		</Item>
		<Item Name="Arroyo" Type="Folder">
			<Item Name="TempScan.vi" Type="VI" URL="../Arroyo/TempScan.vi"/>
			<Item Name="temp_monitor.vi" Type="VI" URL="../Arroyo/temp_monitor.vi"/>
		</Item>
		<Item Name="Experiment.lvclass" Type="LVClass" URL="../Experiment/Experiment.lvclass"/>
		<Item Name="ExperimentVariables.lvclass" Type="LVClass" URL="../ExperimentVariables/ExperimentVariables.lvclass"/>
		<Item Name="Analog_Input.lvclass" Type="LVClass" URL="../Analog_Input/Analog_Input.lvclass"/>
		<Item Name="Analog_Output.lvclass" Type="LVClass" URL="../Analog_output/Analog_Output.lvclass"/>
		<Item Name="Camera.lvclass" Type="LVClass" URL="../Camera/Camera.lvclass"/>
		<Item Name="Hamamatsu_C9100-13.lvclass" Type="LVClass" URL="../Camera/Hamamatsu_C9100-13/Hamamatsu_C9100-13.lvclass"/>
		<Item Name="Counter.lvclass" Type="LVClass" URL="../Counter/Counter.lvclass"/>
		<Item Name="DAQmx_pulse_out.lvclass" Type="LVClass" URL="../DAQmx_pulse_out/DAQmx_pulse_out.lvclass"/>
		<Item Name="DDS.lvclass" Type="LVClass" URL="../DDS/DDS.lvclass"/>
		<Item Name="HSDIO.lvclass" Type="LVClass" URL="../HSDIO/HSDIO.lvclass"/>
		<Item Name="GPIB.lvclass" Type="LVClass" URL="../GPIB/GPIB.lvclass"/>
		<Item Name="HP83712B_RF_Generator.lvclass" Type="LVClass" URL="../GPIB/HP83712B_RF_Generator/HP83712B_RF_Generator.lvclass"/>
		<Item Name="HP83623A_RF_Generator.lvclass" Type="LVClass" URL="../GPIB/HP83623A_RF_Generator/HP83623A_RF_Generator.lvclass"/>
		<Item Name="HP8662A_RF_Generator.lvclass" Type="LVClass" URL="../GPIB/HP8662A_RF_Generator/HP8662A_RF_Generator.lvclass"/>
		<Item Name="PI_Piezo.lvclass" Type="LVClass" URL="../PI_piezo/PI_Piezo.lvclass"/>
		<Item Name="PicoMotor.lvclass" Type="LVClass" URL="../PicoMotor/PicoMotor.lvclass"/>
		<Item Name="TCP_IP.lvclass" Type="LVClass" URL="../TCP_IP/TCP_IP.lvclass"/>
		<Item Name="TTL_input.lvclass" Type="LVClass" URL="../TTL_input/TTL_input.lvclass"/>
		<Item Name="Globals.vi" Type="VI" URL="../Globals.vi"/>
		<Item Name="append_to_log.vi" Type="VI" URL="../append_to_log.vi"/>
		<Item Name="handle_errors.vi" Type="VI" URL="../handle_errors.vi"/>
		<Item Name="Dependencies" Type="Dependencies">
			<Item Name="instr.lib" Type="Folder">
				<Item Name="niHSDIO_ctl Trigger DigEdge - Edge Values (Ring).ctl" Type="VI" URL="/&lt;instrlib&gt;/niHSDIO/niHSDIO.llb/niHSDIO_ctl Trigger DigEdge - Edge Values (Ring).ctl"/>
				<Item Name="niHSDIO_ctl Trigger DigLvl - Level Values (Ring).ctl" Type="VI" URL="/&lt;instrlib&gt;/niHSDIO/niHSDIO.llb/niHSDIO_ctl Trigger DigLvl - Level Values (Ring).ctl"/>
				<Item Name="niHSDIO_ctl Trigger Script - trigID Values (Ring).ctl" Type="VI" URL="/&lt;instrlib&gt;/niHSDIO/niHSDIO.llb/niHSDIO_ctl Trigger Script - trigID Values (Ring).ctl"/>
				<Item Name="niHSDIO_ctl Trigger Source Values (Ring).ctl" Type="VI" URL="/&lt;instrlib&gt;/niHSDIO/niHSDIO.llb/niHSDIO_ctl Trigger Source Values (Ring).ctl"/>
				<Item Name="niHSDIO Get Session Reference.vi" Type="VI" URL="/&lt;instrlib&gt;/niHSDIO/niHSDIO.llb/niHSDIO Get Session Reference.vi"/>
				<Item Name="niHSDIO Close.vi" Type="VI" URL="/&lt;instrlib&gt;/niHSDIO/niHSDIO.llb/niHSDIO Close.vi"/>
				<Item Name="niHSDIO IVI Error Converter.vi" Type="VI" URL="/&lt;instrlib&gt;/niHSDIO/niHSDIO.llb/niHSDIO IVI Error Converter.vi"/>
				<Item Name="niHSDIO Configure Digital Edge Start Trigger.vi" Type="VI" URL="/&lt;instrlib&gt;/niHSDIO/niHSDIO.llb/niHSDIO Configure Digital Edge Start Trigger.vi"/>
				<Item Name="niHSDIO Configure Digital Level Script Trigger.vi" Type="VI" URL="/&lt;instrlib&gt;/niHSDIO/niHSDIO.llb/niHSDIO Configure Digital Level Script Trigger.vi"/>
				<Item Name="niHSDIO Configure Digital Edge Script Trigger.vi" Type="VI" URL="/&lt;instrlib&gt;/niHSDIO/niHSDIO.llb/niHSDIO Configure Digital Edge Script Trigger.vi"/>
				<Item Name="niHSDIO Configure Multi-Sample Pattern Match Start Trigger.vi" Type="VI" URL="/&lt;instrlib&gt;/niHSDIO/niHSDIO.llb/niHSDIO Configure Multi-Sample Pattern Match Start Trigger.vi"/>
				<Item Name="niHSDIO Configure Multi-Sample Pattern Match Start Trigger (U32).vi" Type="VI" URL="/&lt;instrlib&gt;/niHSDIO/niHSDIO.llb/niHSDIO Configure Multi-Sample Pattern Match Start Trigger (U32).vi"/>
				<Item Name="niHSDIO Configure Multi-Sample Pattern Match Reference Trigger.vi" Type="VI" URL="/&lt;instrlib&gt;/niHSDIO/niHSDIO.llb/niHSDIO Configure Multi-Sample Pattern Match Reference Trigger.vi"/>
				<Item Name="niHSDIO Configure Multi-Sample Pattern Match Reference Trigger (U32).vi" Type="VI" URL="/&lt;instrlib&gt;/niHSDIO/niHSDIO.llb/niHSDIO Configure Multi-Sample Pattern Match Reference Trigger (U32).vi"/>
				<Item Name="niHSDIO Configure Multi-Sample Pattern Match Advance Trigger.vi" Type="VI" URL="/&lt;instrlib&gt;/niHSDIO/niHSDIO.llb/niHSDIO Configure Multi-Sample Pattern Match Advance Trigger.vi"/>
				<Item Name="niHSDIO Configure Multi-Sample Pattern Match Advance Trigger (U32).vi" Type="VI" URL="/&lt;instrlib&gt;/niHSDIO/niHSDIO.llb/niHSDIO Configure Multi-Sample Pattern Match Advance Trigger (U32).vi"/>
				<Item Name="niHSDIO Disable Stop Trigger.vi" Type="VI" URL="/&lt;instrlib&gt;/niHSDIO/niHSDIO.llb/niHSDIO Disable Stop Trigger.vi"/>
				<Item Name="niHSDIO Configure Software Stop Trigger.vi" Type="VI" URL="/&lt;instrlib&gt;/niHSDIO/niHSDIO.llb/niHSDIO Configure Software Stop Trigger.vi"/>
				<Item Name="niHSDIO Configure Digital Edge Stop Trigger.vi" Type="VI" URL="/&lt;instrlib&gt;/niHSDIO/niHSDIO.llb/niHSDIO Configure Digital Edge Stop Trigger.vi"/>
				<Item Name="niHSDIO_ctl Trigger DigPat - Trigger When Values (Ring).ctl" Type="VI" URL="/&lt;instrlib&gt;/niHSDIO/niHSDIO.llb/niHSDIO_ctl Trigger DigPat - Trigger When Values (Ring).ctl"/>
				<Item Name="niHSDIO Configure Pattern Match Pause Trigger (U32).vi" Type="VI" URL="/&lt;instrlib&gt;/niHSDIO/niHSDIO.llb/niHSDIO Configure Pattern Match Pause Trigger (U32).vi"/>
				<Item Name="niHSDIO Configure Pattern Match Advance Trigger (U32).vi" Type="VI" URL="/&lt;instrlib&gt;/niHSDIO/niHSDIO.llb/niHSDIO Configure Pattern Match Advance Trigger (U32).vi"/>
				<Item Name="niHSDIO Configure Pattern Match Ref Trigger (U32).vi" Type="VI" URL="/&lt;instrlib&gt;/niHSDIO/niHSDIO.llb/niHSDIO Configure Pattern Match Ref Trigger (U32).vi"/>
				<Item Name="niHSDIO Configure Pattern Match Start Trigger (U32).vi" Type="VI" URL="/&lt;instrlib&gt;/niHSDIO/niHSDIO.llb/niHSDIO Configure Pattern Match Start Trigger (U32).vi"/>
				<Item Name="niHSDIO Disable Advance Trigger.vi" Type="VI" URL="/&lt;instrlib&gt;/niHSDIO/niHSDIO.llb/niHSDIO Disable Advance Trigger.vi"/>
				<Item Name="niHSDIO Configure Software Advance Trigger.vi" Type="VI" URL="/&lt;instrlib&gt;/niHSDIO/niHSDIO.llb/niHSDIO Configure Software Advance Trigger.vi"/>
				<Item Name="niHSDIO Configure Pattern Match Advance Trigger.vi" Type="VI" URL="/&lt;instrlib&gt;/niHSDIO/niHSDIO.llb/niHSDIO Configure Pattern Match Advance Trigger.vi"/>
				<Item Name="niHSDIO Configure Digital Edge Advance Trigger.vi" Type="VI" URL="/&lt;instrlib&gt;/niHSDIO/niHSDIO.llb/niHSDIO Configure Digital Edge Advance Trigger.vi"/>
				<Item Name="niHSDIO Disable Pause Trigger.vi" Type="VI" URL="/&lt;instrlib&gt;/niHSDIO/niHSDIO.llb/niHSDIO Disable Pause Trigger.vi"/>
				<Item Name="niHSDIO Configure Pattern Match Pause Trigger.vi" Type="VI" URL="/&lt;instrlib&gt;/niHSDIO/niHSDIO.llb/niHSDIO Configure Pattern Match Pause Trigger.vi"/>
				<Item Name="niHSDIO Configure Digital Level Pause Trigger.vi" Type="VI" URL="/&lt;instrlib&gt;/niHSDIO/niHSDIO.llb/niHSDIO Configure Digital Level Pause Trigger.vi"/>
				<Item Name="niHSDIO Disable Script Trigger.vi" Type="VI" URL="/&lt;instrlib&gt;/niHSDIO/niHSDIO.llb/niHSDIO Disable Script Trigger.vi"/>
				<Item Name="niHSDIO Configure Software Script Trigger.vi" Type="VI" URL="/&lt;instrlib&gt;/niHSDIO/niHSDIO.llb/niHSDIO Configure Software Script Trigger.vi"/>
				<Item Name="niHSDIO Disable Ref Trigger.vi" Type="VI" URL="/&lt;instrlib&gt;/niHSDIO/niHSDIO.llb/niHSDIO Disable Ref Trigger.vi"/>
				<Item Name="niHSDIO Configure Software Ref Trigger.vi" Type="VI" URL="/&lt;instrlib&gt;/niHSDIO/niHSDIO.llb/niHSDIO Configure Software Ref Trigger.vi"/>
				<Item Name="niHSDIO Configure Pattern Match Ref Trigger.vi" Type="VI" URL="/&lt;instrlib&gt;/niHSDIO/niHSDIO.llb/niHSDIO Configure Pattern Match Ref Trigger.vi"/>
				<Item Name="niHSDIO Configure Digital Edge Ref Trigger.vi" Type="VI" URL="/&lt;instrlib&gt;/niHSDIO/niHSDIO.llb/niHSDIO Configure Digital Edge Ref Trigger.vi"/>
				<Item Name="niHSDIO Disable Start Trigger.vi" Type="VI" URL="/&lt;instrlib&gt;/niHSDIO/niHSDIO.llb/niHSDIO Disable Start Trigger.vi"/>
				<Item Name="niHSDIO Configure Software Start Trigger.vi" Type="VI" URL="/&lt;instrlib&gt;/niHSDIO/niHSDIO.llb/niHSDIO Configure Software Start Trigger.vi"/>
				<Item Name="niHSDIO Configure Pattern Match Start Trigger.vi" Type="VI" URL="/&lt;instrlib&gt;/niHSDIO/niHSDIO.llb/niHSDIO Configure Pattern Match Start Trigger.vi"/>
				<Item Name="niHSDIO Configure Trigger.vi" Type="VI" URL="/&lt;instrlib&gt;/niHSDIO/niHSDIO.llb/niHSDIO Configure Trigger.vi"/>
				<Item Name="niHSDIO Configure Idle State (String).vi" Type="VI" URL="/&lt;instrlib&gt;/niHSDIO/niHSDIO.llb/niHSDIO Configure Idle State (String).vi"/>
				<Item Name="niHSDIO Configure Idle State (U32).vi" Type="VI" URL="/&lt;instrlib&gt;/niHSDIO/niHSDIO.llb/niHSDIO Configure Idle State (U32).vi"/>
				<Item Name="niHSDIO Configure Idle State.vi" Type="VI" URL="/&lt;instrlib&gt;/niHSDIO/niHSDIO.llb/niHSDIO Configure Idle State.vi"/>
				<Item Name="niHSDIO Configure Initial State (String).vi" Type="VI" URL="/&lt;instrlib&gt;/niHSDIO/niHSDIO.llb/niHSDIO Configure Initial State (String).vi"/>
				<Item Name="niHSDIO Configure Initial State (U32).vi" Type="VI" URL="/&lt;instrlib&gt;/niHSDIO/niHSDIO.llb/niHSDIO Configure Initial State (U32).vi"/>
				<Item Name="niHSDIO Configure Initial State.vi" Type="VI" URL="/&lt;instrlib&gt;/niHSDIO/niHSDIO.llb/niHSDIO Configure Initial State.vi"/>
				<Item Name="niHSDIO_ctl Generation Mode Values (Ring).ctl" Type="VI" URL="/&lt;instrlib&gt;/niHSDIO/niHSDIO.llb/niHSDIO_ctl Generation Mode Values (Ring).ctl"/>
				<Item Name="niHSDIO Configure Generation Mode.vi" Type="VI" URL="/&lt;instrlib&gt;/niHSDIO/niHSDIO.llb/niHSDIO Configure Generation Mode.vi"/>
				<Item Name="niHSDIO_ctl Sample Clock Source Values (ComboBox).ctl" Type="VI" URL="/&lt;instrlib&gt;/niHSDIO/niHSDIO.llb/niHSDIO_ctl Sample Clock Source Values (ComboBox).ctl"/>
				<Item Name="niHSDIO Configure Sample Clock.vi" Type="VI" URL="/&lt;instrlib&gt;/niHSDIO/niHSDIO.llb/niHSDIO Configure Sample Clock.vi"/>
				<Item Name="niHSDIO Assign Dynamic Channels.vi" Type="VI" URL="/&lt;instrlib&gt;/niHSDIO/niHSDIO.llb/niHSDIO Assign Dynamic Channels.vi"/>
				<Item Name="niHSDIO Init Generation Session.vi" Type="VI" URL="/&lt;instrlib&gt;/niHSDIO/niHSDIO.llb/niHSDIO Init Generation Session.vi"/>
				<Item Name="niHSDIO Is Done.vi" Type="VI" URL="/&lt;instrlib&gt;/niHSDIO/niHSDIO.llb/niHSDIO Is Done.vi"/>
				<Item Name="niHSDIO Delete Named Waveform.vi" Type="VI" URL="/&lt;instrlib&gt;/niHSDIO/niHSDIO.llb/niHSDIO Delete Named Waveform.vi"/>
				<Item Name="niHSDIO Initiate.vi" Type="VI" URL="/&lt;instrlib&gt;/niHSDIO/niHSDIO.llb/niHSDIO Initiate.vi"/>
				<Item Name="niHSDIO Abort.vi" Type="VI" URL="/&lt;instrlib&gt;/niHSDIO/niHSDIO.llb/niHSDIO Abort.vi"/>
				<Item Name="niHSDIO Write Script.vi" Type="VI" URL="/&lt;instrlib&gt;/niHSDIO/niHSDIO.llb/niHSDIO Write Script.vi"/>
				<Item Name="niHSDIO Write Named Waveform (Direct DMA).vi" Type="VI" URL="/&lt;instrlib&gt;/niHSDIO/niHSDIO.llb/niHSDIO Write Named Waveform (Direct DMA).vi"/>
				<Item Name="niHSDIO Write Named Waveform From File (HWS).vi" Type="VI" URL="/&lt;instrlib&gt;/niHSDIO/niHSDIO.llb/niHSDIO Write Named Waveform From File (HWS).vi"/>
				<Item Name="niHSDIO Write Named Waveform (1D U8).vi" Type="VI" URL="/&lt;instrlib&gt;/niHSDIO/niHSDIO.llb/niHSDIO Write Named Waveform (1D U8).vi"/>
				<Item Name="niHSDIO Write Named Waveform (1D U16).vi" Type="VI" URL="/&lt;instrlib&gt;/niHSDIO/niHSDIO.llb/niHSDIO Write Named Waveform (1D U16).vi"/>
				<Item Name="niHSDIO Write Named Waveform (WDT).vi" Type="VI" URL="/&lt;instrlib&gt;/niHSDIO/niHSDIO.llb/niHSDIO Write Named Waveform (WDT).vi"/>
				<Item Name="niHSDIO Write Named Waveform (1D U32).vi" Type="VI" URL="/&lt;instrlib&gt;/niHSDIO/niHSDIO.llb/niHSDIO Write Named Waveform (1D U32).vi"/>
				<Item Name="niHSDIO Write Named Waveform.vi" Type="VI" URL="/&lt;instrlib&gt;/niHSDIO/niHSDIO.llb/niHSDIO Write Named Waveform.vi"/>
			</Item>
			<Item Name="vi.lib" Type="Folder">
				<Item Name="Clear Errors.vi" Type="VI" URL="/&lt;vilib&gt;/Utility/error.llb/Clear Errors.vi"/>
				<Item Name="DAQmx Clear Task.vi" Type="VI" URL="/&lt;vilib&gt;/DAQmx/configure/task.llb/DAQmx Clear Task.vi"/>
				<Item Name="DAQmx Create Channel (AI-Voltage-Basic).vi" Type="VI" URL="/&lt;vilib&gt;/DAQmx/create/channels.llb/DAQmx Create Channel (AI-Voltage-Basic).vi"/>
				<Item Name="DAQmx Create Channel (AO-Voltage-Basic).vi" Type="VI" URL="/&lt;vilib&gt;/DAQmx/create/channels.llb/DAQmx Create Channel (AO-Voltage-Basic).vi"/>
				<Item Name="DAQmx Create Channel (CI-Count Edges).vi" Type="VI" URL="/&lt;vilib&gt;/DAQmx/create/channels.llb/DAQmx Create Channel (CI-Count Edges).vi"/>
				<Item Name="DAQmx Create Channel (DI-Digital Input).vi" Type="VI" URL="/&lt;vilib&gt;/DAQmx/create/channels.llb/DAQmx Create Channel (DI-Digital Input).vi"/>
				<Item Name="DAQmx Create Channel (DO-Digital Output).vi" Type="VI" URL="/&lt;vilib&gt;/DAQmx/create/channels.llb/DAQmx Create Channel (DO-Digital Output).vi"/>
				<Item Name="DAQmx Create Virtual Channel.vi" Type="VI" URL="/&lt;vilib&gt;/DAQmx/create/channels.llb/DAQmx Create Virtual Channel.vi"/>
				<Item Name="DAQmx Fill In Error Info.vi" Type="VI" URL="/&lt;vilib&gt;/DAQmx/miscellaneous.llb/DAQmx Fill In Error Info.vi"/>
				<Item Name="DAQmx Read (Analog 1D Wfm NChan 1Samp).vi" Type="VI" URL="/&lt;vilib&gt;/DAQmx/read.llb/DAQmx Read (Analog 1D Wfm NChan 1Samp).vi"/>
				<Item Name="DAQmx Read (Counter 1D U32 1Chan NSamp).vi" Type="VI" URL="/&lt;vilib&gt;/DAQmx/read.llb/DAQmx Read (Counter 1D U32 1Chan NSamp).vi"/>
				<Item Name="DAQmx Read (Digital 1D Bool NChan 1Samp 1Line).vi" Type="VI" URL="/&lt;vilib&gt;/DAQmx/read.llb/DAQmx Read (Digital 1D Bool NChan 1Samp 1Line).vi"/>
				<Item Name="DAQmx Read.vi" Type="VI" URL="/&lt;vilib&gt;/DAQmx/read.llb/DAQmx Read.vi"/>
				<Item Name="DAQmx Start Task.vi" Type="VI" URL="/&lt;vilib&gt;/DAQmx/configure/task.llb/DAQmx Start Task.vi"/>
				<Item Name="DAQmx Stop Task.vi" Type="VI" URL="/&lt;vilib&gt;/DAQmx/configure/task.llb/DAQmx Stop Task.vi"/>
				<Item Name="DAQmx Timing (Sample Clock).vi" Type="VI" URL="/&lt;vilib&gt;/DAQmx/configure/timing.llb/DAQmx Timing (Sample Clock).vi"/>
				<Item Name="DAQmx Timing.vi" Type="VI" URL="/&lt;vilib&gt;/DAQmx/configure/timing.llb/DAQmx Timing.vi"/>
				<Item Name="DialogType.ctl" Type="VI" URL="/&lt;vilib&gt;/Utility/error.llb/DialogType.ctl"/>
				<Item Name="Error Cluster From Error Code.vi" Type="VI" URL="/&lt;vilib&gt;/Utility/error.llb/Error Cluster From Error Code.vi"/>
				<Item Name="Image Type" Type="VI" URL="/&lt;vilib&gt;/vision/Image Controls.llb/Image Type"/>
				<Item Name="IMAQ Attribute.vi" Type="VI" URL="/&lt;vilib&gt;/vision/driver/imaqhl.llb/IMAQ Attribute.vi"/>
				<Item Name="IMAQ Create" Type="VI" URL="/&lt;vilib&gt;/vision/Basics.llb/IMAQ Create"/>
				<Item Name="IMAQ Extract Buffer Old Style.vi" Type="VI" URL="/&lt;vilib&gt;/vision/driver/DLLCalls.llb/IMAQ Extract Buffer Old Style.vi"/>
				<Item Name="IMAQ Extract Buffer.vi" Type="VI" URL="/&lt;vilib&gt;/vision/driver/imaqll.llb/IMAQ Extract Buffer.vi"/>
				<Item Name="IMAQ Image.ctl" Type="VI" URL="/&lt;vilib&gt;/vision/Image Controls.llb/IMAQ Image.ctl"/>
				<Item Name="IMAQ ImageToArray" Type="VI" URL="/&lt;vilib&gt;/vision/Basics.llb/IMAQ ImageToArray"/>
				<Item Name="IMAQ Status.vi" Type="VI" URL="/&lt;vilib&gt;/vision/driver/imaqll.llb/IMAQ Status.vi"/>
				<Item Name="imgBufferElement.vi" Type="VI" URL="/&lt;vilib&gt;/vision/driver/DLLCalls.llb/imgBufferElement.vi"/>
				<Item Name="imgGetBufList.vi" Type="VI" URL="/&lt;vilib&gt;/vision/driver/DLLCalls.llb/imgGetBufList.vi"/>
				<Item Name="imgIsNewStyleInterface.vi" Type="VI" URL="/&lt;vilib&gt;/vision/driver/DLLCalls.llb/imgIsNewStyleInterface.vi"/>
				<Item Name="imgSessionExamineBuffer.vi" Type="VI" URL="/&lt;vilib&gt;/vision/driver/DLLCalls.llb/imgSessionExamineBuffer.vi"/>
				<Item Name="imgSessionReleaseBuffer.vi" Type="VI" URL="/&lt;vilib&gt;/vision/driver/DLLCalls.llb/imgSessionReleaseBuffer.vi"/>
				<Item Name="imgSessionStatus.vi" Type="VI" URL="/&lt;vilib&gt;/vision/driver/DLLCalls.llb/imgSessionStatus.vi"/>
				<Item Name="imgUpdateErrorCluster.vi" Type="VI" URL="/&lt;vilib&gt;/vision/driver/DLLCalls.llb/imgUpdateErrorCluster.vi"/>
				<Item Name="imgWaitForIMAQOccurrence.vi" Type="VI" URL="/&lt;vilib&gt;/vision/driver/DLLCalls.llb/imgWaitForIMAQOccurrence.vi"/>
				<Item Name="NI-845x Fill in Error Info.vi" Type="VI" URL="/&lt;vilib&gt;/ni845x/ni845x.llb/NI-845x Fill in Error Info.vi"/>
				<Item Name="NI-845x SPI Create Script Reference.vi" Type="VI" URL="/&lt;vilib&gt;/ni845x/ni845x.llb/NI-845x SPI Create Script Reference.vi"/>
				<Item Name="NI-845x SPI Extract Script Read Data.vi" Type="VI" URL="/&lt;vilib&gt;/ni845x/ni845x.llb/NI-845x SPI Extract Script Read Data.vi"/>
				<Item Name="NI-845x SPI Run Script.vi" Type="VI" URL="/&lt;vilib&gt;/ni845x/ni845x.llb/NI-845x SPI Run Script.vi"/>
				<Item Name="NI-845x SPI Script Clock Polarity Phase.vi" Type="VI" URL="/&lt;vilib&gt;/ni845x/ni845x.llb/NI-845x SPI Script Clock Polarity Phase.vi"/>
				<Item Name="NI-845x SPI Script Clock Rate.vi" Type="VI" URL="/&lt;vilib&gt;/ni845x/ni845x.llb/NI-845x SPI Script Clock Rate.vi"/>
				<Item Name="NI-845x SPI Script CS High.vi" Type="VI" URL="/&lt;vilib&gt;/ni845x/ni845x.llb/NI-845x SPI Script CS High.vi"/>
				<Item Name="NI-845x SPI Script CS Low.vi" Type="VI" URL="/&lt;vilib&gt;/ni845x/ni845x.llb/NI-845x SPI Script CS Low.vi"/>
				<Item Name="NI-845x SPI Script Delay.vi" Type="VI" URL="/&lt;vilib&gt;/ni845x/ni845x.llb/NI-845x SPI Script Delay.vi"/>
				<Item Name="NI-845x SPI Script DIO Configure Line.vi" Type="VI" URL="/&lt;vilib&gt;/ni845x/ni845x.llb/NI-845x SPI Script DIO Configure Line.vi"/>
				<Item Name="NI-845x SPI Script DIO Write Line.vi" Type="VI" URL="/&lt;vilib&gt;/ni845x/ni845x.llb/NI-845x SPI Script DIO Write Line.vi"/>
				<Item Name="NI-845x SPI Script Enable SPI.vi" Type="VI" URL="/&lt;vilib&gt;/ni845x/ni845x.llb/NI-845x SPI Script Enable SPI.vi"/>
				<Item Name="NI-845x SPI Script Write Read.vi" Type="VI" URL="/&lt;vilib&gt;/ni845x/ni845x.llb/NI-845x SPI Script Write Read.vi"/>
				<Item Name="ni845xControl.ctl" Type="VI" URL="/&lt;vilib&gt;/ni845x/ni845x.llb/ni845xControl.ctl"/>
				<Item Name="ni845xDioLineConfiguration.ctl" Type="VI" URL="/&lt;vilib&gt;/ni845x/ni845x.llb/ni845xDioLineConfiguration.ctl"/>
				<Item Name="ni845xDioLineWriteValue.ctl" Type="VI" URL="/&lt;vilib&gt;/ni845x/ni845x.llb/ni845xDioLineWriteValue.ctl"/>
				<Item Name="ni845xSpiScriptControl.ctl" Type="VI" URL="/&lt;vilib&gt;/ni845x/ni845x.llb/ni845xSpiScriptControl.ctl"/>
				<Item Name="NI_AALBase.lvlib" Type="Library" URL="/&lt;vilib&gt;/Analysis/NI_AALBase.lvlib"/>
				<Item Name="NI_Gmath.lvlib" Type="Library" URL="/&lt;vilib&gt;/gmath/NI_Gmath.lvlib"/>
				<Item Name="SessionLookUp.vi" Type="VI" URL="/&lt;vilib&gt;/vision/driver/DLLCalls.llb/SessionLookUp.vi"/>
				<Item Name="Simple Error Handler.vi" Type="VI" URL="/&lt;vilib&gt;/Utility/error.llb/Simple Error Handler.vi"/>
				<Item Name="subDisplayMessage.vi" Type="VI" URL="/&lt;vilib&gt;/express/express output/DisplayMessageBlock.llb/subDisplayMessage.vi"/>
				<Item Name="Write To Spreadsheet File (DBL).vi" Type="VI" URL="/&lt;vilib&gt;/Utility/file.llb/Write To Spreadsheet File (DBL).vi"/>
				<Item Name="Write To Spreadsheet File (I64).vi" Type="VI" URL="/&lt;vilib&gt;/Utility/file.llb/Write To Spreadsheet File (I64).vi"/>
				<Item Name="Write To Spreadsheet File (string).vi" Type="VI" URL="/&lt;vilib&gt;/Utility/file.llb/Write To Spreadsheet File (string).vi"/>
				<Item Name="Write To Spreadsheet File.vi" Type="VI" URL="/&lt;vilib&gt;/Utility/file.llb/Write To Spreadsheet File.vi"/>
				<Item Name="subTimeDelay.vi" Type="VI" URL="/&lt;vilib&gt;/express/express execution control/TimeDelayBlock.llb/subTimeDelay.vi"/>
				<Item Name="NI-845x SPI Script Ms Delay.vi" Type="VI" URL="/&lt;vilib&gt;/ni845x/ni845x.llb/NI-845x SPI Script Ms Delay.vi"/>
				<Item Name="NI-845x SPI Script Us Delay.vi" Type="VI" URL="/&lt;vilib&gt;/ni845x/ni845x.llb/NI-845x SPI Script Us Delay.vi"/>
				<Item Name="NI_XML.lvlib" Type="Library" URL="/&lt;vilib&gt;/xml/NI_XML.lvlib"/>
				<Item Name="Dynamic To Waveform Array.vi" Type="VI" URL="/&lt;vilib&gt;/express/express shared/transition.llb/Dynamic To Waveform Array.vi"/>
				<Item Name="Trim Whitespace.vi" Type="VI" URL="/&lt;vilib&gt;/Utility/error.llb/Trim Whitespace.vi"/>
				<Item Name="Beep.vi" Type="VI" URL="/&lt;vilib&gt;/Platform/system.llb/Beep.vi"/>
				<Item Name="Space Constant.vi" Type="VI" URL="/&lt;vilib&gt;/dlg_ctls.llb/Space Constant.vi"/>
				<Item Name="TCP Listen.vi" Type="VI" URL="/&lt;vilib&gt;/Utility/tcp.llb/TCP Listen.vi"/>
				<Item Name="Error to Warning.vi" Type="VI" URL="/&lt;vilib&gt;/Utility/error.llb/Error to Warning.vi"/>
				<Item Name="DAQmx Is Task Done.vi" Type="VI" URL="/&lt;vilib&gt;/DAQmx/configure/task.llb/DAQmx Is Task Done.vi"/>
				<Item Name="DTbl Digital Size.vi" Type="VI" URL="/&lt;vilib&gt;/Waveform/DTblOps.llb/DTbl Digital Size.vi"/>
				<Item Name="DTbl Uncompress Digital.vi" Type="VI" URL="/&lt;vilib&gt;/Waveform/DTblOps.llb/DTbl Uncompress Digital.vi"/>
				<Item Name="DWDT Uncompress Digital.vi" Type="VI" URL="/&lt;vilib&gt;/Waveform/DWDTOps.llb/DWDT Uncompress Digital.vi"/>
				<Item Name="DAQmx Start Trigger (Digital Edge).vi" Type="VI" URL="/&lt;vilib&gt;/DAQmx/configure/trigger.llb/DAQmx Start Trigger (Digital Edge).vi"/>
				<Item Name="DAQmx Trigger.vi" Type="VI" URL="/&lt;vilib&gt;/DAQmx/configure/trigger.llb/DAQmx Trigger.vi"/>
				<Item Name="DAQmx Write (Digital Wfm 1Chan NSamp).vi" Type="VI" URL="/&lt;vilib&gt;/DAQmx/write.llb/DAQmx Write (Digital Wfm 1Chan NSamp).vi"/>
				<Item Name="DAQmx Write (Analog 1D Wfm NChan NSamp).vi" Type="VI" URL="/&lt;vilib&gt;/DAQmx/write.llb/DAQmx Write (Analog 1D Wfm NChan NSamp).vi"/>
				<Item Name="DAQmx Write.vi" Type="VI" URL="/&lt;vilib&gt;/DAQmx/write.llb/DAQmx Write.vi"/>
				<Item Name="Three Button Dialog.vi" Type="VI" URL="/&lt;vilib&gt;/Utility/error.llb/Three Button Dialog.vi"/>
				<Item Name="General Error Handler.vi" Type="VI" URL="/&lt;vilib&gt;/Utility/error.llb/General Error Handler.vi"/>
				<Item Name="IMAQ Configure Buffer.vi" Type="VI" URL="/&lt;vilib&gt;/vision/driver/imaqll.llb/IMAQ Configure Buffer.vi"/>
				<Item Name="imgSessionAcquire.vi" Type="VI" URL="/&lt;vilib&gt;/vision/driver/DLLCalls.llb/imgSessionAcquire.vi"/>
				<Item Name="imgSessionConfigure.vi" Type="VI" URL="/&lt;vilib&gt;/vision/driver/DLLCalls.llb/imgSessionConfigure.vi"/>
				<Item Name="imgMemLock.vi" Type="VI" URL="/&lt;vilib&gt;/vision/driver/DLLCalls.llb/imgMemLock.vi"/>
				<Item Name="imgEnsureEqualBorders.vi" Type="VI" URL="/&lt;vilib&gt;/vision/driver/DLLCalls.llb/imgEnsureEqualBorders.vi"/>
				<Item Name="IMAQ Start.vi" Type="VI" URL="/&lt;vilib&gt;/vision/driver/imaqll.llb/IMAQ Start.vi"/>
				<Item Name="imgDisposeBufList.vi" Type="VI" URL="/&lt;vilib&gt;/vision/driver/DLLCalls.llb/imgDisposeBufList.vi"/>
				<Item Name="imgSessionAttribute.vi" Type="VI" URL="/&lt;vilib&gt;/vision/driver/DLLCalls.llb/imgSessionAttribute.vi"/>
				<Item Name="imgSetRoi.vi" Type="VI" URL="/&lt;vilib&gt;/vision/driver/DLLCalls.llb/imgSetRoi.vi"/>
				<Item Name="imgCreateBufList.vi" Type="VI" URL="/&lt;vilib&gt;/vision/driver/DLLCalls.llb/imgCreateBufList.vi"/>
				<Item Name="IMAQ Configure List.vi" Type="VI" URL="/&lt;vilib&gt;/vision/driver/imaqll.llb/IMAQ Configure List.vi"/>
				<Item Name="imgClose.vi" Type="VI" URL="/&lt;vilib&gt;/vision/driver/DLLCalls.llb/imgClose.vi"/>
				<Item Name="IMAQRegisterSession.vi" Type="VI" URL="/&lt;vilib&gt;/vision/driver/DLLCalls.llb/IMAQRegisterSession.vi"/>
				<Item Name="imgSessionOpen.vi" Type="VI" URL="/&lt;vilib&gt;/vision/driver/DLLCalls.llb/imgSessionOpen.vi"/>
				<Item Name="imgInterfaceOpen.vi" Type="VI" URL="/&lt;vilib&gt;/vision/driver/DLLCalls.llb/imgInterfaceOpen.vi"/>
				<Item Name="IMAQ Init.vi" Type="VI" URL="/&lt;vilib&gt;/vision/driver/imaqhl.llb/IMAQ Init.vi"/>
				<Item Name="IMAQ Serial Read.vi" Type="VI" URL="/&lt;vilib&gt;/vision/driver/imaqll.llb/IMAQ Serial Read.vi"/>
				<Item Name="IMAQ Serial Write.vi" Type="VI" URL="/&lt;vilib&gt;/vision/driver/imaqll.llb/IMAQ Serial Write.vi"/>
				<Item Name="IMAQ Dispose" Type="VI" URL="/&lt;vilib&gt;/vision/Basics.llb/IMAQ Dispose"/>
				<Item Name="IMAQUnregisterSession.vi" Type="VI" URL="/&lt;vilib&gt;/vision/driver/DLLCalls.llb/IMAQUnregisterSession.vi"/>
				<Item Name="IMAQ Close.vi" Type="VI" URL="/&lt;vilib&gt;/vision/driver/imaqhl.llb/IMAQ Close.vi"/>
				<Item Name="imgSessionStopAcquisition.vi" Type="VI" URL="/&lt;vilib&gt;/vision/driver/DLLCalls.llb/imgSessionStopAcquisition.vi"/>
				<Item Name="IMAQ Stop.vi" Type="VI" URL="/&lt;vilib&gt;/vision/driver/imaqll.llb/IMAQ Stop.vi"/>
				<Item Name="DAQmx Configure Input Buffer.vi" Type="VI" URL="/&lt;vilib&gt;/DAQmx/configure/buffer.llb/DAQmx Configure Input Buffer.vi"/>
				<Item Name="GPIB Status Boolean Array.ctl" Type="VI" URL="/&lt;vilib&gt;/Instr/_visa.llb/GPIB Status Boolean Array.ctl"/>
				<Item Name="NI-845x SPI Script DIO Configure Port.vi" Type="VI" URL="/&lt;vilib&gt;/ni845x/ni845x.llb/NI-845x SPI Script DIO Configure Port.vi"/>
				<Item Name="NI-845x SPI Script Disable SPI.vi" Type="VI" URL="/&lt;vilib&gt;/ni845x/ni845x.llb/NI-845x SPI Script Disable SPI.vi"/>
				<Item Name="NI-845x Close Device Reference.vi" Type="VI" URL="/&lt;vilib&gt;/ni845x/ni845x.llb/NI-845x Close Device Reference.vi"/>
				<Item Name="ni845xI2cSlaveConfiguration.ctl" Type="VI" URL="/&lt;vilib&gt;/ni845x/ni845x.llb/ni845xI2cSlaveConfiguration.ctl"/>
				<Item Name="NI-845x I2C Slave Close Configuration Reference.vi" Type="VI" URL="/&lt;vilib&gt;/ni845x/ni845x.llb/NI-845x I2C Slave Close Configuration Reference.vi"/>
				<Item Name="ni845xSpiStreamConfiguration.ctl" Type="VI" URL="/&lt;vilib&gt;/ni845x/ni845x.llb/ni845xSpiStreamConfiguration.ctl"/>
				<Item Name="NI-845x SPI Stream Close Configuration Reference.vi" Type="VI" URL="/&lt;vilib&gt;/ni845x/ni845x.llb/NI-845x SPI Stream Close Configuration Reference.vi"/>
				<Item Name="ni845xI2cScriptControl.ctl" Type="VI" URL="/&lt;vilib&gt;/ni845x/ni845x.llb/ni845xI2cScriptControl.ctl"/>
				<Item Name="NI-845x I2C Close Script Reference.vi" Type="VI" URL="/&lt;vilib&gt;/ni845x/ni845x.llb/NI-845x I2C Close Script Reference.vi"/>
				<Item Name="ni845xI2cConfiguration.ctl" Type="VI" URL="/&lt;vilib&gt;/ni845x/ni845x.llb/ni845xI2cConfiguration.ctl"/>
				<Item Name="NI-845x I2C Close Configuration Reference.vi" Type="VI" URL="/&lt;vilib&gt;/ni845x/ni845x.llb/NI-845x I2C Close Configuration Reference.vi"/>
				<Item Name="NI-845x SPI Close Script Reference.vi" Type="VI" URL="/&lt;vilib&gt;/ni845x/ni845x.llb/NI-845x SPI Close Script Reference.vi"/>
				<Item Name="ni845xSpiConfiguration.ctl" Type="VI" URL="/&lt;vilib&gt;/ni845x/ni845x.llb/ni845xSpiConfiguration.ctl"/>
				<Item Name="NI-845x SPI Close Configuration Reference.vi" Type="VI" URL="/&lt;vilib&gt;/ni845x/ni845x.llb/NI-845x SPI Close Configuration Reference.vi"/>
				<Item Name="NI-845x Close Reference.vi" Type="VI" URL="/&lt;vilib&gt;/ni845x/ni845x.llb/NI-845x Close Reference.vi"/>
				<Item Name="LVBoundsTypeDef.ctl" Type="VI" URL="/&lt;vilib&gt;/Utility/miscctls.llb/LVBoundsTypeDef.ctl"/>
				<Item Name="Get String Text Bounds.vi" Type="VI" URL="/&lt;vilib&gt;/Utility/error.llb/Get String Text Bounds.vi"/>
				<Item Name="Get Text Rect.vi" Type="VI" URL="/&lt;vilib&gt;/picture/picture.llb/Get Text Rect.vi"/>
				<Item Name="Convert property node font to graphics font.vi" Type="VI" URL="/&lt;vilib&gt;/Utility/error.llb/Convert property node font to graphics font.vi"/>
				<Item Name="Longest Line Length in Pixels.vi" Type="VI" URL="/&lt;vilib&gt;/Utility/error.llb/Longest Line Length in Pixels.vi"/>
				<Item Name="Three Button Dialog CORE.vi" Type="VI" URL="/&lt;vilib&gt;/Utility/error.llb/Three Button Dialog CORE.vi"/>
				<Item Name="GetHelpDir.vi" Type="VI" URL="/&lt;vilib&gt;/Utility/error.llb/GetHelpDir.vi"/>
				<Item Name="BuildHelpPath.vi" Type="VI" URL="/&lt;vilib&gt;/Utility/error.llb/BuildHelpPath.vi"/>
				<Item Name="DialogTypeEnum.ctl" Type="VI" URL="/&lt;vilib&gt;/Utility/error.llb/DialogTypeEnum.ctl"/>
				<Item Name="Not Found Dialog.vi" Type="VI" URL="/&lt;vilib&gt;/Utility/error.llb/Not Found Dialog.vi"/>
				<Item Name="Set Bold Text.vi" Type="VI" URL="/&lt;vilib&gt;/Utility/error.llb/Set Bold Text.vi"/>
				<Item Name="eventvkey.ctl" Type="VI" URL="/&lt;vilib&gt;/event_ctls.llb/eventvkey.ctl"/>
				<Item Name="ErrWarn.ctl" Type="VI" URL="/&lt;vilib&gt;/Utility/error.llb/ErrWarn.ctl"/>
				<Item Name="Details Display Dialog.vi" Type="VI" URL="/&lt;vilib&gt;/Utility/error.llb/Details Display Dialog.vi"/>
				<Item Name="Search and Replace Pattern.vi" Type="VI" URL="/&lt;vilib&gt;/Utility/error.llb/Search and Replace Pattern.vi"/>
				<Item Name="Find Tag.vi" Type="VI" URL="/&lt;vilib&gt;/Utility/error.llb/Find Tag.vi"/>
				<Item Name="Format Message String.vi" Type="VI" URL="/&lt;vilib&gt;/Utility/error.llb/Format Message String.vi"/>
				<Item Name="whitespace.ctl" Type="VI" URL="/&lt;vilib&gt;/Utility/error.llb/whitespace.ctl"/>
				<Item Name="Error Code Database.vi" Type="VI" URL="/&lt;vilib&gt;/Utility/error.llb/Error Code Database.vi"/>
				<Item Name="GetRTHostConnectedProp.vi" Type="VI" URL="/&lt;vilib&gt;/Utility/error.llb/GetRTHostConnectedProp.vi"/>
				<Item Name="Set String Value.vi" Type="VI" URL="/&lt;vilib&gt;/Utility/error.llb/Set String Value.vi"/>
				<Item Name="TagReturnType.ctl" Type="VI" URL="/&lt;vilib&gt;/Utility/error.llb/TagReturnType.ctl"/>
				<Item Name="Check Special Tags.vi" Type="VI" URL="/&lt;vilib&gt;/Utility/error.llb/Check Special Tags.vi"/>
				<Item Name="General Error Handler CORE.vi" Type="VI" URL="/&lt;vilib&gt;/Utility/error.llb/General Error Handler CORE.vi"/>
				<Item Name="TCP Listen List Operations.ctl" Type="VI" URL="/&lt;vilib&gt;/Utility/tcp.llb/TCP Listen List Operations.ctl"/>
				<Item Name="TCP Listen Internal List.vi" Type="VI" URL="/&lt;vilib&gt;/Utility/tcp.llb/TCP Listen Internal List.vi"/>
				<Item Name="Internecine Avoider.vi" Type="VI" URL="/&lt;vilib&gt;/Utility/tcp.llb/Internecine Avoider.vi"/>
				<Item Name="Write Spreadsheet String.vi" Type="VI" URL="/&lt;vilib&gt;/Utility/file.llb/Write Spreadsheet String.vi"/>
				<Item Name="ex_CorrectErrorChain.vi" Type="VI" URL="/&lt;vilib&gt;/express/express shared/ex_CorrectErrorChain.vi"/>
				<Item Name="DAQmx Read (Analog 1D Wfm NChan NSamp).vi" Type="VI" URL="/&lt;vilib&gt;/DAQmx/read.llb/DAQmx Read (Analog 1D Wfm NChan NSamp).vi"/>
				<Item Name="DAQmx Read (Analog 1D DBL 1Chan NSamp).vi" Type="VI" URL="/&lt;vilib&gt;/DAQmx/read.llb/DAQmx Read (Analog 1D DBL 1Chan NSamp).vi"/>
				<Item Name="DAQmx Read (Analog 1D DBL NChan 1Samp).vi" Type="VI" URL="/&lt;vilib&gt;/DAQmx/read.llb/DAQmx Read (Analog 1D DBL NChan 1Samp).vi"/>
				<Item Name="DAQmx Read (Analog 2D DBL NChan NSamp).vi" Type="VI" URL="/&lt;vilib&gt;/DAQmx/read.llb/DAQmx Read (Analog 2D DBL NChan NSamp).vi"/>
				<Item Name="DAQmx Read (Analog DBL 1Chan 1Samp).vi" Type="VI" URL="/&lt;vilib&gt;/DAQmx/read.llb/DAQmx Read (Analog DBL 1Chan 1Samp).vi"/>
				<Item Name="DAQmx Read (Analog Wfm 1Chan 1Samp).vi" Type="VI" URL="/&lt;vilib&gt;/DAQmx/read.llb/DAQmx Read (Analog Wfm 1Chan 1Samp).vi"/>
				<Item Name="DAQmx Read (Analog Wfm 1Chan NSamp).vi" Type="VI" URL="/&lt;vilib&gt;/DAQmx/read.llb/DAQmx Read (Analog Wfm 1Chan NSamp).vi"/>
				<Item Name="DAQmx Read (Digital 1D Bool 1Chan 1Samp).vi" Type="VI" URL="/&lt;vilib&gt;/DAQmx/read.llb/DAQmx Read (Digital 1D Bool 1Chan 1Samp).vi"/>
				<Item Name="DAQmx Read (Digital 1D U32 1Chan NSamp).vi" Type="VI" URL="/&lt;vilib&gt;/DAQmx/read.llb/DAQmx Read (Digital 1D U32 1Chan NSamp).vi"/>
				<Item Name="DAQmx Read (Digital 1D U8 1Chan NSamp).vi" Type="VI" URL="/&lt;vilib&gt;/DAQmx/read.llb/DAQmx Read (Digital 1D U8 1Chan NSamp).vi"/>
				<Item Name="DAQmx Read (Digital 1D Wfm NChan 1Samp).vi" Type="VI" URL="/&lt;vilib&gt;/DAQmx/read.llb/DAQmx Read (Digital 1D Wfm NChan 1Samp).vi"/>
				<Item Name="DAQmx Read (Digital 2D U32 NChan NSamp).vi" Type="VI" URL="/&lt;vilib&gt;/DAQmx/read.llb/DAQmx Read (Digital 2D U32 NChan NSamp).vi"/>
				<Item Name="DAQmx Read (Digital 2D U8 NChan NSamp).vi" Type="VI" URL="/&lt;vilib&gt;/DAQmx/read.llb/DAQmx Read (Digital 2D U8 NChan NSamp).vi"/>
				<Item Name="DAQmx Read (Digital Bool 1Line 1Point).vi" Type="VI" URL="/&lt;vilib&gt;/DAQmx/read.llb/DAQmx Read (Digital Bool 1Line 1Point).vi"/>
				<Item Name="DAQmx Read (Digital Wfm 1Chan NSamp).vi" Type="VI" URL="/&lt;vilib&gt;/DAQmx/read.llb/DAQmx Read (Digital Wfm 1Chan NSamp).vi"/>
				<Item Name="DAQmx Read (Raw 1D I16).vi" Type="VI" URL="/&lt;vilib&gt;/DAQmx/read.llb/DAQmx Read (Raw 1D I16).vi"/>
				<Item Name="DAQmx Read (Raw 1D I32).vi" Type="VI" URL="/&lt;vilib&gt;/DAQmx/read.llb/DAQmx Read (Raw 1D I32).vi"/>
				<Item Name="DAQmx Read (Raw 1D I8).vi" Type="VI" URL="/&lt;vilib&gt;/DAQmx/read.llb/DAQmx Read (Raw 1D I8).vi"/>
				<Item Name="DAQmx Read (Raw 1D U16).vi" Type="VI" URL="/&lt;vilib&gt;/DAQmx/read.llb/DAQmx Read (Raw 1D U16).vi"/>
				<Item Name="DAQmx Read (Raw 1D U32).vi" Type="VI" URL="/&lt;vilib&gt;/DAQmx/read.llb/DAQmx Read (Raw 1D U32).vi"/>
				<Item Name="DAQmx Read (Raw 1D U8).vi" Type="VI" URL="/&lt;vilib&gt;/DAQmx/read.llb/DAQmx Read (Raw 1D U8).vi"/>
				<Item Name="DAQmx Read (Digital 1D Wfm NChan NSamp).vi" Type="VI" URL="/&lt;vilib&gt;/DAQmx/read.llb/DAQmx Read (Digital 1D Wfm NChan NSamp).vi"/>
				<Item Name="DAQmx Read (Digital Wfm 1Chan 1Samp).vi" Type="VI" URL="/&lt;vilib&gt;/DAQmx/read.llb/DAQmx Read (Digital Wfm 1Chan 1Samp).vi"/>
				<Item Name="DAQmx Read (Counter 1D DBL 1Chan NSamp).vi" Type="VI" URL="/&lt;vilib&gt;/DAQmx/read.llb/DAQmx Read (Counter 1D DBL 1Chan NSamp).vi"/>
				<Item Name="DAQmx Read (Counter DBL 1Chan 1Samp).vi" Type="VI" URL="/&lt;vilib&gt;/DAQmx/read.llb/DAQmx Read (Counter DBL 1Chan 1Samp).vi"/>
				<Item Name="DAQmx Read (Counter U32 1Chan 1Samp).vi" Type="VI" URL="/&lt;vilib&gt;/DAQmx/read.llb/DAQmx Read (Counter U32 1Chan 1Samp).vi"/>
				<Item Name="DAQmx Read (Digital 1D U8 NChan 1Samp).vi" Type="VI" URL="/&lt;vilib&gt;/DAQmx/read.llb/DAQmx Read (Digital 1D U8 NChan 1Samp).vi"/>
				<Item Name="DAQmx Read (Digital 1D U32 NChan 1Samp).vi" Type="VI" URL="/&lt;vilib&gt;/DAQmx/read.llb/DAQmx Read (Digital 1D U32 NChan 1Samp).vi"/>
				<Item Name="DAQmx Read (Digital U8 1Chan 1Samp).vi" Type="VI" URL="/&lt;vilib&gt;/DAQmx/read.llb/DAQmx Read (Digital U8 1Chan 1Samp).vi"/>
				<Item Name="DAQmx Read (Digital U32 1Chan 1Samp).vi" Type="VI" URL="/&lt;vilib&gt;/DAQmx/read.llb/DAQmx Read (Digital U32 1Chan 1Samp).vi"/>
				<Item Name="DAQmx Read (Digital 2D Bool NChan 1Samp NLine).vi" Type="VI" URL="/&lt;vilib&gt;/DAQmx/read.llb/DAQmx Read (Digital 2D Bool NChan 1Samp NLine).vi"/>
				<Item Name="DAQmx Read (Analog 2D U16 NChan NSamp).vi" Type="VI" URL="/&lt;vilib&gt;/DAQmx/read.llb/DAQmx Read (Analog 2D U16 NChan NSamp).vi"/>
				<Item Name="DAQmx Read (Analog 2D I16 NChan NSamp).vi" Type="VI" URL="/&lt;vilib&gt;/DAQmx/read.llb/DAQmx Read (Analog 2D I16 NChan NSamp).vi"/>
				<Item Name="DAQmx Read (Analog 2D I32 NChan NSamp).vi" Type="VI" URL="/&lt;vilib&gt;/DAQmx/read.llb/DAQmx Read (Analog 2D I32 NChan NSamp).vi"/>
				<Item Name="DAQmx Read (Analog 2D U32 NChan NSamp).vi" Type="VI" URL="/&lt;vilib&gt;/DAQmx/read.llb/DAQmx Read (Analog 2D U32 NChan NSamp).vi"/>
				<Item Name="DAQmx Read (Digital U16 1Chan 1Samp).vi" Type="VI" URL="/&lt;vilib&gt;/DAQmx/read.llb/DAQmx Read (Digital U16 1Chan 1Samp).vi"/>
				<Item Name="DAQmx Read (Digital 1D U16 1Chan NSamp).vi" Type="VI" URL="/&lt;vilib&gt;/DAQmx/read.llb/DAQmx Read (Digital 1D U16 1Chan NSamp).vi"/>
				<Item Name="DAQmx Read (Digital 1D U16 NChan 1Samp).vi" Type="VI" URL="/&lt;vilib&gt;/DAQmx/read.llb/DAQmx Read (Digital 1D U16 NChan 1Samp).vi"/>
				<Item Name="DAQmx Read (Digital 2D U16 NChan NSamp).vi" Type="VI" URL="/&lt;vilib&gt;/DAQmx/read.llb/DAQmx Read (Digital 2D U16 NChan NSamp).vi"/>
				<Item Name="DAQmx Read (Counter 1D Pulse Freq 1 Chan NSamp).vi" Type="VI" URL="/&lt;vilib&gt;/DAQmx/read.llb/DAQmx Read (Counter 1D Pulse Freq 1 Chan NSamp).vi"/>
				<Item Name="DAQmx Read (Counter 1D Pulse Ticks 1Chan NSamp).vi" Type="VI" URL="/&lt;vilib&gt;/DAQmx/read.llb/DAQmx Read (Counter 1D Pulse Ticks 1Chan NSamp).vi"/>
				<Item Name="DAQmx Read (Counter 1D Pulse Time 1Chan NSamp).vi" Type="VI" URL="/&lt;vilib&gt;/DAQmx/read.llb/DAQmx Read (Counter 1D Pulse Time 1Chan NSamp).vi"/>
				<Item Name="DAQmx Read (Counter Pulse Freq 1 Chan 1 Samp).vi" Type="VI" URL="/&lt;vilib&gt;/DAQmx/read.llb/DAQmx Read (Counter Pulse Freq 1 Chan 1 Samp).vi"/>
				<Item Name="DAQmx Read (Counter Pulse Ticks 1Chan 1Samp).vi" Type="VI" URL="/&lt;vilib&gt;/DAQmx/read.llb/DAQmx Read (Counter Pulse Ticks 1Chan 1Samp).vi"/>
				<Item Name="DAQmx Read (Counter Pulse Time 1Chan 1Samp).vi" Type="VI" URL="/&lt;vilib&gt;/DAQmx/read.llb/DAQmx Read (Counter Pulse Time 1Chan 1Samp).vi"/>
				<Item Name="DAQmx Rollback Channel If Error.vi" Type="VI" URL="/&lt;vilib&gt;/DAQmx/create/channels.llb/DAQmx Rollback Channel If Error.vi"/>
				<Item Name="DAQmx Create AI Channel (sub).vi" Type="VI" URL="/&lt;vilib&gt;/DAQmx/create/channels.llb/DAQmx Create AI Channel (sub).vi"/>
				<Item Name="DAQmx Create Channel (AI-Voltage-Custom with Excitation).vi" Type="VI" URL="/&lt;vilib&gt;/DAQmx/create/channels.llb/DAQmx Create Channel (AI-Voltage-Custom with Excitation).vi"/>
				<Item Name="DAQmx Create Channel (AI-Resistance).vi" Type="VI" URL="/&lt;vilib&gt;/DAQmx/create/channels.llb/DAQmx Create Channel (AI-Resistance).vi"/>
				<Item Name="DAQmx Create Channel (AI-Temperature-Thermocouple).vi" Type="VI" URL="/&lt;vilib&gt;/DAQmx/create/channels.llb/DAQmx Create Channel (AI-Temperature-Thermocouple).vi"/>
				<Item Name="DAQmx Set CJC Parameters (sub).vi" Type="VI" URL="/&lt;vilib&gt;/DAQmx/create/channels.llb/DAQmx Set CJC Parameters (sub).vi"/>
				<Item Name="DAQmx Create Channel (AI-Temperature-RTD).vi" Type="VI" URL="/&lt;vilib&gt;/DAQmx/create/channels.llb/DAQmx Create Channel (AI-Temperature-RTD).vi"/>
				<Item Name="DAQmx Create Channel (AI-Temperature-Thermistor-Iex).vi" Type="VI" URL="/&lt;vilib&gt;/DAQmx/create/channels.llb/DAQmx Create Channel (AI-Temperature-Thermistor-Iex).vi"/>
				<Item Name="DAQmx Create Channel (AI-Temperature-Thermistor-Vex).vi" Type="VI" URL="/&lt;vilib&gt;/DAQmx/create/channels.llb/DAQmx Create Channel (AI-Temperature-Thermistor-Vex).vi"/>
				<Item Name="DAQmx Create AO Channel (sub).vi" Type="VI" URL="/&lt;vilib&gt;/DAQmx/create/channels.llb/DAQmx Create AO Channel (sub).vi"/>
				<Item Name="DAQmx Create Channel (AO-FuncGen).vi" Type="VI" URL="/&lt;vilib&gt;/DAQmx/create/channels.llb/DAQmx Create Channel (AO-FuncGen).vi"/>
				<Item Name="DAQmx Create DI Channel (sub).vi" Type="VI" URL="/&lt;vilib&gt;/DAQmx/create/channels.llb/DAQmx Create DI Channel (sub).vi"/>
				<Item Name="DAQmx Create DO Channel (sub).vi" Type="VI" URL="/&lt;vilib&gt;/DAQmx/create/channels.llb/DAQmx Create DO Channel (sub).vi"/>
				<Item Name="DAQmx Create Channel (CI-Frequency).vi" Type="VI" URL="/&lt;vilib&gt;/DAQmx/create/channels.llb/DAQmx Create Channel (CI-Frequency).vi"/>
				<Item Name="DAQmx Create CI Channel (sub).vi" Type="VI" URL="/&lt;vilib&gt;/DAQmx/create/channels.llb/DAQmx Create CI Channel (sub).vi"/>
				<Item Name="DAQmx Create Channel (CI-Period).vi" Type="VI" URL="/&lt;vilib&gt;/DAQmx/create/channels.llb/DAQmx Create Channel (CI-Period).vi"/>
				<Item Name="DAQmx Create Channel (CI-Pulse Width).vi" Type="VI" URL="/&lt;vilib&gt;/DAQmx/create/channels.llb/DAQmx Create Channel (CI-Pulse Width).vi"/>
				<Item Name="DAQmx Create Channel (CI-Semi Period).vi" Type="VI" URL="/&lt;vilib&gt;/DAQmx/create/channels.llb/DAQmx Create Channel (CI-Semi Period).vi"/>
				<Item Name="DAQmx Create Channel (AI-Current-Basic).vi" Type="VI" URL="/&lt;vilib&gt;/DAQmx/create/channels.llb/DAQmx Create Channel (AI-Current-Basic).vi"/>
				<Item Name="DAQmx Create Channel (AI-Strain-Strain Gage).vi" Type="VI" URL="/&lt;vilib&gt;/DAQmx/create/channels.llb/DAQmx Create Channel (AI-Strain-Strain Gage).vi"/>
				<Item Name="DAQmx Create Channel (AI-Temperature-Built-in Sensor).vi" Type="VI" URL="/&lt;vilib&gt;/DAQmx/create/channels.llb/DAQmx Create Channel (AI-Temperature-Built-in Sensor).vi"/>
				<Item Name="DAQmx Create Channel (AI-Frequency-Voltage).vi" Type="VI" URL="/&lt;vilib&gt;/DAQmx/create/channels.llb/DAQmx Create Channel (AI-Frequency-Voltage).vi"/>
				<Item Name="DAQmx Create Channel (CO-Pulse Generation-Frequency).vi" Type="VI" URL="/&lt;vilib&gt;/DAQmx/create/channels.llb/DAQmx Create Channel (CO-Pulse Generation-Frequency).vi"/>
				<Item Name="DAQmx Create CO Channel (sub).vi" Type="VI" URL="/&lt;vilib&gt;/DAQmx/create/channels.llb/DAQmx Create CO Channel (sub).vi"/>
				<Item Name="DAQmx Create Channel (CO-Pulse Generation-Time).vi" Type="VI" URL="/&lt;vilib&gt;/DAQmx/create/channels.llb/DAQmx Create Channel (CO-Pulse Generation-Time).vi"/>
				<Item Name="DAQmx Create Channel (CO-Pulse Generation-Ticks).vi" Type="VI" URL="/&lt;vilib&gt;/DAQmx/create/channels.llb/DAQmx Create Channel (CO-Pulse Generation-Ticks).vi"/>
				<Item Name="DAQmx Create Channel (AI-Position-LVDT).vi" Type="VI" URL="/&lt;vilib&gt;/DAQmx/create/channels.llb/DAQmx Create Channel (AI-Position-LVDT).vi"/>
				<Item Name="DAQmx Create Channel (AI-Position-RVDT).vi" Type="VI" URL="/&lt;vilib&gt;/DAQmx/create/channels.llb/DAQmx Create Channel (AI-Position-RVDT).vi"/>
				<Item Name="DAQmx Create Channel (CI-Two Edge Separation).vi" Type="VI" URL="/&lt;vilib&gt;/DAQmx/create/channels.llb/DAQmx Create Channel (CI-Two Edge Separation).vi"/>
				<Item Name="DAQmx Create Channel (AI-Acceleration-Accelerometer).vi" Type="VI" URL="/&lt;vilib&gt;/DAQmx/create/channels.llb/DAQmx Create Channel (AI-Acceleration-Accelerometer).vi"/>
				<Item Name="DAQmx Create Channel (CI-Position-Angular Encoder).vi" Type="VI" URL="/&lt;vilib&gt;/DAQmx/create/channels.llb/DAQmx Create Channel (CI-Position-Angular Encoder).vi"/>
				<Item Name="DAQmx Create Channel (CI-Position-Linear Encoder).vi" Type="VI" URL="/&lt;vilib&gt;/DAQmx/create/channels.llb/DAQmx Create Channel (CI-Position-Linear Encoder).vi"/>
				<Item Name="DAQmx Create Channel (TEDS-AI-Acceleration-Accelerometer).vi" Type="VI" URL="/&lt;vilib&gt;/DAQmx/create/channels.llb/DAQmx Create Channel (TEDS-AI-Acceleration-Accelerometer).vi"/>
				<Item Name="DAQmx Create AI Channel TEDS(sub).vi" Type="VI" URL="/&lt;vilib&gt;/DAQmx/create/channels.llb/DAQmx Create AI Channel TEDS(sub).vi"/>
				<Item Name="DAQmx Create Channel (TEDS-AI-Current-Basic).vi" Type="VI" URL="/&lt;vilib&gt;/DAQmx/create/channels.llb/DAQmx Create Channel (TEDS-AI-Current-Basic).vi"/>
				<Item Name="DAQmx Create Channel (TEDS-AI-Position-LVDT).vi" Type="VI" URL="/&lt;vilib&gt;/DAQmx/create/channels.llb/DAQmx Create Channel (TEDS-AI-Position-LVDT).vi"/>
				<Item Name="DAQmx Create Channel (TEDS-AI-Position-RVDT).vi" Type="VI" URL="/&lt;vilib&gt;/DAQmx/create/channels.llb/DAQmx Create Channel (TEDS-AI-Position-RVDT).vi"/>
				<Item Name="DAQmx Create Channel (TEDS-AI-Resistance).vi" Type="VI" URL="/&lt;vilib&gt;/DAQmx/create/channels.llb/DAQmx Create Channel (TEDS-AI-Resistance).vi"/>
				<Item Name="DAQmx Create Channel (TEDS-AI-Strain-Strain Gage).vi" Type="VI" URL="/&lt;vilib&gt;/DAQmx/create/channels.llb/DAQmx Create Channel (TEDS-AI-Strain-Strain Gage).vi"/>
				<Item Name="DAQmx Create Channel (TEDS-AI-Temperature-RTD).vi" Type="VI" URL="/&lt;vilib&gt;/DAQmx/create/channels.llb/DAQmx Create Channel (TEDS-AI-Temperature-RTD).vi"/>
				<Item Name="DAQmx Create Channel (TEDS-AI-Temperature-Thermistor-Iex).vi" Type="VI" URL="/&lt;vilib&gt;/DAQmx/create/channels.llb/DAQmx Create Channel (TEDS-AI-Temperature-Thermistor-Iex).vi"/>
				<Item Name="DAQmx Create Channel (TEDS-AI-Temperature-Thermistor-Vex).vi" Type="VI" URL="/&lt;vilib&gt;/DAQmx/create/channels.llb/DAQmx Create Channel (TEDS-AI-Temperature-Thermistor-Vex).vi"/>
				<Item Name="DAQmx Create Channel (TEDS-AI-Voltage-Basic).vi" Type="VI" URL="/&lt;vilib&gt;/DAQmx/create/channels.llb/DAQmx Create Channel (TEDS-AI-Voltage-Basic).vi"/>
				<Item Name="DAQmx Create Channel (TEDS-AI-Voltage-Custom with Excitation).vi" Type="VI" URL="/&lt;vilib&gt;/DAQmx/create/channels.llb/DAQmx Create Channel (TEDS-AI-Voltage-Custom with Excitation).vi"/>
				<Item Name="DAQmx Create Channel (TEDS-AI-Temperature-Thermocouple).vi" Type="VI" URL="/&lt;vilib&gt;/DAQmx/create/channels.llb/DAQmx Create Channel (TEDS-AI-Temperature-Thermocouple).vi"/>
				<Item Name="DAQmx Create Channel (AI-Sound Pressure-Microphone).vi" Type="VI" URL="/&lt;vilib&gt;/DAQmx/create/channels.llb/DAQmx Create Channel (AI-Sound Pressure-Microphone).vi"/>
				<Item Name="DAQmx Create Channel (TEDS-AI-Sound Pressure-Microphone).vi" Type="VI" URL="/&lt;vilib&gt;/DAQmx/create/channels.llb/DAQmx Create Channel (TEDS-AI-Sound Pressure-Microphone).vi"/>
				<Item Name="DAQmx Create Channel (CI-GPS Timestamp).vi" Type="VI" URL="/&lt;vilib&gt;/DAQmx/create/channels.llb/DAQmx Create Channel (CI-GPS Timestamp).vi"/>
				<Item Name="DAQmx Create Channel (AO-Current-Basic).vi" Type="VI" URL="/&lt;vilib&gt;/DAQmx/create/channels.llb/DAQmx Create Channel (AO-Current-Basic).vi"/>
				<Item Name="DAQmx Create Channel (AI-Voltage-RMS).vi" Type="VI" URL="/&lt;vilib&gt;/DAQmx/create/channels.llb/DAQmx Create Channel (AI-Voltage-RMS).vi"/>
				<Item Name="DAQmx Create Channel (AI-Current-RMS).vi" Type="VI" URL="/&lt;vilib&gt;/DAQmx/create/channels.llb/DAQmx Create Channel (AI-Current-RMS).vi"/>
				<Item Name="DAQmx Create Channel (AI-Position-EddyCurrentProxProbe).vi" Type="VI" URL="/&lt;vilib&gt;/DAQmx/create/channels.llb/DAQmx Create Channel (AI-Position-EddyCurrentProxProbe).vi"/>
				<Item Name="DAQmx Create Channel (CI-Pulse Freq).vi" Type="VI" URL="/&lt;vilib&gt;/DAQmx/create/channels.llb/DAQmx Create Channel (CI-Pulse Freq).vi"/>
				<Item Name="DAQmx Create Channel (CI-Pulse Time).vi" Type="VI" URL="/&lt;vilib&gt;/DAQmx/create/channels.llb/DAQmx Create Channel (CI-Pulse Time).vi"/>
				<Item Name="DAQmx Create Channel (CI-Pulse Ticks).vi" Type="VI" URL="/&lt;vilib&gt;/DAQmx/create/channels.llb/DAQmx Create Channel (CI-Pulse Ticks).vi"/>
				<Item Name="DAQmx Create Channel (AI-Bridge).vi" Type="VI" URL="/&lt;vilib&gt;/DAQmx/create/channels.llb/DAQmx Create Channel (AI-Bridge).vi"/>
				<Item Name="DAQmx Create Channel (AI-Force-Bridge-Polynomial).vi" Type="VI" URL="/&lt;vilib&gt;/DAQmx/create/channels.llb/DAQmx Create Channel (AI-Force-Bridge-Polynomial).vi"/>
				<Item Name="DAQmx Create Channel (AI-Force-Bridge-Table).vi" Type="VI" URL="/&lt;vilib&gt;/DAQmx/create/channels.llb/DAQmx Create Channel (AI-Force-Bridge-Table).vi"/>
				<Item Name="DAQmx Create Channel (AI-Force-Bridge-Two-Point-Linear).vi" Type="VI" URL="/&lt;vilib&gt;/DAQmx/create/channels.llb/DAQmx Create Channel (AI-Force-Bridge-Two-Point-Linear).vi"/>
				<Item Name="DAQmx Create Channel (AI-Pressure-Bridge-Two-Point-Linear).vi" Type="VI" URL="/&lt;vilib&gt;/DAQmx/create/channels.llb/DAQmx Create Channel (AI-Pressure-Bridge-Two-Point-Linear).vi"/>
				<Item Name="DAQmx Create Channel (AI-Pressure-Bridge-Table).vi" Type="VI" URL="/&lt;vilib&gt;/DAQmx/create/channels.llb/DAQmx Create Channel (AI-Pressure-Bridge-Table).vi"/>
				<Item Name="DAQmx Create Channel (AI-Pressure-Bridge-Polynomial).vi" Type="VI" URL="/&lt;vilib&gt;/DAQmx/create/channels.llb/DAQmx Create Channel (AI-Pressure-Bridge-Polynomial).vi"/>
				<Item Name="DAQmx Create Channel (AI-Torque-Bridge-Two-Point-Linear).vi" Type="VI" URL="/&lt;vilib&gt;/DAQmx/create/channels.llb/DAQmx Create Channel (AI-Torque-Bridge-Two-Point-Linear).vi"/>
				<Item Name="DAQmx Create Channel (AI-Torque-Bridge-Table).vi" Type="VI" URL="/&lt;vilib&gt;/DAQmx/create/channels.llb/DAQmx Create Channel (AI-Torque-Bridge-Table).vi"/>
				<Item Name="DAQmx Create Channel (AI-Torque-Bridge-Polynomial).vi" Type="VI" URL="/&lt;vilib&gt;/DAQmx/create/channels.llb/DAQmx Create Channel (AI-Torque-Bridge-Polynomial).vi"/>
				<Item Name="DAQmx Create Channel (TEDS-AI-Force-Bridge).vi" Type="VI" URL="/&lt;vilib&gt;/DAQmx/create/channels.llb/DAQmx Create Channel (TEDS-AI-Force-Bridge).vi"/>
				<Item Name="DAQmx Create Channel (TEDS-AI-Pressure-Bridge).vi" Type="VI" URL="/&lt;vilib&gt;/DAQmx/create/channels.llb/DAQmx Create Channel (TEDS-AI-Pressure-Bridge).vi"/>
				<Item Name="DAQmx Create Channel (TEDS-AI-Torque-Bridge).vi" Type="VI" URL="/&lt;vilib&gt;/DAQmx/create/channels.llb/DAQmx Create Channel (TEDS-AI-Torque-Bridge).vi"/>
				<Item Name="DAQmx Create Channel (TEDS-AI-Force-IEPE Sensor).vi" Type="VI" URL="/&lt;vilib&gt;/DAQmx/create/channels.llb/DAQmx Create Channel (TEDS-AI-Force-IEPE Sensor).vi"/>
				<Item Name="DAQmx Create Channel (AI-Force-IEPE Sensor).vi" Type="VI" URL="/&lt;vilib&gt;/DAQmx/create/channels.llb/DAQmx Create Channel (AI-Force-IEPE Sensor).vi"/>
				<Item Name="DAQmx Create Channel (TEDS-AI-Bridge).vi" Type="VI" URL="/&lt;vilib&gt;/DAQmx/create/channels.llb/DAQmx Create Channel (TEDS-AI-Bridge).vi"/>
				<Item Name="DAQmx Create Channel (AI-Velocity-IEPE Sensor).vi" Type="VI" URL="/&lt;vilib&gt;/DAQmx/create/channels.llb/DAQmx Create Channel (AI-Velocity-IEPE Sensor).vi"/>
				<Item Name="DAQmx Create Channel (AI-Strain-Rosette Strain Gage).vi" Type="VI" URL="/&lt;vilib&gt;/DAQmx/create/channels.llb/DAQmx Create Channel (AI-Strain-Rosette Strain Gage).vi"/>
				<Item Name="DAQmx Create Strain Rosette AI Channels (sub).vi" Type="VI" URL="/&lt;vilib&gt;/DAQmx/create/channels.llb/DAQmx Create Strain Rosette AI Channels (sub).vi"/>
				<Item Name="DAQmx Timing (Handshaking).vi" Type="VI" URL="/&lt;vilib&gt;/DAQmx/configure/timing.llb/DAQmx Timing (Handshaking).vi"/>
				<Item Name="DAQmx Timing (Implicit).vi" Type="VI" URL="/&lt;vilib&gt;/DAQmx/configure/timing.llb/DAQmx Timing (Implicit).vi"/>
				<Item Name="DAQmx Timing (Use Waveform).vi" Type="VI" URL="/&lt;vilib&gt;/DAQmx/configure/timing.llb/DAQmx Timing (Use Waveform).vi"/>
				<Item Name="DAQmx Timing (Change Detection).vi" Type="VI" URL="/&lt;vilib&gt;/DAQmx/configure/timing.llb/DAQmx Timing (Change Detection).vi"/>
				<Item Name="DAQmx Timing (Burst Import Clock).vi" Type="VI" URL="/&lt;vilib&gt;/DAQmx/configure/timing.llb/DAQmx Timing (Burst Import Clock).vi"/>
				<Item Name="DAQmx Timing (Burst Export Clock).vi" Type="VI" URL="/&lt;vilib&gt;/DAQmx/configure/timing.llb/DAQmx Timing (Burst Export Clock).vi"/>
				<Item Name="DAQmx Timing (Pipelined Sample Clock).vi" Type="VI" URL="/&lt;vilib&gt;/DAQmx/configure/timing.llb/DAQmx Timing (Pipelined Sample Clock).vi"/>
				<Item Name="DAQmx Start Trigger (None).vi" Type="VI" URL="/&lt;vilib&gt;/DAQmx/configure/trigger.llb/DAQmx Start Trigger (None).vi"/>
				<Item Name="DAQmx Start Trigger (Analog Edge).vi" Type="VI" URL="/&lt;vilib&gt;/DAQmx/configure/trigger.llb/DAQmx Start Trigger (Analog Edge).vi"/>
				<Item Name="DAQmx Reference Trigger (Analog Edge).vi" Type="VI" URL="/&lt;vilib&gt;/DAQmx/configure/trigger.llb/DAQmx Reference Trigger (Analog Edge).vi"/>
				<Item Name="DAQmx Advance Trigger (Digital Edge).vi" Type="VI" URL="/&lt;vilib&gt;/DAQmx/configure/trigger.llb/DAQmx Advance Trigger (Digital Edge).vi"/>
				<Item Name="DAQmx Reference Trigger (None).vi" Type="VI" URL="/&lt;vilib&gt;/DAQmx/configure/trigger.llb/DAQmx Reference Trigger (None).vi"/>
				<Item Name="DAQmx Reference Trigger (Digital Edge).vi" Type="VI" URL="/&lt;vilib&gt;/DAQmx/configure/trigger.llb/DAQmx Reference Trigger (Digital Edge).vi"/>
				<Item Name="DAQmx Start Trigger (Analog Window).vi" Type="VI" URL="/&lt;vilib&gt;/DAQmx/configure/trigger.llb/DAQmx Start Trigger (Analog Window).vi"/>
				<Item Name="DAQmx Reference Trigger (Analog Window).vi" Type="VI" URL="/&lt;vilib&gt;/DAQmx/configure/trigger.llb/DAQmx Reference Trigger (Analog Window).vi"/>
				<Item Name="DAQmx Advance Trigger (None).vi" Type="VI" URL="/&lt;vilib&gt;/DAQmx/configure/trigger.llb/DAQmx Advance Trigger (None).vi"/>
				<Item Name="DAQmx Reference Trigger (Digital Pattern).vi" Type="VI" URL="/&lt;vilib&gt;/DAQmx/configure/trigger.llb/DAQmx Reference Trigger (Digital Pattern).vi"/>
				<Item Name="DAQmx Start Trigger (Digital Pattern).vi" Type="VI" URL="/&lt;vilib&gt;/DAQmx/configure/trigger.llb/DAQmx Start Trigger (Digital Pattern).vi"/>
				<Item Name="DAQmx Write (Analog 1D DBL 1Chan NSamp).vi" Type="VI" URL="/&lt;vilib&gt;/DAQmx/write.llb/DAQmx Write (Analog 1D DBL 1Chan NSamp).vi"/>
				<Item Name="DAQmx Write (Analog 1D DBL NChan 1Samp).vi" Type="VI" URL="/&lt;vilib&gt;/DAQmx/write.llb/DAQmx Write (Analog 1D DBL NChan 1Samp).vi"/>
				<Item Name="DAQmx Write (Analog 1D Wfm NChan 1Samp).vi" Type="VI" URL="/&lt;vilib&gt;/DAQmx/write.llb/DAQmx Write (Analog 1D Wfm NChan 1Samp).vi"/>
				<Item Name="DAQmx Write (Analog 2D DBL NChan NSamp).vi" Type="VI" URL="/&lt;vilib&gt;/DAQmx/write.llb/DAQmx Write (Analog 2D DBL NChan NSamp).vi"/>
				<Item Name="DAQmx Write (Analog DBL 1Chan 1Samp).vi" Type="VI" URL="/&lt;vilib&gt;/DAQmx/write.llb/DAQmx Write (Analog DBL 1Chan 1Samp).vi"/>
				<Item Name="DAQmx Write (Analog Wfm 1Chan 1Samp).vi" Type="VI" URL="/&lt;vilib&gt;/DAQmx/write.llb/DAQmx Write (Analog Wfm 1Chan 1Samp).vi"/>
				<Item Name="DAQmx Write (Analog Wfm 1Chan NSamp).vi" Type="VI" URL="/&lt;vilib&gt;/DAQmx/write.llb/DAQmx Write (Analog Wfm 1Chan NSamp).vi"/>
				<Item Name="DAQmx Write (Digital 2D U32 NChan NSamp).vi" Type="VI" URL="/&lt;vilib&gt;/DAQmx/write.llb/DAQmx Write (Digital 2D U32 NChan NSamp).vi"/>
				<Item Name="DAQmx Write (Digital 2D U8 NChan NSamp).vi" Type="VI" URL="/&lt;vilib&gt;/DAQmx/write.llb/DAQmx Write (Digital 2D U8 NChan NSamp).vi"/>
				<Item Name="DAQmx Write (Digital 1D Bool 1Chan 1Samp).vi" Type="VI" URL="/&lt;vilib&gt;/DAQmx/write.llb/DAQmx Write (Digital 1D Bool 1Chan 1Samp).vi"/>
				<Item Name="DAQmx Write (Digital 1D U32 1Chan NSamp).vi" Type="VI" URL="/&lt;vilib&gt;/DAQmx/write.llb/DAQmx Write (Digital 1D U32 1Chan NSamp).vi"/>
				<Item Name="DAQmx Write (Digital 1D U8 1Chan NSamp).vi" Type="VI" URL="/&lt;vilib&gt;/DAQmx/write.llb/DAQmx Write (Digital 1D U8 1Chan NSamp).vi"/>
				<Item Name="DAQmx Write (Digital Bool 1Line 1Point).vi" Type="VI" URL="/&lt;vilib&gt;/DAQmx/write.llb/DAQmx Write (Digital Bool 1Line 1Point).vi"/>
				<Item Name="DAQmx Write (Raw 1D I16).vi" Type="VI" URL="/&lt;vilib&gt;/DAQmx/write.llb/DAQmx Write (Raw 1D I16).vi"/>
				<Item Name="DAQmx Write (Raw 1D I32).vi" Type="VI" URL="/&lt;vilib&gt;/DAQmx/write.llb/DAQmx Write (Raw 1D I32).vi"/>
				<Item Name="DAQmx Write (Raw 1D I8).vi" Type="VI" URL="/&lt;vilib&gt;/DAQmx/write.llb/DAQmx Write (Raw 1D I8).vi"/>
				<Item Name="DAQmx Write (Raw 1D U16).vi" Type="VI" URL="/&lt;vilib&gt;/DAQmx/write.llb/DAQmx Write (Raw 1D U16).vi"/>
				<Item Name="DAQmx Write (Raw 1D U32).vi" Type="VI" URL="/&lt;vilib&gt;/DAQmx/write.llb/DAQmx Write (Raw 1D U32).vi"/>
				<Item Name="DAQmx Write (Raw 1D U8).vi" Type="VI" URL="/&lt;vilib&gt;/DAQmx/write.llb/DAQmx Write (Raw 1D U8).vi"/>
				<Item Name="DAQmx Write (Digital 1D Wfm NChan 1Samp).vi" Type="VI" URL="/&lt;vilib&gt;/DAQmx/write.llb/DAQmx Write (Digital 1D Wfm NChan 1Samp).vi"/>
				<Item Name="DAQmx Write (Digital Wfm 1Chan 1Samp).vi" Type="VI" URL="/&lt;vilib&gt;/DAQmx/write.llb/DAQmx Write (Digital Wfm 1Chan 1Samp).vi"/>
				<Item Name="DAQmx Write (Digital 1D Wfm NChan NSamp).vi" Type="VI" URL="/&lt;vilib&gt;/DAQmx/write.llb/DAQmx Write (Digital 1D Wfm NChan NSamp).vi"/>
				<Item Name="DAQmx Write (Digital U8 1Chan 1Samp).vi" Type="VI" URL="/&lt;vilib&gt;/DAQmx/write.llb/DAQmx Write (Digital U8 1Chan 1Samp).vi"/>
				<Item Name="DAQmx Write (Digital U32 1Chan 1Samp).vi" Type="VI" URL="/&lt;vilib&gt;/DAQmx/write.llb/DAQmx Write (Digital U32 1Chan 1Samp).vi"/>
				<Item Name="DAQmx Write (Digital 1D U32 NChan 1Samp).vi" Type="VI" URL="/&lt;vilib&gt;/DAQmx/write.llb/DAQmx Write (Digital 1D U32 NChan 1Samp).vi"/>
				<Item Name="DAQmx Write (Digital 1D U8 NChan 1Samp).vi" Type="VI" URL="/&lt;vilib&gt;/DAQmx/write.llb/DAQmx Write (Digital 1D U8 NChan 1Samp).vi"/>
				<Item Name="DAQmx Write (Digital 2D Bool NChan 1Samp NLine).vi" Type="VI" URL="/&lt;vilib&gt;/DAQmx/write.llb/DAQmx Write (Digital 2D Bool NChan 1Samp NLine).vi"/>
				<Item Name="DAQmx Write (Digital 1D Bool NChan 1Samp 1Line).vi" Type="VI" URL="/&lt;vilib&gt;/DAQmx/write.llb/DAQmx Write (Digital 1D Bool NChan 1Samp 1Line).vi"/>
				<Item Name="DAQmx Write (Analog 2D I16 NChan NSamp).vi" Type="VI" URL="/&lt;vilib&gt;/DAQmx/write.llb/DAQmx Write (Analog 2D I16 NChan NSamp).vi"/>
				<Item Name="DAQmx Write (Analog 2D U16 NChan NSamp).vi" Type="VI" URL="/&lt;vilib&gt;/DAQmx/write.llb/DAQmx Write (Analog 2D U16 NChan NSamp).vi"/>
				<Item Name="DAQmx Write (Counter Frequency 1Chan 1Samp).vi" Type="VI" URL="/&lt;vilib&gt;/DAQmx/write.llb/DAQmx Write (Counter Frequency 1Chan 1Samp).vi"/>
				<Item Name="DAQmx Write (Counter Ticks 1Chan 1Samp).vi" Type="VI" URL="/&lt;vilib&gt;/DAQmx/write.llb/DAQmx Write (Counter Ticks 1Chan 1Samp).vi"/>
				<Item Name="DAQmx Write (Counter Time 1Chan 1Samp).vi" Type="VI" URL="/&lt;vilib&gt;/DAQmx/write.llb/DAQmx Write (Counter Time 1Chan 1Samp).vi"/>
				<Item Name="DAQmx Write (Counter 1D Frequency NChan 1Samp).vi" Type="VI" URL="/&lt;vilib&gt;/DAQmx/write.llb/DAQmx Write (Counter 1D Frequency NChan 1Samp).vi"/>
				<Item Name="DAQmx Write (Counter 1D Time NChan 1Samp).vi" Type="VI" URL="/&lt;vilib&gt;/DAQmx/write.llb/DAQmx Write (Counter 1D Time NChan 1Samp).vi"/>
				<Item Name="DAQmx Write (Counter 1DTicks NChan 1Samp).vi" Type="VI" URL="/&lt;vilib&gt;/DAQmx/write.llb/DAQmx Write (Counter 1DTicks NChan 1Samp).vi"/>
				<Item Name="DAQmx Write (Analog 2D I32 NChan NSamp).vi" Type="VI" URL="/&lt;vilib&gt;/DAQmx/write.llb/DAQmx Write (Analog 2D I32 NChan NSamp).vi"/>
				<Item Name="DAQmx Write (Digital U16 1Chan 1Samp).vi" Type="VI" URL="/&lt;vilib&gt;/DAQmx/write.llb/DAQmx Write (Digital U16 1Chan 1Samp).vi"/>
				<Item Name="DAQmx Write (Digital 1D U16 1Chan NSamp).vi" Type="VI" URL="/&lt;vilib&gt;/DAQmx/write.llb/DAQmx Write (Digital 1D U16 1Chan NSamp).vi"/>
				<Item Name="DAQmx Write (Digital 1D U16 NChan 1Samp).vi" Type="VI" URL="/&lt;vilib&gt;/DAQmx/write.llb/DAQmx Write (Digital 1D U16 NChan 1Samp).vi"/>
				<Item Name="DAQmx Write (Digital 2D U16 NChan NSamp).vi" Type="VI" URL="/&lt;vilib&gt;/DAQmx/write.llb/DAQmx Write (Digital 2D U16 NChan NSamp).vi"/>
				<Item Name="DAQmx Write (Counter 1D Frequency 1Chan NSamp).vi" Type="VI" URL="/&lt;vilib&gt;/DAQmx/write.llb/DAQmx Write (Counter 1D Frequency 1Chan NSamp).vi"/>
				<Item Name="DAQmx Write (Counter 1D Ticks 1Chan NSamp).vi" Type="VI" URL="/&lt;vilib&gt;/DAQmx/write.llb/DAQmx Write (Counter 1D Ticks 1Chan NSamp).vi"/>
				<Item Name="DAQmx Write (Counter 1D Time 1Chan NSamp).vi" Type="VI" URL="/&lt;vilib&gt;/DAQmx/write.llb/DAQmx Write (Counter 1D Time 1Chan NSamp).vi"/>
				<Item Name="Uncompress Digital.vi" Type="VI" URL="/&lt;vilib&gt;/Waveform/DWDT.llb/Uncompress Digital.vi"/>
				<Item Name="VISA Configure Serial Port (Instr).vi" Type="VI" URL="/&lt;vilib&gt;/Instr/_visa.llb/VISA Configure Serial Port (Instr).vi"/>
				<Item Name="VISA Configure Serial Port (Serial Instr).vi" Type="VI" URL="/&lt;vilib&gt;/Instr/_visa.llb/VISA Configure Serial Port (Serial Instr).vi"/>
				<Item Name="VISA Configure Serial Port" Type="VI" URL="/&lt;vilib&gt;/Instr/_visa.llb/VISA Configure Serial Port"/>
				<Item Name="DAQmx Export Signal (Most Signals).vi" Type="VI" URL="/&lt;vilib&gt;/DAQmx/configure/events/hardwareSignals.llb/DAQmx Export Signal (Most Signals).vi"/>
				<Item Name="DAQmx Export Signal.vi" Type="VI" URL="/&lt;vilib&gt;/DAQmx/configure/events/hardwareSignals.llb/DAQmx Export Signal.vi"/>
				<Item Name="DAQmx Control Task.vi" Type="VI" URL="/&lt;vilib&gt;/DAQmx/configure/task.llb/DAQmx Control Task.vi"/>
			</Item>
			<Item Name="AD9910 Register Info.vi" Type="VI" URL="../../DDS drivers v3/AD9910 Register Info.vi"/>
			<Item Name="AD9910 registers.ctl" Type="VI" URL="../../DDS drivers v3/AD9910 registers.ctl"/>
			<Item Name="DDS Channel to CS Pin.vi" Type="VI" URL="../../DDS drivers v3/DDS Channel to CS Pin.vi"/>
			<Item Name="DDS Channel to IO Update Pin.vi" Type="VI" URL="../../DDS drivers v3/DDS Channel to IO Update Pin.vi"/>
			<Item Name="DDS Channel to Master Reset Pin.vi" Type="VI" URL="../../DDS drivers v3/DDS Channel to Master Reset Pin.vi"/>
			<Item Name="DDS Com Check.vi" Type="VI" URL="../../DDS drivers v3/DDS Com Check.vi"/>
			<Item Name="DDS CS pins.ctl" Type="VI" URL="../../DDS drivers v3/DDS CS pins.ctl"/>
			<Item Name="DDS DIO pins.ctl" Type="VI" URL="../../DDS drivers v3/DDS DIO pins.ctl"/>
			<Item Name="DDS Initialize.vi" Type="VI" URL="../../DDS drivers v3/DDS Initialize.vi"/>
			<Item Name="DDS Power Down.vi" Type="VI" URL="../../DDS drivers v3/DDS Power Down.vi"/>
			<Item Name="DDS Pulse IO Reset.vi" Type="VI" URL="../../DDS drivers v3/DDS Pulse IO Reset.vi"/>
			<Item Name="DDS Pulse IO Update.vi" Type="VI" URL="../../DDS drivers v3/DDS Pulse IO Update.vi"/>
			<Item Name="DDS Pulse Master Reset.vi" Type="VI" URL="../../DDS drivers v3/DDS Pulse Master Reset.vi"/>
			<Item Name="DDS RAM Enable.vi" Type="VI" URL="../../DDS drivers v3/DDS RAM Enable.vi"/>
			<Item Name="DDS RAM mode.ctl" Type="VI" URL="../../DDS drivers v3/DDS RAM mode.ctl"/>
			<Item Name="DDS RAM Programmer.vi" Type="VI" URL="../../DDS drivers v3/DDS RAM Programmer.vi"/>
			<Item Name="DDS RAM Set.vi" Type="VI" URL="../../DDS drivers v3/DDS RAM Set.vi"/>
			<Item Name="DDS Re-initialize One Channel.vi" Type="VI" URL="../../DDS drivers v3/DDS Re-initialize One Channel.vi"/>
			<Item Name="DDS Read Register.vi" Type="VI" URL="../../DDS drivers v3/DDS Read Register.vi"/>
			<Item Name="DDS Set RAM Profile.vi" Type="VI" URL="../../DDS drivers v3/DDS Set RAM Profile.vi"/>
			<Item Name="DDS Set Single-Tone Profile.vi" Type="VI" URL="../../DDS drivers v3/DDS Set Single-Tone Profile.vi"/>
			<Item Name="DDS Wake Up.vi" Type="VI" URL="../../DDS drivers v3/DDS Wake Up.vi"/>
			<Item Name="DDS Write RAM register 2.vi" Type="VI" URL="../../DDS drivers v3/DDS Write RAM register 2.vi"/>
			<Item Name="DDS Write Register.vi" Type="VI" URL="../../DDS drivers v3/DDS Write Register.vi"/>
			<Item Name="imaq.dll" Type="Document" URL="imaq.dll">
				<Property Name="NI.PreserveRelativePath" Type="Bool">true</Property>
			</Item>
			<Item Name="ni845x.dll" Type="Document" URL="ni845x.dll">
				<Property Name="NI.PreserveRelativePath" Type="Bool">true</Property>
			</Item>
			<Item Name="nivissvc.dll" Type="Document" URL="nivissvc.dll">
				<Property Name="NI.PreserveRelativePath" Type="Bool">true</Property>
			</Item>
			<Item Name="Pulse CS Line Script.vi" Type="VI" URL="../../DDS drivers v3/Pulse CS Line Script.vi"/>
			<Item Name="Pulse DIO Line Script.vi" Type="VI" URL="../../DDS drivers v3/Pulse DIO Line Script.vi"/>
			<Item Name="Read Write Script 2.vi" Type="VI" URL="../../DDS drivers v3/Read Write Script 2.vi"/>
			<Item Name="Read Write Script.vi" Type="VI" URL="../../DDS drivers v3/Read Write Script.vi"/>
			<Item Name="DDS Read RAM register.vi" Type="VI" URL="../../DDS drivers v3/DDS Read RAM register.vi"/>
			<Item Name="Read Write Script 3.vi" Type="VI" URL="../../DDS drivers v3/Read Write Script 3.vi"/>
			<Item Name="counter_graph_refnums.ctl" Type="VI" URL="../Counter/counter_graph_refnums.ctl"/>
			<Item Name="lvanlys.dll" Type="Document" URL="/&lt;resource&gt;/lvanlys.dll"/>
			<Item Name="Array_of_DDS_Boxes.ctl" Type="VI" URL="../../DDS drivers v3/Array_of_DDS_Boxes.ctl"/>
			<Item Name="DDS_box_cluster.ctl" Type="VI" URL="../../DDS drivers v3/DDS_box_cluster.ctl"/>
			<Item Name="DDS_box_device_reference.ctl" Type="VI" URL="../../DDS drivers v3/DDS_box_device_reference.ctl"/>
			<Item Name="DOMUserDefRef.dll" Type="Document" URL="DOMUserDefRef.dll">
				<Property Name="NI.PreserveRelativePath" Type="Bool">true</Property>
			</Item>
			<Item Name="GCSTranslateError.vi" Type="VI" URL="../PI_piezo/GCS_LabVIEW_digital/Low Level/Support.llb/GCSTranslateError.vi"/>
			<Item Name="ERR?.vi" Type="VI" URL="../PI_piezo/GCS_LabVIEW_digital/Low Level/General command.llb/ERR?.vi"/>
			<Item Name="SVA.vi" Type="VI" URL="../PI_piezo/GCS_LabVIEW_digital/Low Level/PZT voltage.llb/SVA.vi"/>
			<Item Name="ONT?.vi" Type="VI" URL="../PI_piezo/GCS_LabVIEW_digital/Low Level/General command.llb/ONT?.vi"/>
			<Item Name="MOV.vi" Type="VI" URL="../PI_piezo/GCS_LabVIEW_digital/Low Level/General command.llb/MOV.vi"/>
			<Item Name="Split multiple axes command.vi" Type="VI" URL="../PI_piezo/GCS_LabVIEW_digital/Low Level/Support.llb/Split multiple axes command.vi"/>
			<Item Name="Define connected axes.vi" Type="VI" URL="../PI_piezo/GCS_LabVIEW_digital/Low Level/General command.llb/Define connected axes.vi"/>
			<Item Name="*IDN?.vi" Type="VI" URL="../PI_piezo/GCS_LabVIEW_digital/Low Level/General command.llb/*IDN?.vi"/>
			<Item Name="GCSTranslator.dll" Type="Document" URL="../PI_piezo/GCS_LabVIEW_digital/Low Level/GCSTranslator.dll"/>
			<Item Name="Cut out additional spaces.vi" Type="VI" URL="../PI_piezo/GCS_LabVIEW_digital/Low Level/Support.llb/Cut out additional spaces.vi"/>
			<Item Name="Controller names.ctl" Type="VI" URL="../PI_piezo/GCS_LabVIEW_digital/Low Level/General command.llb/Controller names.ctl"/>
			<Item Name="Global2 (Array).vi" Type="VI" URL="../PI_piezo/GCS_LabVIEW_digital/Low Level/General command.llb/Global2 (Array).vi"/>
			<Item Name="Get all axes.vi" Type="VI" URL="../PI_piezo/GCS_LabVIEW_digital/Low Level/Support.llb/Get all axes.vi"/>
			<Item Name="Assign booleans from string to axes.vi" Type="VI" URL="../PI_piezo/GCS_LabVIEW_digital/Low Level/Support.llb/Assign booleans from string to axes.vi"/>
			<Item Name="Termination character.ctl" Type="VI" URL="../PI_piezo/GCS_LabVIEW_digital/Low Level/Communication.llb/Termination character.ctl"/>
			<Item Name="Available interfaces.ctl" Type="VI" URL="../PI_piezo/GCS_LabVIEW_digital/Low Level/Communication.llb/Available interfaces.ctl"/>
			<Item Name="Available DLL interfaces.ctl" Type="VI" URL="../PI_piezo/GCS_LabVIEW_digital/Low Level/Communication.llb/Available DLL interfaces.ctl"/>
			<Item Name="Available DLLs.ctl" Type="VI" URL="../PI_piezo/GCS_LabVIEW_digital/Low Level/Communication.llb/Available DLLs.ctl"/>
			<Item Name="Global1.vi" Type="VI" URL="../PI_piezo/GCS_LabVIEW_digital/Low Level/Communication.llb/Global1.vi"/>
			<Item Name="Return space.vi" Type="VI" URL="../PI_piezo/GCS_LabVIEW_digital/Low Level/Support.llb/Return space.vi"/>
			<Item Name="Build query command substring.vi" Type="VI" URL="../PI_piezo/GCS_LabVIEW_digital/Low Level/Support.llb/Build query command substring.vi"/>
			<Item Name="Get arrays without blanks.vi" Type="VI" URL="../PI_piezo/GCS_LabVIEW_digital/Low Level/Support.llb/Get arrays without blanks.vi"/>
			<Item Name="Commanded axes connected?.vi" Type="VI" URL="../PI_piezo/GCS_LabVIEW_digital/Low Level/Support.llb/Commanded axes connected?.vi"/>
			<Item Name="String with ASCII code conversion.vi" Type="VI" URL="../PI_piezo/GCS_LabVIEW_digital/Low Level/Support.llb/String with ASCII code conversion.vi"/>
			<Item Name="Analog Receive String.vi" Type="VI" URL="../PI_piezo/GCS_LabVIEW_digital/Low Level/Analog control.llb/Analog Receive String.vi"/>
			<Item Name="Get lines from string.vi" Type="VI" URL="../PI_piezo/GCS_LabVIEW_digital/Low Level/Support.llb/Get lines from string.vi"/>
			<Item Name="Global DaisyChain.vi" Type="VI" URL="../PI_piezo/GCS_LabVIEW_digital/Low Level/Communication.llb/Global DaisyChain.vi"/>
			<Item Name="GCSTranslator DLL Functions.vi" Type="VI" URL="../PI_piezo/GCS_LabVIEW_digital/Low Level/Communication.llb/GCSTranslator DLL Functions.vi"/>
			<Item Name="PI VISA Receive Characters.vi" Type="VI" URL="../PI_piezo/GCS_LabVIEW_digital/Low Level/Communication.llb/PI VISA Receive Characters.vi"/>
			<Item Name="PI Receive String.vi" Type="VI" URL="../PI_piezo/GCS_LabVIEW_digital/Low Level/Communication.llb/PI Receive String.vi"/>
			<Item Name="Available Analog Commands.ctl" Type="VI" URL="../PI_piezo/GCS_LabVIEW_digital/Low Level/Analog control.llb/Available Analog Commands.ctl"/>
			<Item Name="Analog Functions.vi" Type="VI" URL="../PI_piezo/GCS_LabVIEW_digital/Low Level/Analog control.llb/Analog Functions.vi"/>
			<Item Name="PI Send String.vi" Type="VI" URL="../PI_piezo/GCS_LabVIEW_digital/Low Level/Communication.llb/PI Send String.vi"/>
			<Item Name="Build command substring.vi" Type="VI" URL="../PI_piezo/GCS_LabVIEW_digital/Low Level/Support.llb/Build command substring.vi"/>
			<Item Name="Global Analog.vi" Type="VI" URL="../PI_piezo/GCS_LabVIEW_digital/Low Level/Analog control.llb/Global Analog.vi"/>
			<Item Name="#5.vi" Type="VI" URL="../PI_piezo/GCS_LabVIEW_digital/Low Level/Special command.llb/#5.vi"/>
			<Item Name="#5_old.vi" Type="VI" URL="../PI_piezo/GCS_LabVIEW_digital/Low Level/Old commands.llb/#5_old.vi"/>
			<Item Name="Wait for hexapod system axes to stop.vi" Type="VI" URL="../PI_piezo/GCS_LabVIEW_digital/Low Level/Old commands.llb/Wait for hexapod system axes to stop.vi"/>
			<Item Name="Assign values from string to axes.vi" Type="VI" URL="../PI_piezo/GCS_LabVIEW_digital/Low Level/Support.llb/Assign values from string to axes.vi"/>
			<Item Name="STA?.vi" Type="VI" URL="../PI_piezo/GCS_LabVIEW_digital/Low Level/Special command.llb/STA?.vi"/>
			<Item Name="Wait for axes to stop.vi" Type="VI" URL="../PI_piezo/GCS_LabVIEW_digital/Low Level/Support.llb/Wait for axes to stop.vi"/>
			<Item Name="General wait for movement to stop.vi" Type="VI" URL="../PI_piezo/GCS_LabVIEW_digital/Low Level/Support.llb/General wait for movement to stop.vi"/>
			<Item Name="TSC?.vi" Type="VI" URL="../PI_piezo/GCS_LabVIEW_digital/Low Level/Optical or Analog Input.llb/TSC?.vi"/>
			<Item Name="TPC?.vi" Type="VI" URL="../PI_piezo/GCS_LabVIEW_digital/Low Level/Special command.llb/TPC?.vi"/>
			<Item Name="Build channel query command substring.vi" Type="VI" URL="../PI_piezo/GCS_LabVIEW_digital/Low Level/Support.llb/Build channel query command substring.vi"/>
			<Item Name="VOL?.vi" Type="VI" URL="../PI_piezo/GCS_LabVIEW_digital/Low Level/PZT voltage.llb/VOL?.vi"/>
			<Item Name="SVR.vi" Type="VI" URL="../PI_piezo/GCS_LabVIEW_digital/Low Level/PZT voltage.llb/SVR.vi"/>
			<Item Name="SVO?.vi" Type="VI" URL="../PI_piezo/GCS_LabVIEW_digital/Low Level/General command.llb/SVO?.vi"/>
			<Item Name="SVO.vi" Type="VI" URL="../PI_piezo/GCS_LabVIEW_digital/Low Level/General command.llb/SVO.vi"/>
			<Item Name="SVA?.vi" Type="VI" URL="../PI_piezo/GCS_LabVIEW_digital/Low Level/PZT voltage.llb/SVA?.vi"/>
			<Item Name="RST.vi" Type="VI" URL="../PI_piezo/GCS_LabVIEW_digital/Low Level/Special command.llb/RST.vi"/>
			<Item Name="POS?.vi" Type="VI" URL="../PI_piezo/GCS_LabVIEW_digital/Low Level/General command.llb/POS?.vi"/>
			<Item Name="OVF?.vi" Type="VI" URL="../PI_piezo/GCS_LabVIEW_digital/Low Level/PZT voltage.llb/OVF?.vi"/>
			<Item Name="MVR.vi" Type="VI" URL="../PI_piezo/GCS_LabVIEW_digital/Low Level/General command.llb/MVR.vi"/>
			<Item Name="MOV?.vi" Type="VI" URL="../PI_piezo/GCS_LabVIEW_digital/Low Level/General command.llb/MOV?.vi"/>
			<Item Name="DCO?.vi" Type="VI" URL="../PI_piezo/GCS_LabVIEW_digital/Low Level/PZT voltage.llb/DCO?.vi"/>
			<Item Name="DCO.vi" Type="VI" URL="../PI_piezo/GCS_LabVIEW_digital/Low Level/PZT voltage.llb/DCO.vi"/>
			<Item Name="Initialize Global2.vi" Type="VI" URL="../PI_piezo/GCS_LabVIEW_digital/Low Level/General command.llb/Initialize Global2.vi"/>
			<Item Name="SAI?.vi" Type="VI" URL="../PI_piezo/GCS_LabVIEW_digital/Low Level/General command.llb/SAI?.vi"/>
			<Item Name="CmdLib.dll" Type="Document" URL="../PicoMotor/NewFocus8742/CmdLib.dll"/>
			<Item Name="Arroyo TEC OUTPUT?.vi" Type="VI" URL="../Arroyo/Arroyo.llb/Arroyo TEC OUTPUT?.vi"/>
			<Item Name="Arroyo TEC SET T?.vi" Type="VI" URL="../Arroyo/Arroyo.llb/Arroyo TEC SET T?.vi"/>
			<Item Name="Arroyo TEC ITE?.vi" Type="VI" URL="../Arroyo/Arroyo.llb/Arroyo TEC ITE?.vi"/>
			<Item Name="Arroyo TEC V?.vi" Type="VI" URL="../Arroyo/Arroyo.llb/Arroyo TEC V?.vi"/>
			<Item Name="Arroyo TEC T.vi" Type="VI" URL="../Arroyo/Arroyo.llb/Arroyo TEC T.vi"/>
			<Item Name="Arroyo TEC OUTPUT.vi" Type="VI" URL="../Arroyo/Arroyo.llb/Arroyo TEC OUTPUT.vi"/>
			<Item Name="Arroyo Initialize.vi" Type="VI" URL="../Arroyo/Arroyo.llb/Arroyo Initialize.vi"/>
			<Item Name="Arroyo Command.vi" Type="VI" URL="../Arroyo/Arroyo.llb/Arroyo Command.vi"/>
			<Item Name="Arroyo Flush.vi" Type="VI" URL="../Arroyo/Arroyo.llb/Arroyo Flush.vi"/>
			<Item Name="Arroyo ERR?.vi" Type="VI" URL="../Arroyo/Arroyo.llb/Arroyo ERR?.vi"/>
			<Item Name="Arroyo Query.vi" Type="VI" URL="../Arroyo/Arroyo.llb/Arroyo Query.vi"/>
			<Item Name="Arroyo TEC T?.vi" Type="VI" URL="../Arroyo/Arroyo.llb/Arroyo TEC T?.vi"/>
			<Item Name="AbortMotion.vi" Type="VI" URL="../PicoMotor/NewFocus8742/Command VIs/AbortMotion.vi"/>
			<Item Name="Shutdown.vi" Type="VI" URL="../PicoMotor/NewFocus8742/Device VIs/Shutdown.vi"/>
			<Item Name="InitSingleDevice.vi" Type="VI" URL="../PicoMotor/NewFocus8742/Device VIs/InitSingleDevice.vi"/>
			<Item Name="SetZeroPosition.vi" Type="VI" URL="../PicoMotor/NewFocus8742/Command VIs/SetZeroPosition.vi"/>
			<Item Name="SetMotorType.vi" Type="VI" URL="../PicoMotor/NewFocus8742/Command VIs/SetMotorType.vi"/>
			<Item Name="SetVelocity.vi" Type="VI" URL="../PicoMotor/NewFocus8742/Command VIs/SetVelocity.vi"/>
			<Item Name="SetAcceleration.vi" Type="VI" URL="../PicoMotor/NewFocus8742/Command VIs/SetAcceleration.vi"/>
			<Item Name="AbsoluteMove.vi" Type="VI" URL="../PicoMotor/NewFocus8742/Command VIs/AbsoluteMove.vi"/>
			<Item Name="GetMotionDone.vi" Type="VI" URL="../PicoMotor/NewFocus8742/Command VIs/GetMotionDone.vi"/>
			<Item Name="GetPosition.vi" Type="VI" URL="../PicoMotor/NewFocus8742/Command VIs/GetPosition.vi"/>
			<Item Name="Close connection if open.vi" Type="VI" URL="../PI_piezo/GCS_LabVIEW_digital/Low Level/Communication.llb/Close connection if open.vi"/>
			<Item Name="Analog FGlobal.vi" Type="VI" URL="../PI_piezo/GCS_LabVIEW_digital/Low Level/Analog control.llb/Analog FGlobal.vi"/>
			<Item Name="Hamamatsu_serial.vi" Type="VI" URL="../Camera/Hamamatsu_C9100-13/Hamamatsu_serial.vi"/>
			<Item Name="DDS_profile.ctl" Type="VI" URL="../../DDS drivers v3/DDS_profile.ctl"/>
			<Item Name="DDS_Close_Multiple_Boxes.vi" Type="VI" URL="../../DDS drivers v3/DDS_Close_Multiple_Boxes.vi"/>
			<Item Name="DDS Close.vi" Type="VI" URL="../../DDS drivers v3/DDS Close.vi"/>
			<Item Name="HP836xxA Initialize.vi" Type="VI" URL="../hp836xxa/HP836XXA.LLB/HP836xxA Initialize.vi"/>
			<Item Name="HP836xxA Reset.vi" Type="VI" URL="../hp836xxa/HP836XXA.LLB/HP836xxA Reset.vi"/>
			<Item Name="HP836xxA Configure Frequency.vi" Type="VI" URL="../hp836xxa/HP836XXA.LLB/HP836xxA Configure Frequency.vi"/>
			<Item Name="HP836xxA Configure RF Output Power.vi" Type="VI" URL="../hp836xxa/HP836XXA.LLB/HP836xxA Configure RF Output Power.vi"/>
			<Item Name="HP836xxA Configure Pulse Modulation.vi" Type="VI" URL="../hp836xxa/HP836XXA.LLB/HP836xxA Configure Pulse Modulation.vi"/>
			<Item Name="HP836xxA Close.vi" Type="VI" URL="../hp836xxa/HP836XXA.LLB/HP836xxA Close.vi"/>
			<Item Name="nilvaiu.dll" Type="Document" URL="nilvaiu.dll">
				<Property Name="NI.PreserveRelativePath" Type="Bool">true</Property>
			</Item>
			<Item Name="Define connected systems (Array).vi" Type="VI" URL="../PI_piezo/GCS_LabVIEW_digital/Low Level/General command.llb/Define connected systems (Array).vi"/>
			<Item Name="Select USB device.vi" Type="VI" URL="../PI_piezo/GCS_LabVIEW_digital/Low Level/Communication.llb/Select USB device.vi"/>
			<Item Name="Is DaisyChain open.vi" Type="VI" URL="../PI_piezo/GCS_LabVIEW_digital/Low Level/Communication.llb/Is DaisyChain open.vi"/>
			<Item Name="Initialize Global1.vi" Type="VI" URL="../PI_piezo/GCS_LabVIEW_digital/Low Level/Communication.llb/Initialize Global1.vi"/>
			<Item Name="PI Open Interface of one system.vi" Type="VI" URL="../PI_piezo/GCS_LabVIEW_digital/Low Level/Communication.llb/PI Open Interface of one system.vi"/>
			<Item Name="E816_Configuration_Setup.vi" Type="VI" URL="../PI_piezo/GCS_LabVIEW_digital/E816_Configuration_Setup.vi"/>
			<Item Name="continue.vi" Type="VI" URL="../Experiment/continue.vi"/>
			<Item Name="Variable_Settings.ctl" Type="VI" URL="../ExperimentVariables/Variable_Settings.ctl"/>
			<Item Name="niHSDIO_64.dll" Type="Document" URL="niHSDIO_64.dll">
				<Property Name="NI.PreserveRelativePath" Type="Bool">true</Property>
			</Item>
			<Item Name="XDNodeRunTimeDep.lvlib" Type="Library" URL="/&lt;vilib&gt;/Platform/TimedLoop/XDataNode/XDNodeRunTimeDep.lvlib"/>
		</Item>
		<Item Name="Build Specifications" Type="Build">
			<Item Name="cs_server" Type="EXE">
				<Property Name="App_copyErrors" Type="Bool">true</Property>
				<Property Name="App_INI_aliasGUID" Type="Str">{039CA54C-D176-44A4-BA93-97C7B9EDFAE5}</Property>
				<Property Name="App_INI_GUID" Type="Str">{2E76339E-5A9D-4A2B-A83A-6E934115593D}</Property>
				<Property Name="App_serverConfig.httpPort" Type="Int">8002</Property>
				<Property Name="Bld_autoIncrement" Type="Bool">true</Property>
				<Property Name="Bld_buildCacheID" Type="Str">{53166DA7-B114-42C4-8A00-8ABA1D0039A0}</Property>
				<Property Name="Bld_buildSpecName" Type="Str">cs_server</Property>
				<Property Name="Bld_excludeInlineSubVIs" Type="Bool">true</Property>
				<Property Name="Bld_excludeLibraryItems" Type="Bool">true</Property>
				<Property Name="Bld_excludePolymorphicVIs" Type="Bool">true</Property>
				<Property Name="Bld_localDestDir" Type="Path">..</Property>
				<Property Name="Bld_localDestDirType" Type="Str">relativeToCommon</Property>
				<Property Name="Bld_modifyLibraryFile" Type="Bool">true</Property>
				<Property Name="Bld_previewCacheID" Type="Str">{574B9F9D-241F-4A68-8892-A5E401941744}</Property>
				<Property Name="Bld_version.build" Type="Int">10</Property>
				<Property Name="Bld_version.major" Type="Int">1</Property>
				<Property Name="Destination[0].destName" Type="Str">cs_server.exe</Property>
				<Property Name="Destination[0].path" Type="Path">../cs_server.exe</Property>
				<Property Name="Destination[0].preserveHierarchy" Type="Bool">true</Property>
				<Property Name="Destination[0].type" Type="Str">App</Property>
				<Property Name="Destination[1].destName" Type="Str">Support Directory</Property>
				<Property Name="Destination[1].path" Type="Path">../app_support</Property>
				<Property Name="DestinationCount" Type="Int">2</Property>
				<Property Name="Source[0].itemID" Type="Str">{ED724E4D-CA6D-4348-AF3B-4CEB12F101A8}</Property>
				<Property Name="Source[0].type" Type="Str">Container</Property>
				<Property Name="Source[1].destinationIndex" Type="Int">0</Property>
				<Property Name="Source[1].itemID" Type="Ref">/My Computer/Experiment.lvclass/server.vi</Property>
				<Property Name="Source[1].sourceInclusion" Type="Str">TopLevel</Property>
				<Property Name="Source[1].type" Type="Str">VI</Property>
				<Property Name="SourceCount" Type="Int">2</Property>
				<Property Name="TgtF_enableDebugging" Type="Bool">true</Property>
				<Property Name="TgtF_fileDescription" Type="Str">cs_server</Property>
				<Property Name="TgtF_internalName" Type="Str">cs_server</Property>
				<Property Name="TgtF_legalCopyright" Type="Str">Copyright © 2014 </Property>
				<Property Name="TgtF_productName" Type="Str">cs_server</Property>
				<Property Name="TgtF_targetfileGUID" Type="Str">{2D7F779A-32BB-42BE-B579-CEB9E3237BAD}</Property>
				<Property Name="TgtF_targetfileName" Type="Str">cs_server.exe</Property>
			</Item>
		</Item>
	</Item>
</Project>
