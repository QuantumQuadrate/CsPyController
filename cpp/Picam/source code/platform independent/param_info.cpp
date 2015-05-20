////////////////////////////////////////////////////////////////////////////////
// ParamInfo Sample
// - prints all parameter information of a camera to the console
// - uses the first camera found if any or creates a demo camera
////////////////////////////////////////////////////////////////////////////////

#include <algorithm>
#include <iostream>
#include <iomanip>
#include <string>
#include <sstream>
#include <vector>
#include "picam_advanced.h"

// - constants for formatting
const piint column1_width = 13;
const piint column2_width = 37;
const piint column3_width = 12;
const piint column4_width = 18;
const piint print_width =
    column1_width + column2_width + column3_width + column4_width;
const piint column1b_width = 15;

// - C++ functor to sort parameters in ascending alphabetical order
struct SortAlphabetically
{
    pibool operator()( PicamParameter a, PicamParameter b ) const
    {
        // - get the string for first parameter
        const pichar* string;
        Picam_GetEnumerationString(
            PicamEnumeratedType_Parameter,
            a,
            &string );
        std::string string_a( string );
        Picam_DestroyString( string );

        // - get the string for the second parameter
        Picam_GetEnumerationString(
            PicamEnumeratedType_Parameter,
            b,
            &string );
        std::string string_b( string );
        Picam_DestroyString( string );
        
        // - use default C++ comparison
        return string_a < string_b;
    }
};

// - sorts parameters alphabetically
std::vector<PicamParameter> SortParameters(
    const PicamParameter* parameters,
    piint count )
{
    std::vector<PicamParameter> sorted( parameters, parameters+count );
    std::sort( sorted.begin(), sorted.end(), SortAlphabetically() );
    return sorted;
}

// - prints any picam enum to the console
void PrintEnumString( PicamEnumeratedType type, piint value )
{
    const pichar* string;
    Picam_GetEnumerationString( type, value, &string );
    std::cout << string;
    Picam_DestroyString( string );
}

// - prints the current value of any picam integer parameter
void PrintIntegerValue( PicamHandle camera, PicamParameter parameter )
{
    piint value;
    Picam_GetParameterIntegerValue( camera, parameter, &value );
    std::cout << value << std::endl;
}

// - prints the current value of any picam boolean parameter
void PrintBooleanValue( PicamHandle camera, PicamParameter parameter )
{
    pibln value;
    Picam_GetParameterIntegerValue( camera, parameter, &value );

    // - print as C++ bool
    std::cout << (value != 0) << std::endl;
}

// - prints the current value of any picam enumeration parameter
void PrintEnumValue( PicamHandle camera, PicamParameter parameter )
{
    piint value;
    Picam_GetParameterIntegerValue( camera, parameter, &value );

    // - get the parameter's enumeration type
    PicamEnumeratedType type;
    Picam_GetParameterEnumeratedType( camera, parameter, &type );

    PrintEnumString( type, value );
    std::cout << std::endl;
}

// - prints the current value of any picam large integer parameter
void PrintLargeIntegerValue( PicamHandle camera, PicamParameter parameter )
{
    pi64s value;
    Picam_GetParameterLargeIntegerValue( camera, parameter, &value );
    std::cout << value << std::endl;
}

// - prints the current value of any picam floating point parameter
void PrintFloatingPointValue( PicamHandle camera, PicamParameter parameter )
{
    piflt value;
    Picam_GetParameterFloatingPointValue( camera, parameter, &value );
    std::cout << value << std::endl;
}

// - prints the current value of any picam rois parameter
void PrintRoisValue( PicamHandle camera, PicamParameter parameter )
{
    // - note accessing the rois returns an allocated copy
    const PicamRois* value;
    Picam_GetParameterRoisValue( camera, parameter, &value );

    std::cout << "starting at (" << value->roi_array[0].x
              << ","             << value->roi_array[0].y
              << ") of size "    << value->roi_array[0].width
              << "x"             << value->roi_array[0].height
              << " with "        << value->roi_array[0].x_binning
              << "x"             << value->roi_array[0].y_binning
              << " binning"      << std::endl;

    // - deallocate the value after printing
    Picam_DestroyRois( value );
}

