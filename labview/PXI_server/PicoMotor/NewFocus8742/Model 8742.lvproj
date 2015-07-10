<?xml version='1.0' encoding='UTF-8'?>
<Project Type="Project" LVVersion="13008000">
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
		<Item Name="Command VIs" Type="Folder">
			<Item Name="GetIdentification.vi" Type="VI" URL="../Command VIs/GetIdentification.vi"/>
			<Item Name="GetErrorMsg.vi" Type="VI" URL="../Command VIs/GetErrorMsg.vi"/>
			<Item Name="GetErrorNum.vi" Type="VI" URL="../Command VIs/GetErrorNum.vi"/>
			<Item Name="GetHostName.vi" Type="VI" URL="../Command VIs/GetHostName.vi"/>
			<Item Name="GetMotorType.vi" Type="VI" URL="../Command VIs/GetMotorType.vi"/>
			<Item Name="SetHostName.vi" Type="VI" URL="../Command VIs/SetHostName.vi"/>
			<Item Name="SetMotorType.vi" Type="VI" URL="../Command VIs/SetMotorType.vi"/>
			<Item Name="GetPosition.vi" Type="VI" URL="../Command VIs/GetPosition.vi"/>
			<Item Name="GetRelativeSteps.vi" Type="VI" URL="../Command VIs/GetRelativeSteps.vi"/>
			<Item Name="GetAbsTargetPos.vi" Type="VI" URL="../Command VIs/GetAbsTargetPos.vi"/>
			<Item Name="GetVelocity.vi" Type="VI" URL="../Command VIs/GetVelocity.vi"/>
			<Item Name="GetAcceleration.vi" Type="VI" URL="../Command VIs/GetAcceleration.vi"/>
			<Item Name="RelativeMove.vi" Type="VI" URL="../Command VIs/RelativeMove.vi"/>
			<Item Name="AbsoluteMove.vi" Type="VI" URL="../Command VIs/AbsoluteMove.vi"/>
			<Item Name="SetVelocity.vi" Type="VI" URL="../Command VIs/SetVelocity.vi"/>
			<Item Name="SetAcceleration.vi" Type="VI" URL="../Command VIs/SetAcceleration.vi"/>
			<Item Name="JogNegative.vi" Type="VI" URL="../Command VIs/JogNegative.vi"/>
			<Item Name="JogPositive.vi" Type="VI" URL="../Command VIs/JogPositive.vi"/>
			<Item Name="StopMotion.vi" Type="VI" URL="../Command VIs/StopMotion.vi"/>
			<Item Name="SetZeroPosition.vi" Type="VI" URL="../Command VIs/SetZeroPosition.vi"/>
			<Item Name="AbortMotion.vi" Type="VI" URL="../Command VIs/AbortMotion.vi"/>
			<Item Name="SaveToMemory.vi" Type="VI" URL="../Command VIs/SaveToMemory.vi"/>
			<Item Name="GetMotionDone.vi" Type="VI" URL="../Command VIs/GetMotionDone.vi"/>
		</Item>
		<Item Name="Device VIs" Type="Folder">
			<Item Name="DeviceClose.vi" Type="VI" URL="../Device VIs/DeviceClose.vi"/>
			<Item Name="DeviceOpen.vi" Type="VI" URL="../Device VIs/DeviceOpen.vi"/>
			<Item Name="InitMultipleDevices.vi" Type="VI" URL="../Device VIs/InitMultipleDevices.vi"/>
			<Item Name="InitSingleDevice.vi" Type="VI" URL="../Device VIs/InitSingleDevice.vi"/>
			<Item Name="Shutdown.vi" Type="VI" URL="../Device VIs/Shutdown.vi"/>
			<Item Name="DeviceQuery.vi" Type="VI" URL="../Device VIs/DeviceQuery.vi"/>
			<Item Name="DeviceRead.vi" Type="VI" URL="../Device VIs/DeviceRead.vi"/>
			<Item Name="DeviceWrite.vi" Type="VI" URL="../Device VIs/DeviceWrite.vi"/>
			<Item Name="LogFileWrite.vi" Type="VI" URL="../Device VIs/LogFileWrite.vi"/>
		</Item>
		<Item Name="SampleGetIDMultiple.vi" Type="VI" URL="../SampleGetIDMultiple.vi"/>
		<Item Name="SampleGetIDSingle.vi" Type="VI" URL="../SampleGetIDSingle.vi"/>
		<Item Name="SampleRelativeMove.vi" Type="VI" URL="../SampleRelativeMove.vi"/>
		<Item Name="Dependencies" Type="Dependencies">
			<Item Name="CmdLib.dll" Type="Document" URL="../CmdLib.dll"/>
		</Item>
		<Item Name="Build Specifications" Type="Build"/>
	</Item>
</Project>
