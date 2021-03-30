<?xml version='1.0' encoding='UTF-8'?>
<Project Type="Project" LVVersion="15008000">
	<Item Name="My Computer" Type="My Computer">
		<Property Name="server.app.propertiesEnabled" Type="Bool">true</Property>
		<Property Name="server.control.propertiesEnabled" Type="Bool">true</Property>
		<Property Name="server.tcp.enabled" Type="Bool">false</Property>
		<Property Name="server.tcp.port" Type="Int">0</Property>
		<Property Name="server.tcp.serviceName" Type="Str">My Computer/VI Server</Property>
		<Property Name="server.tcp.serviceName.default" Type="Str">My Computer/VI Server</Property>
		<Property Name="server.vi.callsEnabled" Type="Bool">true</Property>
		<Property Name="server.vi.propertiesEnabled" Type="Bool">true</Property>
		<Property Name="specify.custom.address" Type="Bool">false</Property>
		<Item Name="Experiment.lvclass" Type="LVClass" URL="../Experiment.lvclass"/>
		<Item Name="Dependencies" Type="Dependencies">
			<Item Name="vi.lib" Type="Folder">
				<Item Name="BuildHelpPath.vi" Type="VI" URL="/&lt;vilib&gt;/Utility/error.llb/BuildHelpPath.vi"/>
				<Item Name="Check Special Tags.vi" Type="VI" URL="/&lt;vilib&gt;/Utility/error.llb/Check Special Tags.vi"/>
				<Item Name="Clear Errors.vi" Type="VI" URL="/&lt;vilib&gt;/Utility/error.llb/Clear Errors.vi"/>
				<Item Name="Convert property node font to graphics font.vi" Type="VI" URL="/&lt;vilib&gt;/Utility/error.llb/Convert property node font to graphics font.vi"/>
				<Item Name="Details Display Dialog.vi" Type="VI" URL="/&lt;vilib&gt;/Utility/error.llb/Details Display Dialog.vi"/>
				<Item Name="DialogType.ctl" Type="VI" URL="/&lt;vilib&gt;/Utility/error.llb/DialogType.ctl"/>
				<Item Name="DialogTypeEnum.ctl" Type="VI" URL="/&lt;vilib&gt;/Utility/error.llb/DialogTypeEnum.ctl"/>
				<Item Name="Error Cluster From Error Code.vi" Type="VI" URL="/&lt;vilib&gt;/Utility/error.llb/Error Cluster From Error Code.vi"/>
				<Item Name="Error Code Database.vi" Type="VI" URL="/&lt;vilib&gt;/Utility/error.llb/Error Code Database.vi"/>
				<Item Name="Error to Warning.vi" Type="VI" URL="/&lt;vilib&gt;/Utility/error.llb/Error to Warning.vi"/>
				<Item Name="ErrWarn.ctl" Type="VI" URL="/&lt;vilib&gt;/Utility/error.llb/ErrWarn.ctl"/>
				<Item Name="eventvkey.ctl" Type="VI" URL="/&lt;vilib&gt;/event_ctls.llb/eventvkey.ctl"/>
				<Item Name="ex_CorrectErrorChain.vi" Type="VI" URL="/&lt;vilib&gt;/express/express shared/ex_CorrectErrorChain.vi"/>
				<Item Name="Find Tag.vi" Type="VI" URL="/&lt;vilib&gt;/Utility/error.llb/Find Tag.vi"/>
				<Item Name="Format Message String.vi" Type="VI" URL="/&lt;vilib&gt;/Utility/error.llb/Format Message String.vi"/>
				<Item Name="General Error Handler Core CORE.vi" Type="VI" URL="/&lt;vilib&gt;/Utility/error.llb/General Error Handler Core CORE.vi"/>
				<Item Name="General Error Handler.vi" Type="VI" URL="/&lt;vilib&gt;/Utility/error.llb/General Error Handler.vi"/>
				<Item Name="Get String Text Bounds.vi" Type="VI" URL="/&lt;vilib&gt;/Utility/error.llb/Get String Text Bounds.vi"/>
				<Item Name="Get Text Rect.vi" Type="VI" URL="/&lt;vilib&gt;/picture/picture.llb/Get Text Rect.vi"/>
				<Item Name="GetHelpDir.vi" Type="VI" URL="/&lt;vilib&gt;/Utility/error.llb/GetHelpDir.vi"/>
				<Item Name="GetRTHostConnectedProp.vi" Type="VI" URL="/&lt;vilib&gt;/Utility/error.llb/GetRTHostConnectedProp.vi"/>
				<Item Name="Internecine Avoider.vi" Type="VI" URL="/&lt;vilib&gt;/Utility/tcp.llb/Internecine Avoider.vi"/>
				<Item Name="Longest Line Length in Pixels.vi" Type="VI" URL="/&lt;vilib&gt;/Utility/error.llb/Longest Line Length in Pixels.vi"/>
				<Item Name="LVBoundsTypeDef.ctl" Type="VI" URL="/&lt;vilib&gt;/Utility/miscctls.llb/LVBoundsTypeDef.ctl"/>
				<Item Name="LVRectTypeDef.ctl" Type="VI" URL="/&lt;vilib&gt;/Utility/miscctls.llb/LVRectTypeDef.ctl"/>
				<Item Name="NI-845x Close Device Reference.vi" Type="VI" URL="/&lt;vilib&gt;/ni845x/ni845x.llb/NI-845x Close Device Reference.vi"/>
				<Item Name="NI-845x Close Reference.vi" Type="VI" URL="/&lt;vilib&gt;/ni845x/ni845x.llb/NI-845x Close Reference.vi"/>
				<Item Name="NI-845x Fill in Error Info.vi" Type="VI" URL="/&lt;vilib&gt;/ni845x/ni845x.llb/NI-845x Fill in Error Info.vi"/>
				<Item Name="NI-845x I2C Close Configuration Reference.vi" Type="VI" URL="/&lt;vilib&gt;/ni845x/ni845x.llb/NI-845x I2C Close Configuration Reference.vi"/>
				<Item Name="NI-845x I2C Close Script Reference.vi" Type="VI" URL="/&lt;vilib&gt;/ni845x/ni845x.llb/NI-845x I2C Close Script Reference.vi"/>
				<Item Name="NI-845x I2C Slave Close Configuration Reference.vi" Type="VI" URL="/&lt;vilib&gt;/ni845x/ni845x.llb/NI-845x I2C Slave Close Configuration Reference.vi"/>
				<Item Name="NI-845x SPI Close Configuration Reference.vi" Type="VI" URL="/&lt;vilib&gt;/ni845x/ni845x.llb/NI-845x SPI Close Configuration Reference.vi"/>
				<Item Name="NI-845x SPI Close Script Reference.vi" Type="VI" URL="/&lt;vilib&gt;/ni845x/ni845x.llb/NI-845x SPI Close Script Reference.vi"/>
				<Item Name="NI-845x SPI Create Script Reference.vi" Type="VI" URL="/&lt;vilib&gt;/ni845x/ni845x.llb/NI-845x SPI Create Script Reference.vi"/>
				<Item Name="NI-845x SPI Extract Script Read Data.vi" Type="VI" URL="/&lt;vilib&gt;/ni845x/ni845x.llb/NI-845x SPI Extract Script Read Data.vi"/>
				<Item Name="NI-845x SPI Run Script.vi" Type="VI" URL="/&lt;vilib&gt;/ni845x/ni845x.llb/NI-845x SPI Run Script.vi"/>
				<Item Name="NI-845x SPI Script Clock Polarity Phase.vi" Type="VI" URL="/&lt;vilib&gt;/ni845x/ni845x.llb/NI-845x SPI Script Clock Polarity Phase.vi"/>
				<Item Name="NI-845x SPI Script Clock Rate.vi" Type="VI" URL="/&lt;vilib&gt;/ni845x/ni845x.llb/NI-845x SPI Script Clock Rate.vi"/>
				<Item Name="NI-845x SPI Script CS High.vi" Type="VI" URL="/&lt;vilib&gt;/ni845x/ni845x.llb/NI-845x SPI Script CS High.vi"/>
				<Item Name="NI-845x SPI Script CS Low.vi" Type="VI" URL="/&lt;vilib&gt;/ni845x/ni845x.llb/NI-845x SPI Script CS Low.vi"/>
				<Item Name="NI-845x SPI Script Delay.vi" Type="VI" URL="/&lt;vilib&gt;/ni845x/ni845x.llb/NI-845x SPI Script Delay.vi"/>
				<Item Name="NI-845x SPI Script DIO Configure Line.vi" Type="VI" URL="/&lt;vilib&gt;/ni845x/ni845x.llb/NI-845x SPI Script DIO Configure Line.vi"/>
				<Item Name="NI-845x SPI Script DIO Configure Port.vi" Type="VI" URL="/&lt;vilib&gt;/ni845x/ni845x.llb/NI-845x SPI Script DIO Configure Port.vi"/>
				<Item Name="NI-845x SPI Script DIO Write Line.vi" Type="VI" URL="/&lt;vilib&gt;/ni845x/ni845x.llb/NI-845x SPI Script DIO Write Line.vi"/>
				<Item Name="NI-845x SPI Script Disable SPI.vi" Type="VI" URL="/&lt;vilib&gt;/ni845x/ni845x.llb/NI-845x SPI Script Disable SPI.vi"/>
				<Item Name="NI-845x SPI Script Enable SPI.vi" Type="VI" URL="/&lt;vilib&gt;/ni845x/ni845x.llb/NI-845x SPI Script Enable SPI.vi"/>
				<Item Name="NI-845x SPI Script Ms Delay.vi" Type="VI" URL="/&lt;vilib&gt;/ni845x/ni845x.llb/NI-845x SPI Script Ms Delay.vi"/>
				<Item Name="NI-845x SPI Script Us Delay.vi" Type="VI" URL="/&lt;vilib&gt;/ni845x/ni845x.llb/NI-845x SPI Script Us Delay.vi"/>
				<Item Name="NI-845x SPI Script Write Read.vi" Type="VI" URL="/&lt;vilib&gt;/ni845x/ni845x.llb/NI-845x SPI Script Write Read.vi"/>
				<Item Name="NI-845x SPI Stream Close Configuration Reference.vi" Type="VI" URL="/&lt;vilib&gt;/ni845x/ni845x.llb/NI-845x SPI Stream Close Configuration Reference.vi"/>
				<Item Name="ni845xControl.ctl" Type="VI" URL="/&lt;vilib&gt;/ni845x/ni845x.llb/ni845xControl.ctl"/>
				<Item Name="ni845xDioLineConfiguration.ctl" Type="VI" URL="/&lt;vilib&gt;/ni845x/ni845x.llb/ni845xDioLineConfiguration.ctl"/>
				<Item Name="ni845xDioLineWriteValue.ctl" Type="VI" URL="/&lt;vilib&gt;/ni845x/ni845x.llb/ni845xDioLineWriteValue.ctl"/>
				<Item Name="ni845xI2cConfiguration.ctl" Type="VI" URL="/&lt;vilib&gt;/ni845x/ni845x.llb/ni845xI2cConfiguration.ctl"/>
				<Item Name="ni845xI2cScriptControl.ctl" Type="VI" URL="/&lt;vilib&gt;/ni845x/ni845x.llb/ni845xI2cScriptControl.ctl"/>
				<Item Name="ni845xI2cSlaveConfiguration.ctl" Type="VI" URL="/&lt;vilib&gt;/ni845x/ni845x.llb/ni845xI2cSlaveConfiguration.ctl"/>
				<Item Name="ni845xSpiConfiguration.ctl" Type="VI" URL="/&lt;vilib&gt;/ni845x/ni845x.llb/ni845xSpiConfiguration.ctl"/>
				<Item Name="ni845xSpiScriptControl.ctl" Type="VI" URL="/&lt;vilib&gt;/ni845x/ni845x.llb/ni845xSpiScriptControl.ctl"/>
				<Item Name="ni845xSpiStreamConfiguration.ctl" Type="VI" URL="/&lt;vilib&gt;/ni845x/ni845x.llb/ni845xSpiStreamConfiguration.ctl"/>
				<Item Name="NI_Gmath.lvlib" Type="Library" URL="/&lt;vilib&gt;/gmath/NI_Gmath.lvlib"/>
				<Item Name="NI_XML.lvlib" Type="Library" URL="/&lt;vilib&gt;/xml/NI_XML.lvlib"/>
				<Item Name="Not Found Dialog.vi" Type="VI" URL="/&lt;vilib&gt;/Utility/error.llb/Not Found Dialog.vi"/>
				<Item Name="Search and Replace Pattern.vi" Type="VI" URL="/&lt;vilib&gt;/Utility/error.llb/Search and Replace Pattern.vi"/>
				<Item Name="Set Bold Text.vi" Type="VI" URL="/&lt;vilib&gt;/Utility/error.llb/Set Bold Text.vi"/>
				<Item Name="Set String Value.vi" Type="VI" URL="/&lt;vilib&gt;/Utility/error.llb/Set String Value.vi"/>
				<Item Name="Simple Error Handler.vi" Type="VI" URL="/&lt;vilib&gt;/Utility/error.llb/Simple Error Handler.vi"/>
				<Item Name="Space Constant.vi" Type="VI" URL="/&lt;vilib&gt;/dlg_ctls.llb/Space Constant.vi"/>
				<Item Name="subDisplayMessage.vi" Type="VI" URL="/&lt;vilib&gt;/express/express output/DisplayMessageBlock.llb/subDisplayMessage.vi"/>
				<Item Name="TagReturnType.ctl" Type="VI" URL="/&lt;vilib&gt;/Utility/error.llb/TagReturnType.ctl"/>
				<Item Name="TCP Listen Internal List.vi" Type="VI" URL="/&lt;vilib&gt;/Utility/tcp.llb/TCP Listen Internal List.vi"/>
				<Item Name="TCP Listen List Operations.ctl" Type="VI" URL="/&lt;vilib&gt;/Utility/tcp.llb/TCP Listen List Operations.ctl"/>
				<Item Name="TCP Listen.vi" Type="VI" URL="/&lt;vilib&gt;/Utility/tcp.llb/TCP Listen.vi"/>
				<Item Name="Three Button Dialog CORE.vi" Type="VI" URL="/&lt;vilib&gt;/Utility/error.llb/Three Button Dialog CORE.vi"/>
				<Item Name="Three Button Dialog.vi" Type="VI" URL="/&lt;vilib&gt;/Utility/error.llb/Three Button Dialog.vi"/>
				<Item Name="Trim Whitespace.vi" Type="VI" URL="/&lt;vilib&gt;/Utility/error.llb/Trim Whitespace.vi"/>
				<Item Name="whitespace.ctl" Type="VI" URL="/&lt;vilib&gt;/Utility/error.llb/whitespace.ctl"/>
			</Item>
			<Item Name="append_to_log.vi" Type="VI" URL="../../append_to_log.vi"/>
			<Item Name="DDS.lvclass" Type="LVClass" URL="../../DDS/DDS.lvclass"/>
			<Item Name="DDS.lvlib" Type="Library" URL="../../DDS/DDS Library/DDS.lvlib"/>
			<Item Name="DOMUserDefRef.dll" Type="Document" URL="DOMUserDefRef.dll">
				<Property Name="NI.PreserveRelativePath" Type="Bool">true</Property>
			</Item>
			<Item Name="Globals.vi" Type="VI" URL="../../Globals.vi"/>
			<Item Name="handle_errors.vi" Type="VI" URL="../../handle_errors.vi"/>
			<Item Name="lvanlys.dll" Type="Document" URL="/&lt;resource&gt;/lvanlys.dll"/>
			<Item Name="ni845x.dll" Type="Document" URL="ni845x.dll">
				<Property Name="NI.PreserveRelativePath" Type="Bool">true</Property>
			</Item>
			<Item Name="string_to_boolean.vi" Type="VI" URL="../../config_file_io/string_to_boolean.vi"/>
			<Item Name="TCP_IP.lvclass" Type="LVClass" URL="../../TCP_IP/TCP_IP.lvclass"/>
		</Item>
		<Item Name="Build Specifications" Type="Build">
			<Item Name="DDS_server" Type="EXE">
				<Property Name="App_copyErrors" Type="Bool">true</Property>
				<Property Name="App_INI_aliasGUID" Type="Str">{058806A0-4740-4C85-857C-3E5FF188EADF}</Property>
				<Property Name="App_INI_GUID" Type="Str">{FE61A18A-746E-4F3A-85BA-B6D6664736A9}</Property>
				<Property Name="App_serverConfig.httpPort" Type="Int">8002</Property>
				<Property Name="Bld_autoIncrement" Type="Bool">true</Property>
				<Property Name="Bld_buildCacheID" Type="Str">{69358C2F-B6CB-40D0-9382-997833F356C0}</Property>
				<Property Name="Bld_buildSpecName" Type="Str">DDS_server</Property>
				<Property Name="Bld_excludeInlineSubVIs" Type="Bool">true</Property>
				<Property Name="Bld_excludeLibraryItems" Type="Bool">true</Property>
				<Property Name="Bld_excludePolymorphicVIs" Type="Bool">true</Property>
				<Property Name="Bld_localDestDir" Type="Path">../builds</Property>
				<Property Name="Bld_localDestDirType" Type="Str">relativeToCommon</Property>
				<Property Name="Bld_modifyLibraryFile" Type="Bool">true</Property>
				<Property Name="Bld_previewCacheID" Type="Str">{BC4D42C8-0912-4759-B4C3-AC589F60D831}</Property>
				<Property Name="Bld_version.build" Type="Int">1</Property>
				<Property Name="Bld_version.major" Type="Int">1</Property>
				<Property Name="Destination[0].destName" Type="Str">DDS_server.exe</Property>
				<Property Name="Destination[0].path" Type="Path">../builds/NI_AB_PROJECTNAME.exe</Property>
				<Property Name="Destination[0].preserveHierarchy" Type="Bool">true</Property>
				<Property Name="Destination[0].type" Type="Str">App</Property>
				<Property Name="Destination[1].destName" Type="Str">Support Directory</Property>
				<Property Name="Destination[1].path" Type="Path">../builds/data</Property>
				<Property Name="DestinationCount" Type="Int">2</Property>
				<Property Name="Source[0].itemID" Type="Str">{C8C1E3BD-E5D0-406C-A286-DE8B6810F23D}</Property>
				<Property Name="Source[0].type" Type="Str">Container</Property>
				<Property Name="Source[1].destinationIndex" Type="Int">0</Property>
				<Property Name="Source[1].itemID" Type="Ref">/My Computer/Experiment.lvclass/DDS_server.vi</Property>
				<Property Name="Source[1].sourceInclusion" Type="Str">TopLevel</Property>
				<Property Name="Source[1].type" Type="Str">VI</Property>
				<Property Name="SourceCount" Type="Int">2</Property>
				<Property Name="TgtF_fileDescription" Type="Str">DDS_server</Property>
				<Property Name="TgtF_internalName" Type="Str">DDS_server</Property>
				<Property Name="TgtF_legalCopyright" Type="Str">Copyright © 2020 </Property>
				<Property Name="TgtF_productName" Type="Str">DDS_server</Property>
				<Property Name="TgtF_targetfileGUID" Type="Str">{B33477C6-8A6F-434B-9E16-4C5738317FDA}</Property>
				<Property Name="TgtF_targetfileName" Type="Str">DDS_server.exe</Property>
			</Item>
		</Item>
	</Item>
</Project>