// - prints the current value of any picam pulse parameter
void PrintPulseValue( PicamHandle camera, PicamParameter parameter )
{
    // - note accessing the pulse returns an allocated copy
    const PicamPulse* value;
    Picam_GetParameterPulseValue( camera, parameter, &value );

    std::cout << "delayed to " << value->delay
              << " of width "    << value->width
              << std::endl;

    // - deallocate the value after printing
    Picam_DestroyPulses( value );
}

// - prints the current value of any picam modulations parameter
void PrintModulationsValue( PicamHandle camera, PicamParameter parameter )
{
    // - note accessing the modulations returns an allocated copy
    const PicamModulations* value;
    Picam_GetParameterModulationsValue( camera, parameter, &value );

    std::cout << "cos("
              << value->modulation_array[0].frequency
              << "t + "
              << value->modulation_array[0].phase
              << "pi/180) lasting "
              << value->modulation_array[0].duration
              << " with output signal cos("
              << value->modulation_array[0].output_signal_frequency
              << "t)"
              << std::endl;

    // - deallocate the value after printing
    Picam_DestroyModulations( value );
}

// - prints the initial value of any picam parameter value
void PrintValue(
    PicamHandle camera,
    PicamParameter parameter,
    PicamValueType value_type )
{
    std::cout << std::setw( column1b_width ) << "Initial Value:";
    switch( value_type )
    {
        case PicamValueType_Integer:
            PrintIntegerValue( camera, parameter );
            break;
        case PicamValueType_Boolean:
            PrintBooleanValue( camera, parameter );
            break;
        case PicamValueType_Enumeration:
            PrintEnumValue( camera, parameter );
            break;
        case PicamValueType_LargeInteger:
            PrintLargeIntegerValue( camera, parameter );
            break;
        case PicamValueType_FloatingPoint:
            PrintFloatingPointValue( camera, parameter );
            break;
        case PicamValueType_Rois:
            PrintRoisValue( camera, parameter );
            break;
        case PicamValueType_Pulse:
            PrintPulseValue( camera, parameter );
            break;
        case PicamValueType_Modulations:
            PrintModulationsValue( camera, parameter );
            break;
        default:
            std::cout << "N/A" << std::endl;
            break;
    }
}

// - prints the capabilities of any picam range parameter
void PrintRangeCapabilities( PicamHandle camera, PicamParameter parameter )
{
    // - note accessing a constraint returns an allocated copy
    const PicamRangeConstraint* capable;
    Picam_GetParameterRangeConstraint(
        camera,
        parameter,
        PicamConstraintCategory_Capable,
        &capable );

    // - describe the basic range
    std::cout << "from " << capable->minimum
              << " to "  << capable->maximum
              << " increments of " << capable->increment;

    // - describe any extra values that fall outside of the range
    if( capable->outlying_values_count )
    {
        std::cout << " (including: ";
        for( piint i = 0; i < capable->outlying_values_count; ++i )
        {
            if( i )
                std::cout << ", ";
            std::cout << capable->outlying_values_array[i];
        }
        std::cout << ")";
    }

    // - describe any values inside the range that are not permitted
    if( capable->excluded_values_count )
    {
        std::cout << " (excluding: ";
        for( piint i = 0; i < capable->excluded_values_count; ++i )
        {
            if( i )
                std::cout << ", ";
            std::cout << capable->excluded_values_array[i];
        }
        std::cout << ")";
    }

    // - deallocate the constraint after printing
    Picam_DestroyRangeConstraints( capable );

    std::cout << std::endl;
}

// - prints the capabilities of any picam collection parameter
void PrintCollectionCapabilities(
    PicamHandle camera,
    PicamParameter parameter,
    PicamValueType value_type )
{
    // - note accessing a constraint returns an allocated copy
    const PicamCollectionConstraint* capable;
    Picam_GetParameterCollectionConstraint(
        camera,
        parameter,
        PicamConstraintCategory_Capable,
        &capable );

    // - list each possible value
    for( piint i = 0; i < capable->values_count; ++i )
    {
        if( i )
            std::cout << ", ";

        // - print each value as the appropriate type
        piflt value = capable->values_array[i];
        switch( value_type )
        {
            case PicamValueType_Integer:
                std::cout << static_cast<piint>( value );
                break;
            case PicamValueType_Boolean:
                std::cout << (value != 0);
                break;
            case PicamValueType_Enumeration:
            {
                PicamEnumeratedType type;
                Picam_GetParameterEnumeratedType(
                    camera,
                    parameter,
                    &type );
                PrintEnumString( type, static_cast<piint>( value ) );
                break;
            }
            case PicamValueType_LargeInteger:
                std::cout << static_cast<pi64s>( value );
                break;
            case PicamValueType_FloatingPoint:
                std::cout << capable->values_array[i];
                break;
            default:
                std::cout << capable->values_array[i]
                          << " (unknown type)";
                break;
        }
    }

    // - deallocate the constraint after printing
    Picam_DestroyCollectionConstraints( capable );

    std::cout << std::endl;
}

// - prints the capabilities of any picam rois parameter
void PrintRoisCapabilities( PicamHandle camera, PicamParameter parameter )
{
    // - note accessing a constraint returns an allocated copy
    const PicamRoisConstraint* capable;
    Picam_GetParameterRoisConstraint(
        camera,
        parameter,
        PicamConstraintCategory_Capable,
        &capable );

    // - determine if the number of rois is limited by assuming
    //   each pixel on the sensor can be one region
    pibool limited_roi_count = 
        capable->maximum_roi_count < 
        (capable->width_constraint.maximum*capable->height_constraint.maximum);

    pibool any_restrictions =
        capable->rules != PicamRoisConstraintRulesMask_None ||
        limited_roi_count ||
        capable->x_binning_limits_count ||
        capable->y_binning_limits_count;

    if( !any_restrictions )
        std::cout << "no restrictions";
    else
    {
        // - note each restriction
        std::cout << "restrictions involving ";
        std::ostringstream oss;
        if( capable->rules != PicamRoisConstraintRulesMask_None )
        {
            PrintEnumString(
                PicamEnumeratedType_RoisConstraintRulesMask,
                capable->rules );
            oss << " as well as ";
        }
        pibool printed = false;
        if( limited_roi_count )
        {
            oss << "ROI Count";
            printed = true;
        }
        if( capable->x_binning_limits_count )
        {
            if( printed )
                oss << ", ";
            oss << "X-Binning";
            printed = true;
        }
        if( capable->y_binning_limits_count )
        {
            if( printed )
                oss << ", ";
            oss << "Y-Binning";
            printed = true;
        }
        if( printed )
            std::cout << oss.str();
    }

    // - deallocate the constraint after printing
    Picam_DestroyRoisConstraints( capable );

    std::cout << std::endl;
}

// - prints the capabilities of any picam pulse parameter
void PrintPulseCapabilities( PicamHandle camera, PicamParameter parameter )
{
    // - note accessing a constraint returns an allocated copy
    const PicamPulseConstraint* capable;
    Picam_GetParameterPulseConstraint(
        camera,
        parameter,
        PicamConstraintCategory_Capable,
        &capable );

    std::cout << "duration from " << capable->minimum_duration
              << " to "           << capable->maximum_duration;

    // - deallocate the constraint after printing
    Picam_DestroyPulseConstraints( capable );

    std::cout << std::endl;
}

// - prints the capabilities of any picam modulations parameter
void PrintModulationsCapabilities(
    PicamHandle camera,
    PicamParameter parameter )
{
    // - note accessing a constraint returns an allocated copy
    const PicamModulationsConstraint* capable;
    Picam_GetParameterModulationsConstraint(
        camera,
        parameter,
        PicamConstraintCategory_Capable,
        &capable );

    std::cout << capable->maximum_modulation_count
              << " maximum modulations"
              << std::endl;

    // - deallocate the constraint after printing
    Picam_DestroyModulationsConstraints( capable );

    std::cout << std::endl;
}

// - prints the capabilities of any picam parameter
void PrintCapabilities(
    PicamHandle camera,
    PicamParameter parameter,
    PicamConstraintType constraint_type,
    PicamValueType value_type )
{
    std::cout << std::setw( column1b_width ) << "Capabilities:";
    switch( constraint_type )
    {
        case PicamConstraintType_None:
            std::cout << "N/A" << std::endl;
            break;
        case PicamConstraintType_Range:
            PrintRangeCapabilities( camera, parameter );
            break;
        case PicamConstraintType_Collection:
            PrintCollectionCapabilities( camera, parameter, value_type );
            break;
        case PicamConstraintType_Rois:
            PrintRoisCapabilities( camera, parameter );
            break;
        case PicamConstraintType_Pulse:
            PrintPulseCapabilities( camera, parameter );
            break;
        case PicamConstraintType_Modulations:
            PrintModulationsCapabilities( camera, parameter );
            break;
        default:
            std::cout << "N/A" << std::endl;
            break;
    }
}

// - prints all information pertaining to any picam parameter
void PrintParameter( PicamHandle camera, PicamParameter parameter )
{
    // - print parameter name
    std::cout << std::setw( column1_width ) << "Parameter:";
    std::cout << std::setw( column2_width );
    PrintEnumString( PicamEnumeratedType_Parameter, parameter );

    // - print numeric value of the parameter enum
    std::cout << std::setw( column3_width ) << "ID:";
    std::cout << std::hex << parameter << std::dec << std::endl;

    // - print the value type
    std::cout << std::setw( column1_width ) << "Value Type:";
    std::cout << std::setw( column2_width );
    PicamValueType value_type;
    Picam_GetParameterValueType(
        camera,
        parameter,
        &value_type );
    PrintEnumString( PicamEnumeratedType_ValueType, value_type );

    // - print the value access
    std::cout << std::setw( column3_width ) << "Access:";
    PicamValueAccess value_access;
    Picam_GetParameterValueAccess(
        camera,
        parameter,
        &value_access );
    PrintEnumString( PicamEnumeratedType_ValueAccess, value_access );
    std::cout << std::endl;

    // - print the enumeration value type if applicable
    std::cout << std::setw( column1_width ) << "Enumeration:";
    std::cout << std::setw( column2_width );
    if( value_type != PicamValueType_Enumeration )
        std::cout << "N/A";
    else
    {
        PicamEnumeratedType enumerated_type;
        Picam_GetParameterEnumeratedType(
            camera,
            parameter,
            &enumerated_type );
        PrintEnumString( PicamEnumeratedType_EnumeratedType, enumerated_type );
    }

    // - print the current relevance of the parameter
    std::cout << std::setw( column3_width ) << "Relevant:";
    pibln relevant;
    Picam_IsParameterRelevant(
        camera,
        parameter,
        &relevant );
    std::cout << (relevant != 0) << std::endl;

    // - print the constraint type
    std::cout << std::setw( column1_width ) << "Constraint:";
    std::cout << std::setw( column2_width );
    PicamConstraintType constraint_type;
    Picam_GetParameterConstraintType(
        camera,
        parameter,
        &constraint_type );
    PrintEnumString( PicamEnumeratedType_ConstraintType, constraint_type );

    // - print if the value can be set while the camera is acquiring
    std::cout << std::setw( column3_width ) << "Onlineable:";
    if( value_access == PicamValueAccess_ReadOnly )
        std::cout << "N/A" << std::endl;
    else
    {
        pibln onlineable = false;
        Picam_CanSetParameterOnline(
            camera,
            parameter,
            &onlineable );
        std::cout << (onlineable != 0) << std::endl;
    }

    // - print which properties of the parameter can change
    std::cout << std::setw( column1_width ) << "Dynamics:";
    std::cout << std::setw( column2_width );
    PicamDynamicsMask dynamics;
    PicamAdvanced_GetParameterDynamics(
        camera,
        parameter,
        &dynamics );
    PrintEnumString( PicamEnumeratedType_DynamicsMask, dynamics );

    // - print if the value is volatile and should
    //   be read directly from the camera hardware
    std::cout << std::setw( column3_width ) << "Readable:";
    pibln readable;
    Picam_CanReadParameter(
        camera,
        parameter,
        &readable );
    std::cout << (readable != 0) << std::endl;

    // - print a separator between parameter information and value information
    std::cout << std::string( print_width, '-' ) << std::endl;

    PrintValue( camera, parameter, value_type );
    PrintCapabilities( camera, parameter, constraint_type, value_type );
}

// - prints the camera identity
void PrintCameraID( const PicamCameraID& id )
{
    PrintEnumString( PicamEnumeratedType_Model, id.model );
    std::cout << " (SN:" << id.serial_number << ")"
              << " ["    << id.sensor_name   << "]" << std::endl;
}

int main( int argc, char* argv[] )
{
    // - set formatting options
    std::cout << std::boolalpha << std::showbase << std::left;

    // - allow the following optional argument(s) (in any order):
    //   - demo camera model as the enum integer value
    //   - serial number as single-quoted string
    piint optionalDemoModel = -1;
    std::string optionalDemoSerialNumber;
    if( argc == 2 || argc == 3 )
    {
        piint arguments = argc-1;
        piint parsed = 0;
        while( parsed != arguments )
        {
            std::string arg( argv[parsed+1] );
            if( !arg.empty() && arg[0] == '\'' )
            {
                if( !optionalDemoSerialNumber.empty() )
                {
                    std::cout << "Demo camera serial number already supplied.";
                    return -1;
                }
                if( arg.size() < 3 || arg[arg.size()-1] != '\'' )
                {
                    std::cout << "Invalid demo camera serial number format.";
                    return -1;
                }
                optionalDemoSerialNumber = arg.substr( 1, arg.size()-2 );
            }
            else
            {
                if( optionalDemoModel != -1 )
                {
                    std::cout << "Demo camera model already supplied.";
                    return -1;
                }
                std::istringstream iss( arg );
                iss >> optionalDemoModel;
                if( iss.fail() || !iss.eof() )
                {
                    std::cout << "Invalid demo camera model format.";
                    return -1;
                }
            }
            ++parsed;
        }
    }

    Picam_InitializeLibrary();

    // - try to open the first camera if optional demo camera not specified
    PicamHandle camera;
    PicamCameraID id;
    if( optionalDemoModel == -1 &&
        Picam_OpenFirstCamera( &camera ) == PicamError_None )
    {
        Picam_GetCameraID( camera, &id );
    }
    else
    {
        // - provide a default demo camera if not specified
        PicamModel demoModel =
            optionalDemoModel != -1
                ? static_cast<PicamModel>( optionalDemoModel )
                : PicamModel_Pixis100B;
        std::string demoSerialNumber =
            !optionalDemoSerialNumber.empty()
                ? optionalDemoSerialNumber
                : "12345";

        // - try to connect the demo camera
        PicamError error =
            Picam_ConnectDemoCamera(
                demoModel,
                demoSerialNumber.c_str(),
                &id );
        if( error == PicamError_InvalidDemoModel )
        {
            std::cout << "Invalid demo camera model specified.";
            Picam_UninitializeLibrary();
            return -2;
        }

        // - open the demo camera once successfully connected
        Picam_OpenCamera( &id, &camera );
    }

    // - print an initial seperator
    const std::string marker( print_width, '=' );
    std::cout << marker << std::endl;

    PrintCameraID( id );

    // - accessing parameters returns an allocated array
    const PicamParameter* parameters;
    piint count;
    Picam_GetParameters( camera, &parameters, &count );

    // - copy and sort the parameters to something more suitable for display
    std::vector<PicamParameter> sorted = SortParameters( parameters, count );

    // - deallocate the parameter array after usage
    Picam_DestroyParameters( parameters );

    // - display the number of parameters available for this particular camera
    std::cout << "Parameters: " << count << std::endl;

    // - print each parameter
    for( piint i = 0; i < count; ++i )
    {
        std::cout << marker << std::endl;
        PrintParameter( camera, sorted[i] );
    }

    // - print a final seperator
    std::cout << marker << std::endl;

    Picam_CloseCamera( camera );

    Picam_UninitializeLibrary();
}
