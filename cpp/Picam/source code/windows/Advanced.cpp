////////////////////////////////////////////////////////////////////////////////
// Advanced Sample
// - exercises the picam advanced api in a basic windows application
////////////////////////////////////////////////////////////////////////////////

//##############################################################################
//##############################################################################
//##############################################################################
//##############################################################################
// Pragmas
//##############################################################################
//##############################################################################
//##############################################################################
//##############################################################################
////////////////////////////////////////////////////////////////////////////////
// Enable Visual Styles
////////////////////////////////////////////////////////////////////////////////
#pragma comment( linker, \
"/manifestdependency:\"type='win32' "\
"name='Microsoft.Windows.Common-Controls' "\
"version='6.0.0.0' "\
"processorArchitecture='amd64' "\
"publicKeyToken='6595b64144ccf1df' "\
"language='*'\"" )

#pragma comment(lib, "Ws2_32.lib")

//##############################################################################
//##############################################################################
//##############################################################################
//##############################################################################
// Header Files
//##############################################################################
//##############################################################################
//##############################################################################
//##############################################################################
////////////////////////////////////////////////////////////////////////////////
// Windows Headers
////////////////////////////////////////////////////////////////////////////////
#define WINVER 0x600
#define WIN23_LEAN_AND_MEAN
#define UNICODE
#define NOMINMAX
#include <windows.h>
#include <process.h>
#include <commctrl.h>
#include <string>
using namespace std;


#define WINSOCK_MESSAGE 1045
#define PORTNO 2153

////////////////////////////////////////////////////////////////////////////////
// Standard C++ Library Headers
////////////////////////////////////////////////////////////////////////////////
#include <cmath>
#include <cstring>
#include <algorithm>
#include <fstream>
#include <iterator>
#include <list>
#include <sstream>
#include <string>
#include <vector>
#include <winsock.h>
#include <codecvt>

////////////////////////////////////////////////////////////////////////////////
// Picam Header
////////////////////////////////////////////////////////////////////////////////
#include "picam_advanced.h"

////////////////////////////////////////////////////////////////////////////////
// Window Resource Header
////////////////////////////////////////////////////////////////////////////////
#include "AdvancedResource.h"

//##############################################################################
//##############################################################################
//##############################################################################
//##############################################################################
// Window Constants
//##############################################################################
//##############################################################################
//##############################################################################
//##############################################################################
////////////////////////////////////////////////////////////////////////////////
// Application Exit Codes
////////////////////////////////////////////////////////////////////////////////
enum ExitCode
{
    ExitCode_Success                    =  0,
    ExitCode_RegisterWindowClassFailed  = -1,
    ExitCode_InitializeMainWindowFailed = -2,
    ExitCode_GetMessageFailed           = -3,
    ExitCode_FailedInitialize           = -4
};

////////////////////////////////////////////////////////////////////////////////
// Main Window Class Name
////////////////////////////////////////////////////////////////////////////////
const wchar_t* mainWindowClassName_ = L"MainWindow";

////////////////////////////////////////////////////////////////////////////////
// User-Defined Window Messages
////////////////////////////////////////////////////////////////////////////////
enum
{
    WM_DISPLAY_ERROR = WM_USER+1,   // - display an error (wParam: wstring*)
    WM_REFRESH_CAMERAS,             // - refresh camera selection dialog
    WM_ACQUISITION_STOPPED          // - indicate acquisition is finished
};

struct wsmessage{
	char mesg[5];
	INT32 len;
	char* message;
};

struct wsmessageimagedata{
	char mesg[5];
	INT32 len;
	char* message;
	char16_t* imagedat;
	INT32 imagelen;
};

// Prototypes for functions for using Winsock
int ListenOnPort(short int PortNo);
int ParseInput(char* buffer, int datalen);
int StringToWString(std::wstring &ws, const std::string &s);
int formatmessage(string message, int &length, wsmessage &formattedmessage);
int formatmessageimage(string message, int &length, wsmessageimagedata &formattedmessage, char16_t &imagedat, int imagelen);
int sendmessage(wsmessage formatmesg);
int sendmessageimage(wsmessageimagedata formatmesg);
int test_picam_error(PicamError error, string errmess);
string GetParametersAsString();
void RefreshParametersNoDialog();

int sendmessageimagemult(wsmessageimagedata formatmesg, vector<pi16u>* imgs, int imgssize);
int formatmessageimagemult(string message, int &length, wsmessageimagedata &formattedmessage, vector<char16_t> &imagedat, int imagelen);


PicamAvailableData availabledata;

string ws2s(const std::wstring& wstr);
std::vector<std::string> &split(const std::string &s, char delim, std::vector<std::string> &elems);
std::vector<std::string> split(const std::string &s, char delim);

////////////////////////////////////////////////////////////////////////////////
// Dialog Function Prototypes
////////////////////////////////////////////////////////////////////////////////
void RefreshCamerasDialog( HWND dialog );
INT_PTR CALLBACK CamerasDialogProc(
    HWND hwndDlg,
    UINT uMsg,
    WPARAM wParam,
    LPARAM lParam );
void RefreshExposureDialog( HWND dialog );
INT_PTR CALLBACK ExposureDialogProc(
    HWND hwndDlg,
    UINT uMsg,
    WPARAM wParam,
    LPARAM lParam );
void RefreshRepetitiveGateDialog( HWND dialog );
INT_PTR CALLBACK RepetitiveGateDialogProc(
    HWND hwndDlg,
    UINT uMsg,
    WPARAM wParam,
    LPARAM lParam );
INT_PTR CALLBACK ParametersDialogProc(
    HWND hwndDlg,
    UINT uMsg,
    WPARAM wParam,
    LPARAM lParam );

////////////////////////////////////////////////////////////////////////////////
// Camera Callback Function Prototypes
////////////////////////////////////////////////////////////////////////////////
PicamError PIL_CALL OnlineReadoutRateCalculationChanged(
    PicamHandle camera,
    PicamParameter parameter,
    piflt value );
PicamError PIL_CALL ReadoutStrideChanged(
    PicamHandle camera,
    PicamParameter parameter,
    piint value );
PicamError PIL_CALL ParameterIntegerValueChanged(
    PicamHandle camera,
    PicamParameter parameter,
    piint value );
PicamError PIL_CALL ParameterLargeIntegerValueChanged(
    PicamHandle camera,
    PicamParameter parameter,
    pi64s value );
PicamError PIL_CALL ParameterFloatingPointValueChanged(
    PicamHandle camera,
    PicamParameter parameter,
    piflt value );
PicamError PIL_CALL ParameterRoisValueChanged(
    PicamHandle camera,
    PicamParameter parameter,
    const PicamRois* value );
PicamError PIL_CALL ParameterPulseValueChanged(
    PicamHandle camera,
    PicamParameter parameter,
    const PicamPulse* value );
PicamError PIL_CALL ParameterModulationsValueChanged(
    PicamHandle camera,
    PicamParameter parameter,
    const PicamModulations* value );
PicamError PIL_CALL IsRelevantChanged(
    PicamHandle camera,
    PicamParameter parameter,
    pibln relevant );
PicamError PIL_CALL ValueAccessChanged(
    PicamHandle camera,
    PicamParameter parameter,
    PicamValueAccess access );
PicamError PIL_CALL CollectionConstraintChanged(
    PicamHandle camera,
    PicamParameter parameter,
    const PicamCollectionConstraint* constraint );
PicamError PIL_CALL RangeConstraintChanged(
    PicamHandle camera,
    PicamParameter parameter,
    const PicamRangeConstraint* constraint );
PicamError PIL_CALL RoisConstraintChanged(
    PicamHandle camera,
    PicamParameter parameter,
    const PicamRoisConstraint* constraint );
PicamError PIL_CALL PulseConstraintChanged(
    PicamHandle camera,
    PicamParameter parameter,
    const PicamPulseConstraint* constraint );
PicamError PIL_CALL ModulationsConstraintChanged(
    PicamHandle camera,
    PicamParameter parameter,
    const PicamModulationsConstraint* constraint );
PicamError PIL_CALL AcquisitionUpdated(
    PicamHandle device,
    const PicamAvailableData* available,
    const PicamAcquisitionStatus* status );

////////////////////////////////////////////////////////////////////////////////
// Miscellaneous Function Prototype
////////////////////////////////////////////////////////////////////////////////
void LogEvent( const std::wstring& message );

//##############################################################################
//##############################################################################
//##############################################################################
//##############################################################################
// State
//##############################################################################
//##############################################################################
//##############################################################################
//##############################################################################
////////////////////////////////////////////////////////////////////////////////
// Window Application State
////////////////////////////////////////////////////////////////////////////////
HINSTANCE instance_ = 0;                // - the application instance
HWND main_ = 0;                         // - the main window handle
HDC dc_ = 0;                            // - main window device context
HDC backSurface_ = 0;                   // - main window memory device context
HBITMAP bmp_ = 0;                       // - image bitmap to display
pibyte* bmpBits_ = 0;                   // - image bitmap pixel data
pi64s bitmapVersion_ = 0;               // - current version of displayed image
HACCEL accel_ = 0;                      // - the main window accelerator table
HCURSOR waitCursor_ = 0;                // - the wait cursor
piint busy_ = 0;                        // - controls the wait cursor
HCURSOR acquiringCursor_ = 0;           // - the cursor shown when acquiring
pibool acquiring_ = false;              // - controls the acquiring cursor
PicamHandle device_ = 0;                // - the selected camera (open)
std::vector<pibyte> buffer_;            // - acquisition circular buffer
pi64s calculatedBufferSize_ = 0;        // - calculated buffer size (bytes)
HWND exposure_ = 0;                     // - the exposure time dialog
HWND repetitiveGate_ = 0;               // - the repetitive gate dialog
HWND parameters_ = 0;                   // - the camera parameters dialog

////////////////////////////////////////////////////////////////////////////////
// Shared State
////////////////////////////////////////////////////////////////////////////////
HANDLE acquisitionInactive_;            // - event reset during acquisition
CRITICAL_SECTION lock_;                 // - protects all shared state below
HWND cameras_ = 0;                      // - the camera selection dialog
std::list<PicamCameraID> available_;    // - available cameras
std::list<PicamCameraID> unavailable_;  // - unavailable cameras
piint readoutStride_ = 0;               // - stride to next readout (bytes)
piint framesPerReadout_ = 0;            // - number of frames in a readout
piint frameStride_ = 0;                 // - stride to next frame (bytes)
piint frameSize_ = 0;                   // - size of frame (bytes)
CONDITION_VARIABLE imageDataAvailable_; // - signals fresh image data acquired
std::vector<pi16u> imageData_;          // - data from last frame
pi64s imageDataVersion_ = 0;            // - current version of image data
piint imageDataWidth_ = 0;              // - image data width (pixels)
piint imageDataHeight_ = 0;             // - image data height (pixels)
std::vector<pibyte>* renderedImage_ = 0;// - rendered image bitmap pixel data
pi64s renderedImageVersion_ = 0;        // - current version of rendered image


SOCKET s;
SOCKET client;
SOCKADDR_IN from;
int fromlen = sizeof(from);

//##############################################################################
//##############################################################################
//##############################################################################
//##############################################################################
// Utilities
//##############################################################################
//##############################################################################
//##############################################################################
//##############################################################################
////////////////////////////////////////////////////////////////////////////////
// AutoBusy
// - helper to control wait cursor through RAII (busy in ctor, not in dtor)
// - properly handles nesting
////////////////////////////////////////////////////////////////////////////////
class AutoBusy
{
public:
    //--------------------------------------------------------------------------
    AutoBusy() : previous_( GetCursor() ), released_( false )
    {
        ++busy_;
        if( busy_ == 1 )
            previous_ = SetCursor( waitCursor_ );
    }
    //--------------------------------------------------------------------------
    ~AutoBusy()
    { Release(); }
    //--------------------------------------------------------------------------
    void Release()
    {
        if( !released_ )
        {
            --busy_;
            if( !busy_  )
                SetCursor( previous_ );
            released_ = true;
        }
    }
    //--------------------------------------------------------------------------
private:
    AutoBusy( const AutoBusy& );            // - not implemented
    AutoBusy& operator=( const AutoBusy& ); // - not implemented
    HCURSOR previous_;
    pibool released_;
};

////////////////////////////////////////////////////////////////////////////////
// AutoLock
// - helper to control locking through RAII (acquires in ctor, releases in dtor)
////////////////////////////////////////////////////////////////////////////////
class AutoLock
{
public:
    //--------------------------------------------------------------------------
    AutoLock( CRITICAL_SECTION& lock ) : lock_( lock ), released_( false )
    { EnterCriticalSection( &lock_ ); }
    //--------------------------------------------------------------------------
    ~AutoLock()
    { Release(); }
    //--------------------------------------------------------------------------
    void Release()
    {
        if( !released_ )
        {
            LeaveCriticalSection( &lock_ );
            released_ = true;
        }
    }
    //--------------------------------------------------------------------------
private:
    AutoLock( const AutoLock& );            // - not implemented
    AutoLock& operator=( const AutoLock& ); // - not implemented
    CRITICAL_SECTION& lock_;
    pibool released_;
};

////////////////////////////////////////////////////////////////////////////////
// PicamCameraID Equality Operator
////////////////////////////////////////////////////////////////////////////////
pibool operator==( const PicamCameraID& a, const PicamCameraID& b )
{
    return
        a.model                        == b.model                        &&
        a.computer_interface           == b.computer_interface           &&
        std::string( a.serial_number ) == std::string( b.serial_number ) &&
        std::string( a.sensor_name   ) == std::string( b.sensor_name   );
}

////////////////////////////////////////////////////////////////////////////////
// GetEnumString
// - returns a wstring version of a picam enum
////////////////////////////////////////////////////////////////////////////////
std::wstring GetEnumString( PicamEnumeratedType type, piint value )
{
    const pichar* string;
    if( Picam_GetEnumerationString( type, value, &string ) == PicamError_None )
    {
        std::string s( string );
        Picam_DestroyString( string );

        std::wstring w( s.length(), L'\0' );
        std::copy( s.begin(), s.end(), w.begin() );
        return w;
    }
    return std::wstring();
}

////////////////////////////////////////////////////////////////////////////////
// DisplayError
// - displays an error (with optional picam error code) in a message box
////////////////////////////////////////////////////////////////////////////////
void DisplayError(
    const std::wstring& message,
    PicamError error = PicamError_None )
{
    std::string details( ws2s(message) );
    if( error != PicamError_None )
        details += " ("+ws2s(GetEnumString( PicamEnumeratedType_Error, error ))+")";
	string ack = "Error: ";
	ack.append(details);
	int len;
	wsmessage formatmesg;
	formatmessage(ack, len, formatmesg);
	sendmessage(formatmesg);

	std::ofstream outfile;

	outfile.open("picam.log", std::ios_base::app);
	outfile << details+"\n";
}

string ws2s(const std::wstring& wstr)
{
	typedef codecvt_utf8<wchar_t> convert_typeX;
	wstring_convert<convert_typeX, wchar_t> converterX;

	return converterX.to_bytes(wstr);
}

//##############################################################################
//##############################################################################
//##############################################################################
//##############################################################################
// Graphics
//##############################################################################
//##############################################################################
//##############################################################################
//##############################################################################
////////////////////////////////////////////////////////////////////////////////
// InitializeImage
// - clears the image data/graphics and prepares for a new acquisition
// - takes the lock
////////////////////////////////////////////////////////////////////////////////
pibool InitializeImage()
{
    // - lock before accessing shared state
    AutoLock al( lock_ );

    // - cache frame size
    PicamError error =
        Picam_GetParameterIntegerValue(
            device_,
            PicamParameter_FrameSize,
            &frameSize_ );
    if( error != PicamError_None )
    {
        DisplayError( L"Failed to get frame size.", error );
        return false;
    }

    // - size image data to fit frame
    imageData_.resize( frameSize_ / sizeof( imageData_[0] ) );
    imageDataVersion_ = 0;

    // - determine image dimensions
    const PicamRois* rois;
    error = Picam_GetParameterRoisValue( device_, PicamParameter_Rois, &rois );
    if( error != PicamError_None )
    {
        DisplayError( L"Failed to get rois.", error );
        return false;
    }
    imageDataWidth_  = rois->roi_array[0].width  / rois->roi_array[0].x_binning;
    imageDataHeight_ = rois->roi_array[0].height / rois->roi_array[0].y_binning;
    Picam_DestroyRois( rois );

    // - initialize header
    BITMAPV5HEADER header = { 0 };
    header.bV5Size        = sizeof( header );
    header.bV5Width       = imageDataWidth_;
    header.bV5Height      = -imageDataHeight_;
    header.bV5Planes      = 1;
    header.bV5BitCount    = 24;
    header.bV5Compression = BI_RGB;
    header.bV5CSType      = LCS_WINDOWS_COLOR_SPACE;
    header.bV5Intent      = LCS_GM_BUSINESS;

    // - create and select bitmap into back surface
    bmp_ =
        CreateDIBSection(
            backSurface_,
            reinterpret_cast<BITMAPINFO*>( &header ),
            DIB_RGB_COLORS,
            reinterpret_cast<void**>( &bmpBits_ ),
            0,
            0 );
    DeleteObject( SelectObject( backSurface_, bmp_ ) );
    renderedImage_ = 0;
    bitmapVersion_ = -1;

    // - redraw
    WakeConditionVariable( &imageDataAvailable_ );
    al.Release();

    return true;
}

////////////////////////////////////////////////////////////////////////////////
// GetBlackWhiteLevels
// - returns image data corresponding to thresholds for black/white pixels
////////////////////////////////////////////////////////////////////////////////
void GetBlackWhiteLevels(
    const std::vector<pi16u>& renderImageData,
    pi16u* black,
    pi16u* white )
{
    // - generate a histogram of image data intensities
    static std::vector<piint> histogram( 0x10000 );
    histogram.assign( histogram.size(), 0 );
    const piint dataPoints = static_cast<piint>( renderImageData.size() );
    for( piint i = 0; i < dataPoints; ++i )
        ++histogram[renderImageData[i]];

    // - find the start and end of the histogram
    pi16u b = 0, w = static_cast<pi16u>( histogram.size()-1 );
    while( !histogram[b] || !histogram[w] )
    {
        if( !histogram[b] )
            ++b;
        if( !histogram[w] )
            --w;
    }

    // - clip a small percentage of outlying values in histogram
    const piint outliers = static_cast<piint>( 0.01 * dataPoints );
    piint skippedBlack = 0, skippedWhite = 0;
    while( (skippedBlack < outliers || skippedWhite < outliers) && b != w )
    {
        if( skippedBlack < outliers )
            skippedBlack += histogram[b++];
        if( skippedWhite < outliers )
            skippedWhite += histogram[w--];
    }

    // - if all data are equal set all black if zero, otherwise all white
    if( b == w )
    {
        *black = b == 0x0000 ? b   : b-1;
        *white = b == 0x0000 ? b+1 : b;
        return;
    }

    *black = b;
    *white = w;
}

////////////////////////////////////////////////////////////////////////////////
// UpdateImage
// - generates bitmap data based on image data
// - takes the lock
////////////////////////////////////////////////////////////////////////////////
void UpdateImage(
    const std::vector<pi16u>& renderImageData,
    pi64s renderImageDataVersion,
    piint width,
    piint height,
    std::vector<pibyte>* renderedImage )
{
    // - resize if necessary
    const std::size_t scanlineStride = (width*sizeof( RGBTRIPLE )+3)/4*4;
    std::size_t size = scanlineStride * height;
    if( renderedImage->size() != size )
        renderedImage->resize( size );

    // - update bitmap pixels
    pibyte* start = &(*renderedImage)[0];
    if( !renderImageDataVersion )
    {
        // - indicate no image present
        const RGBTRIPLE noImageDataColor = { 0xE0, 0x00, 0x00 };
        for( piint y = 0; y < height; ++y )
        {
            RGBTRIPLE* pixel =
                reinterpret_cast<RGBTRIPLE*>( start+scanlineStride*y );
            for( piint x = 0; x < width; ++x )
                *pixel++ = noImageDataColor;
        }
    }
    else
    {
        // - determine linear interpolation black/white levels
        pi16u black = 0x0000, white = 0x0000;
        GetBlackWhiteLevels( renderImageData, &black, &white );

        // - auto-contrast pixel based on black/white levels
        piint i = 0;
        for( piint y = 0; y < height; ++y )
        {
            RGBTRIPLE* pixel =
                reinterpret_cast<RGBTRIPLE*>( start+scanlineStride*y );
            for( piint x = 0; x < width; ++x )
            {
                pi16u data = renderImageData[i++];
                pibyte intensity =
                    data < black
                        ? 0x00
                        : data > white
                            ? 0xFF
                            : static_cast<pibyte>(
                                (data-black)*0xFF/(white-black) );
                RGBTRIPLE gray = { intensity, intensity, intensity };
                *pixel++ = gray;
            }
        }
    }

    // - publish the new bitmap data and post a request to redraw
    AutoLock al( lock_ );
    renderedImage_ = renderedImage;
    renderedImageVersion_ = renderImageDataVersion;
    al.Release();
    UINT flags = RDW_INVALIDATE;
    if( !renderImageDataVersion )
        flags |= RDW_ERASE;
    RedrawWindow( main_, 0, 0, flags );
}

////////////////////////////////////////////////////////////////////////////////
// RenderThreadProc
// - generates bitmap data based on image data and redraws the window
// - takes the lock
////////////////////////////////////////////////////////////////////////////////
unsigned __stdcall RenderThreadProc( void* parameter )
{
    UNREFERENCED_PARAMETER( parameter );

    std::vector<pi16u> renderImageData;
    pi64s renderImageDataVersion = 0;
    piint renderImageDataWidth;
    piint renderImageDataHeight;
    std::vector<pibyte> renderedImageBuffer1, renderedImageBuffer2;
    std::vector<pibyte>* renderedImage = 0;

    // - run until application terminates
    for( ;; )
    {
        // - take lock before accessing shared state
        AutoLock al( lock_ );

        // - wait for new image data
        pibool imageDataChanged;
        do
        {
            imageDataChanged =
                !imageData_.empty() &&
                (!renderedImage_ ||
                 renderImageDataVersion != imageDataVersion_);
            if( !imageDataChanged )
                SleepConditionVariableCS(
                    &imageDataAvailable_,
                    &lock_,
                    INFINITE );
        } while( !imageDataChanged );

        // - resize if necessary
        if( renderImageData.size() != imageData_.size() )
            renderImageData.resize( imageData_.size() );

        // - copy the new data
        std::copy(
            imageData_.begin(),
            imageData_.end(),
            renderImageData.begin() );
        renderImageDataVersion = imageDataVersion_;
        renderImageDataWidth   = imageDataWidth_;
        renderImageDataHeight  = imageDataHeight_;

        // - render into the other buffer
        renderedImage = 
            renderedImage_ == &renderedImageBuffer1
                ? &renderedImageBuffer2
                : &renderedImageBuffer1;

        // - release lock after accessing shared state
        al.Release();

        UpdateImage(
            renderImageData,
            renderImageDataVersion,
            renderImageDataWidth,
            renderImageDataHeight,
            renderedImage );
    }
}

//##############################################################################
//##############################################################################
//##############################################################################
//##############################################################################
// Picam Handling
//##############################################################################
//##############################################################################
//##############################################################################
//##############################################################################
////////////////////////////////////////////////////////////////////////////////
// CalculateBufferSize
// - calculates a new circular buffer size given a readout stride and rate
////////////////////////////////////////////////////////////////////////////////
void CalculateBufferSize( piint readoutStride, piflt onlineReadoutRate )
{
    // - calculate a circular buffer with the following simple rules:
    //   - contain at least 3 seconds worth of readout rate
    //   - contain at least 2 readouts
    // - note this takes into account changes that affect rate online (such as
    //   exposure) by assuming worst case (fastest rate)
    pi64s readouts = static_cast<pi64s>(
        std::ceil( std::max( 3.*onlineReadoutRate, 2. ) ) );
    calculatedBufferSize_ = readoutStride * readouts;
}

////////////////////////////////////////////////////////////////////////////////
// InitializeCalculatedBufferSize
// - calculates the first buffer size for a camera just opened
////////////////////////////////////////////////////////////////////////////////
void InitializeCalculatedBufferSize()
{
    // - get the current readout rate
    // - note this accounts for rate increases in online scenarios
    piflt onlineReadoutRate;
    PicamError error =
        Picam_GetParameterFloatingPointValue(
            device_,
            PicamParameter_OnlineReadoutRateCalculation,
            &onlineReadoutRate );
    if( error != PicamError_None )
        DisplayError( L"Failed to get online readout rate.", error );

    // - get the current readout stride
    piint readoutStride;
    error =
        Picam_GetParameterIntegerValue(
            device_,
            PicamParameter_ReadoutStride,
            &readoutStride );
    if( error != PicamError_None )
        DisplayError( L"Failed to get readout stride.", error );

    // - calculate the buffer size
    CalculateBufferSize( readoutStride, onlineReadoutRate );
}

////////////////////////////////////////////////////////////////////////////////
// CacheFrameNavigation
// - caches frame navigation information to extract frames from readouts
// - takes the lock
////////////////////////////////////////////////////////////////////////////////
pibool CacheFrameNavigation()
{
    // - lock before accessing shared state
    AutoLock al( lock_ );

    // - cache the readout stride
    PicamError error =
        Picam_GetParameterIntegerValue(
            device_,
            PicamParameter_ReadoutStride,
            &readoutStride_ );
    if( error != PicamError_None )
    {
        DisplayError( L"Failed to get readout stride.", error );
        return false;
    }

    // - cache the frame stride
    error =
        Picam_GetParameterIntegerValue(
            device_,
            PicamParameter_FrameStride,
            &frameStride_ );
    if( error != PicamError_None )
    {
        DisplayError( L"Failed to get frame stride.", error );
        return false;
    }

    // - cache the frames per readout
    error =
        Picam_GetParameterIntegerValue(
            device_,
            PicamParameter_FramesPerReadout,
            &framesPerReadout_ );
    if( error != PicamError_None )
    {
        DisplayError( L"Failed to get frames per readout.", error );
        return false;
    }

    return true;
}

////////////////////////////////////////////////////////////////////////////////
// RegisterParameterValueChangedCallback
// - initializes callback for any parameter value changes from the camera model
////////////////////////////////////////////////////////////////////////////////
pibool RegisterParameterValueChangedCallback(
    PicamHandle model,
    PicamParameter parameter )
{
    // - get the value type
    PicamValueType valueType;
    PicamError error =
        Picam_GetParameterValueType( model, parameter, &valueType );
    if( error != PicamError_None )
    {
        DisplayError( L"Failed to get parameter value type.", error );
        return false;
    }

    // - register for value changes
    switch( valueType )
    {
        case PicamValueType_Integer:
        case PicamValueType_Boolean:
        case PicamValueType_Enumeration:
            error =
                PicamAdvanced_RegisterForIntegerValueChanged(
                    model,
                    parameter,
                    ParameterIntegerValueChanged );
            break;
        case PicamValueType_LargeInteger:
            error =
                PicamAdvanced_RegisterForLargeIntegerValueChanged(
                    model,
                    parameter,
                    ParameterLargeIntegerValueChanged );
            break;
        case PicamValueType_FloatingPoint:
            error =
                PicamAdvanced_RegisterForFloatingPointValueChanged(
                    model,
                    parameter,
                    ParameterFloatingPointValueChanged );
            break;
        case PicamValueType_Rois:
            error =
                PicamAdvanced_RegisterForRoisValueChanged(
                    model,
                    parameter,
                    ParameterRoisValueChanged );
            break;
        case PicamValueType_Pulse:
            error =
                PicamAdvanced_RegisterForPulseValueChanged(
                    model,
                    parameter,
                    ParameterPulseValueChanged );
            break;
        case PicamValueType_Modulations:
            error =
                PicamAdvanced_RegisterForModulationsValueChanged(
                    model,
                    parameter,
                    ParameterModulationsValueChanged );
            break;
        default:
        {
            std::wstringstream woss;
            woss << L"Unexpected value type. "
                 << L"(" << valueType << L")";
            DisplayError( woss.str() );
            return false;
        }
    }

    if( error != PicamError_None )
    {
        DisplayError( L"Failed to register for value changes.", error );
        return false;
    }

    return true;
}

////////////////////////////////////////////////////////////////////////////////
// RegisterConstraintChangedCallback
// - initializes callback for any parameter constraint changes from the camera
//   model
////////////////////////////////////////////////////////////////////////////////
pibool RegisterConstraintChangedCallback(
    PicamHandle model,
    PicamParameter parameter )
{
    // - get the constraint type
    PicamConstraintType constraintType;
    PicamError error =
        Picam_GetParameterConstraintType(
            model,
            parameter,
            &constraintType );
    if( error != PicamError_None )
    {
        DisplayError( L"Failed to get parameter constraint type.", error );
        return false;
    }

    // - register for constraint changes
    switch( constraintType )
    {
        case PicamConstraintType_None:
            error = PicamError_None;
            break;
        case PicamConstraintType_Collection:
            error =
                PicamAdvanced_RegisterForDependentCollectionConstraintChanged(
                    model,
                    parameter,
                    CollectionConstraintChanged );
            break;
        case PicamConstraintType_Range:
            error =
                PicamAdvanced_RegisterForDependentRangeConstraintChanged(
                    model,
                    parameter,
                    RangeConstraintChanged );
            break;
        case PicamConstraintType_Rois:
            error =
                PicamAdvanced_RegisterForDependentRoisConstraintChanged(
                    model,
                    parameter,
                    RoisConstraintChanged );
            break;
        case PicamConstraintType_Pulse:
            error =
                PicamAdvanced_RegisterForDependentPulseConstraintChanged(
                    model,
                    parameter,
                    PulseConstraintChanged );
            break;
        case PicamConstraintType_Modulations:
            error =
                PicamAdvanced_RegisterForDependentModulationsConstraintChanged(
                    model,
                    parameter,
                    ModulationsConstraintChanged );
            break;
        default:
        {
            std::wstringstream woss;
            woss << L"Unexpected constraint type. "
                 << L"(" << constraintType << L")";
            DisplayError( woss.str() );
            return false;
        }
    }

    if( error != PicamError_None )
    {
        DisplayError(
            L"Failed to register for constraint changes.",
            error );
        return false;
    }

    return true;
}

////////////////////////////////////////////////////////////////////////////////
// RegisterParameterCallbacks
// - initializes callbacks for any parameter changes from the model of the open
//   camera
////////////////////////////////////////////////////////////////////////////////
void RegisterParameterCallbacks()
{
    // - get the camera model
    PicamHandle model;
    PicamError error = PicamAdvanced_GetCameraModel( device_, &model );
    if( error != PicamError_None )
    {
        DisplayError( L"Failed to get camera model.", error );
        return;
    }

    // - register with each parameter
    const PicamParameter* parameters;
    piint count;
    error = Picam_GetParameters( model, &parameters, &count );
    if( error != PicamError_None )
    {
        DisplayError( L"Failed to get camera model.", error );
        return;
    }
    for( piint i = 0; i < count; ++i )
    {
        // - register for relevance changes
        error =
            PicamAdvanced_RegisterForIsRelevantChanged(
                model,
                parameters[i],
                IsRelevantChanged );
        if( error != PicamError_None )
        {
            DisplayError( L"Failed to register for relevance changes.", error );
            continue;
        }

        // - register for value access changes
        error =
            PicamAdvanced_RegisterForValueAccessChanged(
                model,
                parameters[i],
                ValueAccessChanged );
        if( error != PicamError_None )
        {
            DisplayError( L"Failed to register for access changes.", error );
            continue;
        }

        // - register for value changes
        if( !RegisterParameterValueChangedCallback( model, parameters[i] ) )
            continue;

        // - register for constraint changes
        if( !RegisterConstraintChangedCallback( model, parameters[i] ) )
            continue;
    }
    Picam_DestroyParameters( parameters );
}

////////////////////////////////////////////////////////////////////////////////
// RegisterCameraCallbacks
// - initializes callbacks from the open camera
////////////////////////////////////////////////////////////////////////////////
void RegisterCameraCallbacks()
{
    // - register online readout rate changed
    PicamError error =
        PicamAdvanced_RegisterForFloatingPointValueChanged(
            device_,
            PicamParameter_OnlineReadoutRateCalculation,
            OnlineReadoutRateCalculationChanged );
    if( error != PicamError_None )
        DisplayError(
            L"Failed to register for online readout rate changed.",
            error );

    // - register readout stride changed
    error =
        PicamAdvanced_RegisterForIntegerValueChanged(
            device_,
            PicamParameter_ReadoutStride,
            ReadoutStrideChanged );
    if( error != PicamError_None )
        DisplayError(
            L"Failed to register for readout stride changed.",
            error );

    // - register parameter changed
    RegisterParameterCallbacks();

    // - register acquisition updated
    error =
        PicamAdvanced_RegisterForAcquisitionUpdated(
            device_,
            AcquisitionUpdated );
    if( error != PicamError_None )
        DisplayError( L"Failed to register for acquisition updated.", error );
}

////////////////////////////////////////////////////////////////////////////////
// OpenCamera
// - opens the camera for use in the application, while closing the previous
////////////////////////////////////////////////////////////////////////////////
void OpenCamera( const PicamCameraID& id )
{
    // - show wait cursor while in this function
    AutoBusy ab;

    PicamError error;

    // - handle currently open camera
    if( device_ )
    {
        // - close the current camera
        error = PicamAdvanced_CloseCameraDevice( device_ );
        if( error != PicamError_None )
            DisplayError( L"Failed to close camera.", error );
    }

    // - open the newly selected camera
    error = PicamAdvanced_OpenCameraDevice( &id, &device_ );
    if( error != PicamError_None )
        DisplayError( L"Failed to open camera.", error );

    // - initialize with the open camera
    if( device_ )
    {
        RegisterCameraCallbacks();
        InitializeCalculatedBufferSize();
        InitializeImage();

        // - refresh the modeless dialogs (if open)
        if( exposure_ )
            RefreshExposureDialog( exposure_ );
        if( repetitiveGate_ )
            RefreshRepetitiveGateDialog( repetitiveGate_ );
    }
}

////////////////////////////////////////////////////////////////////////////////
// SetReadoutCount
// - sets the readout count appropriate for preview or acquire
////////////////////////////////////////////////////////////////////////////////
pibool SetReadoutCount( pibool acquire )
{
    pi64s readouts = acquire ? 1 : 0;
    PicamError error =
        Picam_SetParameterLargeIntegerValue(
            device_,
            PicamParameter_ReadoutCount,
            readouts );
    if( error != PicamError_None )
    {
        DisplayError( L"Cannot set readout count.", error );
        return false;
    }

    return true;
}

////////////////////////////////////////////////////////////////////////////////
// Start
// - starts acquisition with the selected camera
////////////////////////////////////////////////////////////////////////////////
void Start()
{
    PicamError error;

    // - determine if parameters need to be committed
    pibln committed;
    error = Picam_AreParametersCommitted( device_, &committed );
    if( error != PicamError_None )
    {
        DisplayError(
            L"Cannot determine if parameters need to be committed.",
            error );
        return;
    }

    // - commit parameters from the model to the device
    if( !committed )
    {
        PicamHandle model;
        error = PicamAdvanced_GetCameraModel( device_, &model );
        if( error != PicamError_None )
        {
            DisplayError( L"Cannot get the camera model.", error );
            return;
        }

        error = PicamAdvanced_CommitParametersToCameraDevice( model );
        if( error != PicamError_None )
        {
            DisplayError(
                L"Failed to commit the camera model parameters.",
                error );
            return;
        }
    }

    // - reallocate circular buffer if necessary
    if( calculatedBufferSize_ == 0 )
    {
        DisplayError( L"Cannot start with a circular buffer of no length." );
        return;
    }
    if( static_cast<pi64s>( buffer_.size() ) != calculatedBufferSize_ )
        buffer_.resize( calculatedBufferSize_ );

    // - get current circular buffer
    PicamAcquisitionBuffer buffer;
    error = PicamAdvanced_GetAcquisitionBuffer( device_, &buffer );
    if( error != PicamError_None )
    {
        DisplayError( L"Failed to get circular buffer.", error );
        return;
    }

    // - update circular buffer if neccessary
    if( &buffer_[0] != buffer.memory ||
        static_cast<pi64s>( buffer_.size() ) != buffer.memory_size )
    {
        buffer.memory = &buffer_[0];
        buffer.memory_size = buffer_.size();
        error = PicamAdvanced_SetAcquisitionBuffer( device_, &buffer );
        if( error != PicamError_None )
        {
            DisplayError( L"Failed to set circular buffer.", error );
            return;
        }
    }

    // - cache information used to extract frames during acquisition
	if (!CacheFrameNavigation())
	{
		DisplayError(L"Failed to cache frames.", PicamError_None);
		return;
	}

    // - initialize image data and display
	if (!InitializeImage())
	{
		DisplayError(L"Failed to initialize image.", PicamError_None);
		return;
	}

    // - mark acquisition active just before acquisition begins
    ResetEvent( acquisitionInactive_ );

    // - start
    error = Picam_StartAcquisition( device_ );
    if( error != PicamError_None )
    {
        DisplayError( L"Failed to start acquisition.", error );
        return;
    }

    // - indicate acquisition has begun
    acquiring_ = true;
    SetCursor( acquiringCursor_ );
}

////////////////////////////////////////////////////////////////////////////////
// ApplyExposureTime
// - sets the exposure time on the selected camera
////////////////////////////////////////////////////////////////////////////////
void ApplyExposureTime( piflt exposure )
{
    // - determine if acquiring
    pibln running;
    PicamError error =
        Picam_IsAcquisitionRunning( device_, &running );
    if( error != PicamError_None )
    {
        DisplayError( L"Failed to determine if acquiring.", error );
        return;
    }

    // - set the exposure time appropriately
    PicamHandle model;
    error = PicamAdvanced_GetCameraModel( device_, &model );
    if( error != PicamError_None )
    {
        DisplayError( L"Failed to get camera model.", error );
        return;
    }
    if( running )
    {
        error =
            Picam_SetParameterFloatingPointValueOnline(
                model,
                PicamParameter_ExposureTime,
                exposure );
        if( error != PicamError_None )
        {
            DisplayError( L"Failed to set exposure time online.", error );
            return;
        }
    }
    else
    {
        error =
            Picam_SetParameterFloatingPointValue(
                model,
                PicamParameter_ExposureTime,
                exposure );
        if( error != PicamError_None )
        {
            DisplayError( L"Failed to set exposure time.", error );
            return;
        }
    }
}

////////////////////////////////////////////////////////////////////////////////
// ApplyRepetitiveGate
// - sets the repetitive gate on the selected camera
////////////////////////////////////////////////////////////////////////////////
void ApplyRepetitiveGate( const PicamPulse& pulse )
{
    // - determine if acquiring
    pibln running;
    PicamError error =
        Picam_IsAcquisitionRunning( device_, &running );
    if( error != PicamError_None )
    {
        DisplayError( L"Failed to determine if acquiring.", error );
        return;
    }

    // - set the repetitive appropriately
    PicamHandle model;
    error = PicamAdvanced_GetCameraModel( device_, &model );
    if( error != PicamError_None )
    {
        DisplayError( L"Failed to get camera model.", error );
        return;
    }
    if( running )
    {
        error =
            Picam_SetParameterPulseValueOnline(
                model,
                PicamParameter_RepetitiveGate,
                &pulse );
        if( error != PicamError_None )
        {
            DisplayError( L"Failed to set repetitive gate online.", error );
            return;
        }
    }
    else
    {
        error =
            Picam_SetParameterPulseValue(
                model,
                PicamParameter_RepetitiveGate,
                &pulse );
        if( error != PicamError_None )
        {
            DisplayError( L"Failed to set repetitive gate.", error );
            return;
        }
    }
}

////////////////////////////////////////////////////////////////////////////////
// GetParameterValue
// - gets the selected camera model's parameter value as two wstrings
////////////////////////////////////////////////////////////////////////////////
pibool GetParameterValue(
    PicamParameter parameter,
    std::wstring& text,
    std::wstring& formatted )
{
    // - clear strings in case of errors
    text.clear();
    formatted.clear();

    // - get the camera model
    PicamHandle model;
    PicamError error = PicamAdvanced_GetCameraModel( device_, &model );
    if( error != PicamError_None )
    {
        DisplayError( L"Failed to get camera model.", error );
        return false;
    }

    // - get the value type
    PicamValueType valueType;
    error = Picam_GetParameterValueType( model, parameter, &valueType );
    if( error != PicamError_None )
    {
        DisplayError( L"Failed to get parameter value type.", error );
        return false;
    }

    // - get the value
    switch( valueType )
    {
        case PicamValueType_Integer:
        {
            piint value;
            error =
                Picam_GetParameterIntegerValue(
                    model,
                    parameter,
                    &value );
            if( error != PicamError_None )
            {
                DisplayError( L"Failed to get parameter value.", error );
                return false;
            }
            std::wostringstream woss;
            woss << value;
            formatted = text = woss.str();
            break;
        }
        case PicamValueType_Boolean:
        {
            piint value;
            error =
                Picam_GetParameterIntegerValue(
                    model,
                    parameter,
                    &value );
            if( error != PicamError_None )
            {
                DisplayError( L"Failed to get parameter value.", error );
                return false;
            }
            std::wostringstream woss;
            woss << value;
            text = woss.str();
            formatted = value ? L"true" : L"false";
            break;
        }
        case PicamValueType_Enumeration:
        {
            piint value;
            error =
                Picam_GetParameterIntegerValue(
                    model,
                    parameter,
                    &value );
            if( error != PicamError_None )
            {
                DisplayError( L"Failed to get parameter value.", error );
                return false;
            }
            std::wostringstream woss;
            woss << value;
            text = woss.str();
            PicamEnumeratedType enumType;
            error =
                Picam_GetParameterEnumeratedType(
                    model,
                    parameter,
                    &enumType );
            if( error != PicamError_None )
            {
                DisplayError( L"Failed to get enumerated type.", error );
                return false;
            }
            formatted = GetEnumString( enumType, value );
            break;
        }
        case PicamValueType_LargeInteger:
        {
            pi64s value;
            error =
                Picam_GetParameterLargeIntegerValue(
                    model,
                    parameter,
                    &value );
            if( error != PicamError_None )
            {
                DisplayError( L"Failed to get parameter value.", error );
                return false;
            }
            std::wostringstream woss;
            woss << value;
            formatted = text = woss.str();
            break;
        }
        case PicamValueType_FloatingPoint:
        {
            piflt value;
            error =
                Picam_GetParameterFloatingPointValue(
                    model,
                    parameter,
                    &value );
            if( error != PicamError_None )
            {
                DisplayError( L"Failed to get parameter value.", error );
                return false;
            }
            std::wostringstream woss;
            woss << value;
            formatted = text = woss.str();
            break;
        }
        case PicamValueType_Rois:
        {
            const PicamRois* value;
            error =
                Picam_GetParameterRoisValue(
                    model,
                    parameter,
                    &value );
            if( error != PicamError_None )
            {
                DisplayError( L"Failed to get parameter value.", error );
                return false;
            }
            std::wostringstream woss1;
            woss1 << value->roi_array[0].x
                  << L","
                  << value->roi_array[0].y
                  << L" "
                  << value->roi_array[0].width
                  << L","
                  << value->roi_array[0].height
                  << L" "
                  << value->roi_array[0].x_binning
                  << L","
                  << value->roi_array[0].y_binning;
            text = woss1.str();
            std::wostringstream woss2;
            woss2 << L"("
                  << value->roi_array[0].x
                  << L", "
                  << value->roi_array[0].y
                  << L") - "
                  << value->roi_array[0].width
                  << L" x "
                  << value->roi_array[0].height
                  << L" - "
                  << value->roi_array[0].x_binning
                  << L" x "
                  << value->roi_array[0].y_binning
                  << L" bin";
            formatted = woss2.str();
            Picam_DestroyRois( value );
            break;
        }
        case PicamValueType_Pulse:
        {
            const PicamPulse* value;
            error =
                Picam_GetParameterPulseValue(
                    model,
                    parameter,
                    &value );
            if( error != PicamError_None )
            {
                DisplayError( L"Failed to get parameter value.", error );
                return false;
            }
            std::wostringstream woss1;
            woss1 << value->delay
                  << L","
                  << value->width;
            text = woss1.str();
            std::wostringstream woss2;
            woss2 << L"delayed to "
                  << value->delay
                  << L" of width "
                  << value->width;
            formatted = woss2.str();
            Picam_DestroyPulses( value );
            break;
        }
        case PicamValueType_Modulations:
        {
            const PicamModulations* value;
            error =
                Picam_GetParameterModulationsValue(
                    model,
                    parameter,
                    &value );
            if( error != PicamError_None )
            {
                DisplayError( L"Failed to get parameter value.", error );
                return false;
            }
            std::wostringstream woss1;
            for( piint m = 0; m < value->modulation_count; ++m )
            {
                woss1 << value->modulation_array[m].duration
                      << L","
                      << value->modulation_array[m].frequency
                      << L","
                      << value->modulation_array[m].phase
                      << L","
                      << value->modulation_array[m].output_signal_frequency;
                if( m != value->modulation_count-1 )
                    woss1 << L" ";
            }
            text = woss1.str();
            std::wostringstream woss2;
            woss2 << L"cos("
                  << value->modulation_array[0].frequency
                  << L"t + "
                  << value->modulation_array[0].phase
                  << L"pi/180) lasting "
                  << value->modulation_array[0].duration
                  << L" with output signal cos("
                  << value->modulation_array[0].output_signal_frequency
                  << L"t)";
            if( value->modulation_count > 1 )
                woss2 << L"...";
            formatted = woss2.str();
            Picam_DestroyModulations( value );
            break;
        }
        default:
            formatted = text = L"'unknown value'";
            break;
    }

    return true;
}

////////////////////////////////////////////////////////////////////////////////
// SetParameterValue
// - sets the selected camera model's parameter value via wstring
////////////////////////////////////////////////////////////////////////////////
pibool SetParameterValue( PicamParameter parameter, const std::wstring& text )
{
    // - get the camera model
    PicamHandle model;
    PicamError error = PicamAdvanced_GetCameraModel( device_, &model );
    if( error != PicamError_None )
    {
        DisplayError( L"Failed to get camera model.", error );
        return false;
    }

    // - get the value type
    PicamValueType valueType;
    error = Picam_GetParameterValueType( model, parameter, &valueType );
    if( error != PicamError_None )
    {
        DisplayError( L"Failed to get parameter value type.", error );
        return false;
    }

    switch( valueType )
    {
        case PicamValueType_Integer:
        case PicamValueType_Boolean:
        case PicamValueType_Enumeration:
        {
            // - parse the text
            piint value;
            std::wistringstream wiss( text );
            wiss >> value >> std::ws;
            if( wiss.fail() || !wiss.eof() )
            {
                DisplayError( L"Invalid format." );
                return false;
            }

            // - set the value
            error = Picam_SetParameterIntegerValue( model, parameter, value );
            if( error != PicamError_None )
            {
                DisplayError( L"Failed to set parameter value.", error );
                return false;
            }
            break;
        }
        case PicamValueType_LargeInteger:
        {
            // - parse the text
            pi64s value;
            std::wistringstream wiss( text );
            wiss >> value >> std::ws;
            if( wiss.fail() || !wiss.eof() )
            {
                DisplayError( L"Invalid format." );
                return false;
            }

            // - set the value
            error =
                Picam_SetParameterLargeIntegerValue( model, parameter, value );
            if( error != PicamError_None )
            {
                DisplayError( L"Failed to set parameter value.", error );
                return false;
            }
            break;
        }
        case PicamValueType_FloatingPoint:
        {
            // - parse the text
            piflt value;
            std::wistringstream wiss( text );
            wiss >> value >> std::ws;
            if( wiss.fail() || !wiss.eof() )
            {
                DisplayError( L"Invalid format." );
                return false;
            }

            // - set the value
            error =
                Picam_SetParameterFloatingPointValue( model, parameter, value );
            if( error != PicamError_None )
            {
                DisplayError( L"Failed to set parameter value.", error );
                return false;
            }
            break;
        }
        case PicamValueType_Rois:
        {
            // - parse the text
            PicamRoi roi;
            wchar_t comma1, comma2, comma3;
            std::wistringstream wiss( text );
            wiss >> roi.x         >> comma1 >> roi.y
                 >> roi.width     >> comma2 >> roi.height 
                 >> roi.x_binning >> comma3 >> roi.y_binning
                 >> std::ws;
            if( wiss.fail() || !wiss.eof() ||
                comma1 != L',' || comma2 != L',' || comma3 != L',' )
            {
                DisplayError( L"Invalid format." );
                return false;
            }

            // - set the value
            PicamRois value = { &roi, 1 };
            error = Picam_SetParameterRoisValue( model, parameter, &value );
            if( error != PicamError_None )
            {
                DisplayError( L"Failed to set parameter value.", error );
                return false;
            }
            break;
        }
        case PicamValueType_Pulse:
        {
            // - parse the text
            PicamPulse value;
            wchar_t comma;
            std::wistringstream wiss( text );
            wiss >> value.delay >> comma >> value.width >> std::ws;
            if( wiss.fail() || !wiss.eof() || comma != L',' )
            {
                DisplayError( L"Invalid format." );
                return false;
            }

            // - set the value
            error = Picam_SetParameterPulseValue( model, parameter, &value );
            if( error != PicamError_None )
            {
                DisplayError( L"Failed to set parameter value.", error );
                return false;
            }
            break;
        }
        case PicamValueType_Modulations:
        {
            // - parse the text
            std::vector<PicamModulation> modulations;
            std::wistringstream wiss( text );
            do
            {
                PicamModulation modulation;
                wchar_t comma1, comma2, comma3;
                wiss >> modulation.duration  >> comma1
                     >> modulation.frequency >> comma2
                     >> modulation.phase     >> comma3
                     >> modulation.output_signal_frequency
                     >> std::ws;
                if( wiss.fail() ||
                    comma1 != L',' || comma2 != L',' || comma3 != L',' )
                {
                    DisplayError( L"Invalid format." );
                    return false;
                }
                modulations.push_back( modulation );
            }
            while( !wiss.eof() );

            // - set the value
            PicamModulations value =
            {
                &modulations[0],
                static_cast<piint>( modulations.size() )
            };
            error =
                Picam_SetParameterModulationsValue( model, parameter, &value );
            if( error != PicamError_None )
            {
                DisplayError( L"Failed to set parameter value.", error );
                return false;
            }
            break;
        }
        default:
        {
            std::wostringstream woss;
            woss << L"Failed to parse parameter type. "
                 << L"(" << valueType << L")";
            DisplayError( woss.str() );
            return false;
        }
    }

    return true;
}

//##############################################################################
//##############################################################################
//##############################################################################
//##############################################################################
// Picam Callbacks
//##############################################################################
//##############################################################################
//##############################################################################
//##############################################################################
////////////////////////////////////////////////////////////////////////////////
// CameraDiscovered
// - called when a camera becomes available or unavailable due to:
//   - connected/disconnected (including demo cameras)
//   - opened/closed in another process
// - called asynchronously on other threads
// - multiple, simulaneous callbacks are possible
// - takes the lock
////////////////////////////////////////////////////////////////////////////////
PicamError PIL_CALL CameraDiscovered(
    const PicamCameraID* id,
    PicamHandle device,
    PicamDiscoveryAction action )
{
    UNREFERENCED_PARAMETER( device );

    // - update available/unavailable lists based on lost/found
    // - refresh dialog if currently open
    switch( action )
    {
        case PicamDiscoveryAction_Found:
        {
            AutoLock al( lock_ );
            unavailable_.remove( *id );
            pibool absent =
                std::find( available_.begin(), available_.end(), *id ) ==
                    available_.end();
            if( absent )
                available_.push_back( *id );
            if( cameras_ )
                PostMessage( cameras_, WM_REFRESH_CAMERAS, 0, 0 );
            break;
        }
        case PicamDiscoveryAction_Lost:
        {
            AutoLock al( lock_ );
            available_.remove( *id );
            pibool absent =
                std::find( unavailable_.begin(), unavailable_.end(), *id ) ==
                    unavailable_.end();
            if( absent )
                unavailable_.push_back( *id );
            if( cameras_ )
                PostMessage( cameras_, WM_REFRESH_CAMERAS, 0, 0 );
            break;
        }
        default:
        {
            std::wostringstream woss;
            woss << L"Received unexpected discovery action. "
                 << L"(" << static_cast<piint>( action ) << L")";
            PostMessage(
                main_,
                WM_DISPLAY_ERROR,
                reinterpret_cast<WPARAM>( new std::wstring( woss.str() ) ),
                0 );
            break;
        }
    }

    return PicamError_None;
}

////////////////////////////////////////////////////////////////////////////////
// ReadoutRateChanged
// - called when the online readout rate changes due to another parameter change
// - called on the same thread that changed the other parameter (in this case
//   all SetParameter calls will be made on the main thread)
////////////////////////////////////////////////////////////////////////////////
PicamError PIL_CALL OnlineReadoutRateCalculationChanged(
    PicamHandle camera,
    PicamParameter parameter,
    piflt value )
{
    UNREFERENCED_PARAMETER( parameter );

    piint readoutStride;
    PicamError error =
        Picam_GetParameterIntegerValue(
            camera,
            PicamParameter_ReadoutStride,
            &readoutStride );
    if( error != PicamError_None )
    {
        DisplayError( L"Failed to get readout stride.", error );
        return PicamError_None;
    }

    CalculateBufferSize( readoutStride, value );

    return PicamError_None;
}

////////////////////////////////////////////////////////////////////////////////
// ReadoutStrideChanged
// - called when the readout stride changes due to another parameter change
// - called on the same thread that changed the other parameter (in this case
//   all SetParameter calls will be made on the main thread)
////////////////////////////////////////////////////////////////////////////////
PicamError PIL_CALL ReadoutStrideChanged(
    PicamHandle camera,
    PicamParameter parameter,
    piint value )
{
    UNREFERENCED_PARAMETER( parameter );

    piflt onlineReadoutRate;
    PicamError error =
        Picam_GetParameterFloatingPointValue(
            camera,
            PicamParameter_OnlineReadoutRateCalculation,
            &onlineReadoutRate );
    if( error != PicamError_None )
    {
        DisplayError( L"Failed to get online readout rate.", error );
        return PicamError_None;
    }

    CalculateBufferSize( value, onlineReadoutRate );

    return PicamError_None;
}

////////////////////////////////////////////////////////////////////////////////
// ParameterIntegerValueChanged
// - called when an integer parameter changes due to another parameter change
// - called on the same thread that changed the other parameter (in this case
//   all SetParameter calls will be made on the main thread)
////////////////////////////////////////////////////////////////////////////////
PicamError PIL_CALL ParameterIntegerValueChanged(
    PicamHandle camera,
    PicamParameter parameter,
    piint value )
{
    // - do nothing if parameters dialog is not open
    if( !parameters_ )
        return PicamError_None;

    // - get the value type
    PicamValueType valueType;
    PicamError error =
        Picam_GetParameterValueType( camera, parameter, &valueType );
    if( error != PicamError_None )
    {
        DisplayError( L"Failed to get parameter value type.", error );
        return PicamError_None;
    }

    // - generate log message
    std::wstring message =
        GetEnumString( PicamEnumeratedType_Parameter, parameter ) +
        L" value changed to ";
    switch( valueType )
    {
        case PicamValueType_Integer:
        {
            std::wostringstream woss;
            woss << value;
            message += woss.str();
            break;
        }
        case PicamValueType_Boolean:
            message += value ? L"true" : L"false";
            break;
        case PicamValueType_Enumeration:
        {
            PicamEnumeratedType enumType;
            error =
                Picam_GetParameterEnumeratedType(
                    camera,
                    parameter,
                    &enumType );
            if( error != PicamError_None )
            {
                DisplayError( L"Failed to get enumerated type.", error );
                return PicamError_None;
            }
            message += GetEnumString( enumType, value );
            break;
        }
        default:
        {
            std::wostringstream woss;
            woss << value << L" (unknown value type " << valueType << L")";
            message += woss.str();
            break;
        }
    }

    LogEvent( message );

    return PicamError_None;
}

////////////////////////////////////////////////////////////////////////////////
// ParameterLargeIntegerValueChanged
// - called when a large integer parameter changes due to another parameter
//   change
// - called on the same thread that changed the other parameter (in this case
//   all SetParameter calls will be made on the main thread)
////////////////////////////////////////////////////////////////////////////////
PicamError PIL_CALL ParameterLargeIntegerValueChanged(
    PicamHandle camera,
    PicamParameter parameter,
    pi64s value )
{
    UNREFERENCED_PARAMETER( camera );

    // - do nothing if parameters dialog is not open
    if( !parameters_ )
        return PicamError_None;

    // - generate log message
    std::wstring message =
        GetEnumString( PicamEnumeratedType_Parameter, parameter ) +
        L" value changed to ";
    std::wostringstream woss;
    woss << value;
    message += woss.str();

    LogEvent( message );

    return PicamError_None;
}

////////////////////////////////////////////////////////////////////////////////
// ParameterFloatingPointValueChanged
// - called when a floating point parameter changes due to another parameter
//   change
// - called on the same thread that changed the other parameter (in this case
//   all SetParameter calls will be made on the main thread)
////////////////////////////////////////////////////////////////////////////////
PicamError PIL_CALL ParameterFloatingPointValueChanged(
    PicamHandle camera,
    PicamParameter parameter,
    piflt value )
{
    UNREFERENCED_PARAMETER( camera );

    // - do nothing if parameters dialog is not open
    if( !parameters_ )
        return PicamError_None;

    // - generate log message
    std::wstring message =
        GetEnumString( PicamEnumeratedType_Parameter, parameter ) +
        L" value changed to ";
    std::wostringstream woss;
    woss << value;
    message += woss.str();

    LogEvent( message );

    return PicamError_None;
}

////////////////////////////////////////////////////////////////////////////////
// ParameterRoisValueChanged
// - called when a rois parameter changes due to another parameter change
// - called on the same thread that changed the other parameter (in this case
//   all SetParameter calls will be made on the main thread)
////////////////////////////////////////////////////////////////////////////////
PicamError PIL_CALL ParameterRoisValueChanged(
    PicamHandle camera,
    PicamParameter parameter,
    const PicamRois* value )
{
    UNREFERENCED_PARAMETER( camera );

    // - do nothing if parameters dialog is not open
    if( !parameters_ )
        return PicamError_None;

    // - generate log message
    std::wstring message =
        GetEnumString( PicamEnumeratedType_Parameter, parameter ) +
        L" value changed to ";
    std::wostringstream woss;
    woss << L"("
         << value->roi_array[0].x
         << L", "
         << value->roi_array[0].y
         << L") - "
         << value->roi_array[0].width
         << L" x "
         << value->roi_array[0].height
         << L" - "
         << value->roi_array[0].x_binning
         << L" x "
         << value->roi_array[0].y_binning
         << L" bin";
    message += woss.str();

    LogEvent( message );

    return PicamError_None;
}

////////////////////////////////////////////////////////////////////////////////
// ParameterPulseValueChanged
// - called when a pulse parameter changes due to another parameter change
// - called on the same thread that changed the other parameter (in this case
//   all SetParameter calls will be made on the main thread)
////////////////////////////////////////////////////////////////////////////////
PicamError PIL_CALL ParameterPulseValueChanged(
    PicamHandle camera,
    PicamParameter parameter,
    const PicamPulse* value )
{
    UNREFERENCED_PARAMETER( camera );

    // - do nothing if parameters dialog is not open
    if( !parameters_ )
        return PicamError_None;

    // - generate log message
    std::wstring message =
        GetEnumString( PicamEnumeratedType_Parameter, parameter ) +
        L" value changed to ";
    std::wostringstream woss;
    woss << L"delayed to "
         << value->delay
         << L" of width "
         << value->width;
    message += woss.str();

    LogEvent( message );

    return PicamError_None;
}

////////////////////////////////////////////////////////////////////////////////
// ParameterModulationsValueChanged
// - called when a modulations parameter changes due to another parameter change
// - called on the same thread that changed the other parameter (in this case
//   all SetParameter calls will be made on the main thread)
////////////////////////////////////////////////////////////////////////////////
PicamError PIL_CALL ParameterModulationsValueChanged(
    PicamHandle camera,
    PicamParameter parameter,
    const PicamModulations* value )
{
    UNREFERENCED_PARAMETER( camera );

    // - do nothing if parameters dialog is not open
    if( !parameters_ )
        return PicamError_None;

    // - generate log message
    std::wstring message =
        GetEnumString( PicamEnumeratedType_Parameter, parameter ) +
        L" value changed to:\r\n";
    std::wostringstream woss;
    for( piint m = 0; m < value->modulation_count; ++m )
    {
        woss << L"\tcos("
             << value->modulation_array[m].frequency
             << L"t + "
             << value->modulation_array[m].phase
             << L"pi/180) lasting "
             << value->modulation_array[m].duration
             << L" with output signal cos("
             << value->modulation_array[m].output_signal_frequency
             << L"t)";
        if( m != value->modulation_count-1 )
            woss << L"\r\n";
    }
    message += woss.str();

    LogEvent( message );

    return PicamError_None;
}

////////////////////////////////////////////////////////////////////////////////
// IsRelevantChanged
// - called when the relevance of a parameter changes due to another parameter
//   change
// - called on the same thread that changed the other parameter (in this case
//   all SetParameter calls will be made on the main thread)
////////////////////////////////////////////////////////////////////////////////
PicamError PIL_CALL IsRelevantChanged(
    PicamHandle camera,
    PicamParameter parameter,
    pibln relevant )
{
    UNREFERENCED_PARAMETER( camera );

    // - do nothing if parameters dialog is not open
    if( !parameters_ )
        return PicamError_None;

    // - generate log message
    std::wstring message =
        GetEnumString( PicamEnumeratedType_Parameter, parameter ) +
        L" relevance changed to ";
    message += relevant ? L"true" : L"false";

    LogEvent( message );

    return PicamError_None;
}

////////////////////////////////////////////////////////////////////////////////
// ValueAccessChanged
// - called when the value access of a parameter changes due to another
//   parameter change
// - called on the same thread that changed the other parameter (in this case
//   all SetParameter calls will be made on the main thread)
////////////////////////////////////////////////////////////////////////////////
PicamError PIL_CALL ValueAccessChanged(
    PicamHandle camera,
    PicamParameter parameter,
    PicamValueAccess access )
{
    UNREFERENCED_PARAMETER( camera );

    // - do nothing if parameters dialog is not open
    if( !parameters_ )
        return PicamError_None;

    // - generate log message
    std::wstring message =
        GetEnumString( PicamEnumeratedType_Parameter, parameter ) +
        L" value access changed to ";
    message += GetEnumString( PicamEnumeratedType_ValueAccess, access );

    LogEvent( message );

    return PicamError_None;
}

////////////////////////////////////////////////////////////////////////////////
// CollectionConstraintChanged
// - called when a collection constraint of a parameter changes due to another
//   parameter change
// - called on the same thread that changed the other parameter (in this case
//   all SetParameter calls will be made on the main thread)
////////////////////////////////////////////////////////////////////////////////
PicamError PIL_CALL CollectionConstraintChanged(
    PicamHandle camera,
    PicamParameter parameter,
    const PicamCollectionConstraint* constraint )
{
    // - do nothing if parameters dialog is not open
    if( !parameters_ )
        return PicamError_None;

    // - get the value type
    PicamValueType valueType;
    PicamError error =
        Picam_GetParameterValueType( camera, parameter, &valueType );
    if( error != PicamError_None )
    {
        DisplayError( L"Failed to get parameter value type.", error );
        return PicamError_None;
    }

    // - generate log message
    std::wostringstream woss;
    woss << GetEnumString( PicamEnumeratedType_Parameter, parameter )
         << L" collection constraint changed to:\r\n";
    if( !constraint->values_count )
        woss << L"\t<empty set>";
    else
    {
        woss << L"\t" << constraint->values_count << L" Value(s):";
        for( piint i = 0; i < constraint->values_count; ++i )
        {
            woss << L"\r\n\t\t";
            switch( valueType )
            {
                case PicamValueType_Integer:
                    woss << static_cast<piint>( constraint->values_array[i] );
                    break;
                case PicamValueType_Boolean:
                    woss << (constraint->values_array[i] ? L"true" : L"false");
                    break;
                case PicamValueType_Enumeration:
                {
                    PicamEnumeratedType enumType;
                    error =
                        Picam_GetParameterEnumeratedType(
                            camera,
                            parameter,
                            &enumType );
                    if( error != PicamError_None )
                    {
                        DisplayError(
                            L"Failed to get enumerated type.",
                            error );
                        return PicamError_None;
                    }
                    woss <<
                        GetEnumString(
                            enumType,
                            static_cast<piint>( constraint->values_array[i] ) );
                    break;
                }
                case PicamValueType_LargeInteger:
                    woss << static_cast<pi64s>( constraint->values_array[i] );
                    break;
                case PicamValueType_FloatingPoint:
                    woss << constraint->values_array[i];
                    break;
                default:
                    woss << constraint->values_array[i]
                         << L" (unknown value type " << valueType << L")";
                    break;
            }
        }
    }

    LogEvent( woss.str() );

    return PicamError_None;
}

////////////////////////////////////////////////////////////////////////////////
// RangeConstraintChanged
// - called when a range constraint of a parameter changes due to another
//   parameter change
// - called on the same thread that changed the other parameter (in this case
//   all SetParameter calls will be made on the main thread)
////////////////////////////////////////////////////////////////////////////////
PicamError PIL_CALL RangeConstraintChanged(
    PicamHandle camera,
    PicamParameter parameter,
    const PicamRangeConstraint* constraint )
{
    // - do nothing if parameters dialog is not open
    if( !parameters_ )
        return PicamError_None;

    // - get the value type
    PicamValueType valueType;
    PicamError error =
        Picam_GetParameterValueType( camera, parameter, &valueType );
    if( error != PicamError_None )
    {
        DisplayError( L"Failed to get parameter value type.", error );
        return PicamError_None;
    }

    // - generate log message
    std::wostringstream woss;
    woss << GetEnumString( PicamEnumeratedType_Parameter, parameter )
         << L" range constraint changed to:\r\n";
    if( constraint->empty_set )
        woss << L"\t<empty set>";
    else
    {
        switch( valueType )
        {
            case PicamValueType_Integer:
                woss << L"\tMinimum: "
                     << static_cast<piint>( constraint->minimum ) << L"\r\n";
                woss << L"\tMaximum: "
                     << static_cast<piint>( constraint->maximum ) << L"\r\n";
                woss << L"\tIncrement: "
                     << static_cast<piint>( constraint->increment );
                if( constraint->outlying_values_count )
                {
                    woss << L"\r\n\tIncluding "
                         << constraint->outlying_values_count << L" Value(s):";
                    for( piint i = 0;
                         i < constraint->outlying_values_count;
                         ++i )
                    {
                        woss << L"\r\n\t\t"
                             << static_cast<piint>(
                                constraint->outlying_values_array[i] );
                    }
                }
                if( constraint->excluded_values_count )
                {
                    woss << L"\r\n\tExcluding "
                         << constraint->excluded_values_count << L" Value(s):";
                    for( piint i = 0;
                         i < constraint->excluded_values_count;
                         ++i )
                    {
                        woss << L"\r\n\t\t"
                             << static_cast<piint>(
                                constraint->excluded_values_array[i] );
                    }
                }
                break;
            case PicamValueType_LargeInteger:
                woss << L"\tMinimum: "
                     << static_cast<pi64s>( constraint->minimum ) << L"\r\n";
                woss << L"\tMaximum: "
                     << static_cast<pi64s>( constraint->maximum ) << L"\r\n";
                woss << L"\tIncrement: "
                     << static_cast<pi64s>( constraint->increment );
                if( constraint->outlying_values_count )
                {
                    woss << L"\r\n\tIncluding "
                         << constraint->outlying_values_count << L" Value(s):";
                    for( piint i = 0;
                         i < constraint->outlying_values_count;
                         ++i )
                    {
                        woss << L"\r\n\t\t"
                             << static_cast<pi64s>(
                                constraint->outlying_values_array[i] );
                    }
                }
                if( constraint->excluded_values_count )
                {
                    woss << L"\r\n\tExcluding "
                         << constraint->excluded_values_count << L" Value(s):";
                    for( piint i = 0;
                         i < constraint->excluded_values_count;
                         ++i )
                    {
                        woss << L"\r\n\t\t"
                             << static_cast<pi64s>(
                                constraint->excluded_values_array[i] );
                    }
                }
                break;
            case PicamValueType_FloatingPoint:
                woss << L"\tMinimum: " << constraint->minimum << L"\r\n";
                woss << L"\tMaximum: " << constraint->maximum << L"\r\n";
                woss << L"\tIncrement: " << constraint->increment;
                if( constraint->outlying_values_count )
                {
                    woss << L"\r\n\tIncluding "
                         << constraint->outlying_values_count << L" Value(s):";
                    for( piint i = 0;
                         i < constraint->outlying_values_count;
                         ++i )
                    {
                        woss << L"\r\n\t\t"
                             << constraint->outlying_values_array[i];
                    }
                }
                if( constraint->excluded_values_count )
                {
                    woss << L"\r\n\tExcluding "
                         << constraint->excluded_values_count << L" Value(s):";
                    for( piint i = 0;
                         i < constraint->excluded_values_count;
                         ++i )
                    {
                        woss << L"\r\n\t\t"
                             << constraint->excluded_values_array[i];
                    }
                }
                break;
            default:
                woss << L"\tMinimum: "
                     << constraint->minimum 
                     << L" (unknown value type " << valueType << L")\r\n";
                woss << L"\tMaximum: "
                     << constraint->maximum
                     << L" (unknown value type " << valueType << L")\r\n";
                woss << L"\tIncrement: "
                     << constraint->increment
                     << L" (unknown value type " << valueType << L")";
                if( constraint->outlying_values_count )
                {
                    woss << L"\r\n\tIncluding "
                         << constraint->outlying_values_count << L" Value(s):";
                    for( piint i = 0;
                         i < constraint->outlying_values_count;
                         ++i )
                    {
                        woss << L"\r\n\t\t"
                             << constraint->outlying_values_array[i]
                             << L" (unknown value type " << valueType << L")";
                    }
                }
                if( constraint->excluded_values_count )
                {
                    woss << L"\r\n\tExcluding "
                         << constraint->excluded_values_count << L" Value(s):";
                    for( piint i = 0;
                         i < constraint->excluded_values_count;
                         ++i )
                    {
                        woss << L"\r\n\t\t"
                             << constraint->excluded_values_array[i]
                             << L" (unknown value type " << valueType << L")";
                    }
                }
                break;
        }
    }

    LogEvent( woss.str() );

    return PicamError_None;
}

////////////////////////////////////////////////////////////////////////////////
// RoisConstraintChanged
// - called when a rois constraint of a parameter changes due to another
//   parameter change
// - called on the same thread that changed the other parameter (in this case
//   all SetParameter calls will be made on the main thread)
////////////////////////////////////////////////////////////////////////////////
PicamError PIL_CALL RoisConstraintChanged(
    PicamHandle camera,
    PicamParameter parameter,
    const PicamRoisConstraint* constraint )
{
    UNREFERENCED_PARAMETER( camera );

    // - do nothing if parameters dialog is not open
    if( !parameters_ )
        return PicamError_None;

    // - generate log message
    std::wostringstream woss;
    woss << GetEnumString( PicamEnumeratedType_Parameter, parameter )
         << L" rois constraint changed to:\r\n";
    if( constraint->empty_set )
        woss << L"\t<empty set>";
    else
    {
        // - generate maximum count message
        woss << L"\tMaximum Count: "
             << constraint->maximum_roi_count << L"\r\n";

        // - generate rois rules message
        woss << L"\tRules: "
             << GetEnumString(
                    PicamEnumeratedType_RoisConstraintRulesMask,
                    constraint->rules )
             << L"\r\n";

        // - generate x constraint message
        woss << L"\tX Constraint:\r\n";
        woss << L"\t\tMinimum: "
             << static_cast<piint>( constraint->x_constraint.minimum )
             << L"\r\n";
        woss << L"\t\tMaximum: "
             << static_cast<piint>( constraint->x_constraint.maximum )
             << L"\r\n";
        woss << L"\t\tIncrement: "
             << static_cast<piint>( constraint->x_constraint.increment );
        if( constraint->x_constraint.outlying_values_count )
        {
            woss << L"\r\n\t\tIncluding "
                 << constraint->x_constraint.outlying_values_count
                 << L" Value(s):";
            for( piint i = 0;
                 i < constraint->x_constraint.outlying_values_count;
                 ++i )
            {
                woss << L"\r\n\t\t\t"
                     << static_cast<piint>(
                        constraint->x_constraint.outlying_values_array[i] );
            }
        }
        if( constraint->x_constraint.excluded_values_count )
        {
            woss << L"\r\n\t\tExcluding "
                 << constraint->x_constraint.excluded_values_count
                 << L" Value(s):";
            for( piint i = 0;
                 i < constraint->x_constraint.excluded_values_count;
                 ++i )
            {
                woss << L"\r\n\t\t\t"
                     << static_cast<piint>(
                        constraint->x_constraint.excluded_values_array[i] );
            }
        }

        // - generate y constraint message
        woss << L"\r\n\tY Constraint:\r\n";
        woss << L"\t\tMinimum: "
             << static_cast<piint>( constraint->y_constraint.minimum )
             << L"\r\n";
        woss << L"\t\tMaximum: "
             << static_cast<piint>( constraint->y_constraint.maximum )
             << L"\r\n";
        woss << L"\t\tIncrement: "
             << static_cast<piint>( constraint->y_constraint.increment );
        if( constraint->y_constraint.outlying_values_count )
        {
            woss << L"\r\n\t\tIncluding "
                 << constraint->y_constraint.outlying_values_count
                 << L" Value(s):";
            for( piint i = 0;
                 i < constraint->y_constraint.outlying_values_count;
                 ++i )
            {
                woss << L"\r\n\t\t\t"
                     << static_cast<piint>(
                        constraint->y_constraint.outlying_values_array[i] );
            }
        }
        if( constraint->y_constraint.excluded_values_count )
        {
            woss << L"\r\n\t\tExcluding "
                 << constraint->y_constraint.excluded_values_count
                 << L" Value(s):";
            for( piint i = 0;
                 i < constraint->y_constraint.excluded_values_count;
                 ++i )
            {
                woss << L"\r\n\t\t\t"
                     << static_cast<piint>(
                        constraint->y_constraint.excluded_values_array[i] );
            }
        }

        // - generate width constraint message
        woss << L"\r\n\tWidth Constraint:\r\n";
        woss << L"\t\tMinimum: "
             << static_cast<piint>( constraint->width_constraint.minimum )
             << L"\r\n";
        woss << L"\t\tMaximum: "
             << static_cast<piint>( constraint->width_constraint.maximum )
             << L"\r\n";
        woss << L"\t\tIncrement: "
             << static_cast<piint>( constraint->width_constraint.increment );
        if( constraint->width_constraint.outlying_values_count )
        {
            woss << L"\r\n\t\tIncluding "
                 << constraint->width_constraint.outlying_values_count
                 << L" Value(s):";
            for( piint i = 0;
                 i < constraint->width_constraint.outlying_values_count;
                 ++i )
            {
                woss << L"\r\n\t\t\t"
                     << static_cast<piint>(
                        constraint->width_constraint.outlying_values_array[i] );
            }
        }
        if( constraint->width_constraint.excluded_values_count )
        {
            woss << L"\r\n\t\tExcluding "
                 << constraint->width_constraint.excluded_values_count
                 << L" Value(s):";
            for( piint i = 0;
                 i < constraint->width_constraint.excluded_values_count;
                 ++i )
            {
                woss << L"\r\n\t\t\t"
                     << static_cast<piint>(
                        constraint->width_constraint.excluded_values_array[i] );
            }
        }

        // - generate height constraint message
        woss << L"\r\n\tHeight Constraint:\r\n";
        woss << L"\t\tMinimum: "
             << static_cast<piint>( constraint->height_constraint.minimum )
             << L"\r\n";
        woss << L"\t\tMaximum: "
             << static_cast<piint>( constraint->height_constraint.maximum )
             << L"\r\n";
        woss << L"\t\tIncrement: "
             << static_cast<piint>( constraint->height_constraint.increment );
        if( constraint->height_constraint.outlying_values_count )
        {
            woss << L"\r\n\t\tIncluding "
                 << constraint->height_constraint.outlying_values_count
                 << L" Value(s):";
            for( piint i = 0;
                 i < constraint->height_constraint.outlying_values_count;
                 ++i )
            {
                woss << L"\r\n\t\t\t"
                     << static_cast<piint>(
                        constraint->height_constraint.outlying_values_array[i] );
            }
        }
        if( constraint->height_constraint.excluded_values_count )
        {
            woss << L"\r\n\t\tExcluding "
                 << constraint->height_constraint.excluded_values_count
                 << L" Value(s):";
            for( piint i = 0;
                 i < constraint->height_constraint.excluded_values_count;
                 ++i )
            {
                woss << L"\r\n\t\t\t"
                     << static_cast<piint>(
                        constraint->height_constraint.excluded_values_array[i] );
            }
        }

        // - generate x-binning constraint message
        if( constraint->x_binning_limits_count )
        {
            woss << L"\r\n\tX-Binning Limitted to "
                 << constraint->x_binning_limits_count << L" Value(s):";
            for( piint i = 0; i < constraint->x_binning_limits_count; ++i )
                woss << L"\r\n\t\t" << constraint->x_binning_limits_array[i];
        }

        // - generate y-binning constraint message
        if( constraint->y_binning_limits_count )
        {
            woss << L"\r\n\tY-Binning Limitted to "
                 << constraint->y_binning_limits_count << L" Value(s):";
            for( piint i = 0; i < constraint->y_binning_limits_count; ++i )
                woss << L"\r\n\t\t" << constraint->y_binning_limits_array[i];
        }
    }

    LogEvent( woss.str() );

    return PicamError_None;
}

////////////////////////////////////////////////////////////////////////////////
// PulseConstraintChanged
// - called when a pulse constraint of a parameter changes due to another
//   parameter change
// - called on the same thread that changed the other parameter (in this case
//   all SetParameter calls will be made on the main thread)
////////////////////////////////////////////////////////////////////////////////
PicamError PIL_CALL PulseConstraintChanged(
    PicamHandle camera,
    PicamParameter parameter,
    const PicamPulseConstraint* constraint )
{
    UNREFERENCED_PARAMETER( camera );

    // - do nothing if parameters dialog is not open
    if( !parameters_ )
        return PicamError_None;

    // - generate log message
    std::wostringstream woss;
    woss << GetEnumString( PicamEnumeratedType_Parameter, parameter )
         << L" pulse constraint changed to:\r\n";
    if( constraint->empty_set )
        woss << L"\t<empty set>";
    else
    {
        // - generate minimum duration message
        woss << L"\tMinimum Duration: "
             << constraint->minimum_duration << L"\r\n";

        // - generate maximum duration message
        woss << L"\tMaximum Duration: "
             << constraint->maximum_duration << L"\r\n";

        // - generate delay constraint message
        woss << L"\tDelay Constraint:\r\n";
        woss << L"\t\tMinimum: "
             << constraint->delay_constraint.minimum
             << L"\r\n";
        woss << L"\t\tMaximum: "
             << constraint->delay_constraint.maximum
             << L"\r\n";
        woss << L"\t\tIncrement: "
             << constraint->delay_constraint.increment;
        if( constraint->delay_constraint.outlying_values_count )
        {
            woss << L"\r\n\t\tIncluding "
                 << constraint->delay_constraint.outlying_values_count
                 << L" Value(s):";
            for( piint i = 0;
                 i < constraint->delay_constraint.outlying_values_count;
                 ++i )
            {
                woss << L"\r\n\t\t\t"
                     << constraint->delay_constraint.outlying_values_array[i];
            }
        }
        if( constraint->delay_constraint.excluded_values_count )
        {
            woss << L"\r\n\t\tExcluding "
                 << constraint->delay_constraint.excluded_values_count
                 << L" Value(s):";
            for( piint i = 0;
                 i < constraint->delay_constraint.excluded_values_count;
                 ++i )
            {
                woss << L"\r\n\t\t\t"
                     << constraint->delay_constraint.excluded_values_array[i];
            }
        }

        // - generate width constraint message
        woss << L"\r\n\tWidth Constraint:\r\n";
        woss << L"\t\tMinimum: "
             << constraint->width_constraint.minimum
             << L"\r\n";
        woss << L"\t\tMaximum: "
             << constraint->width_constraint.maximum
             << L"\r\n";
        woss << L"\t\tIncrement: "
             << constraint->width_constraint.increment;
        if( constraint->width_constraint.outlying_values_count )
        {
            woss << L"\r\n\t\tIncluding "
                 << constraint->width_constraint.outlying_values_count
                 << L" Value(s):";
            for( piint i = 0;
                 i < constraint->width_constraint.outlying_values_count;
                 ++i )
            {
                woss << L"\r\n\t\t\t"
                     << constraint->width_constraint.outlying_values_array[i];
            }
        }
        if( constraint->width_constraint.excluded_values_count )
        {
            woss << L"\r\n\t\tExcluding "
                 << constraint->width_constraint.excluded_values_count
                 << L" Value(s):";
            for( piint i = 0;
                 i < constraint->width_constraint.excluded_values_count;
                 ++i )
            {
                woss << L"\r\n\t\t\t"
                     << constraint->width_constraint.excluded_values_array[i];
            }
        }
    }

    LogEvent( woss.str() );

    return PicamError_None;
}

////////////////////////////////////////////////////////////////////////////////
// ModulationsConstraintChanged
// - called when a modulations constraint of a parameter changes due to another
//   parameter change
// - called on the same thread that changed the other parameter (in this case
//   all SetParameter calls will be made on the main thread)
////////////////////////////////////////////////////////////////////////////////
PicamError PIL_CALL ModulationsConstraintChanged(
    PicamHandle camera,
    PicamParameter parameter,
    const PicamModulationsConstraint* constraint )
{
    UNREFERENCED_PARAMETER( camera );

    // - do nothing if parameters dialog is not open
    if( !parameters_ )
        return PicamError_None;

    // - generate log message
    std::wostringstream woss;
    woss << GetEnumString( PicamEnumeratedType_Parameter, parameter )
         << L" modulations constraint changed to:\r\n";
    if( constraint->empty_set )
        woss << L"\t<empty set>";
    else
    {
        // - generate maximum count message
        woss << L"\tMaximum Count: "
             << constraint->maximum_modulation_count << L"\r\n";

        // - generate duration constraint message
        woss << L"\tDuration Constraint:\r\n";
        woss << L"\t\tMinimum: "
             << constraint->duration_constraint.minimum
             << L"\r\n";
        woss << L"\t\tMaximum: "
             << constraint->duration_constraint.maximum
             << L"\r\n";
        woss << L"\t\tIncrement: "
             << constraint->duration_constraint.increment;
        if( constraint->duration_constraint.outlying_values_count )
        {
            woss << L"\r\n\t\tIncluding "
                 << constraint->duration_constraint.outlying_values_count
                 << L" Value(s):";
            for( piint i = 0;
                 i < constraint->duration_constraint.outlying_values_count;
                 ++i )
            {
                woss << L"\r\n\t\t\t"
                     << constraint->
                        duration_constraint.outlying_values_array[i];
            }
        }
        if( constraint->duration_constraint.excluded_values_count )
        {
            woss << L"\r\n\t\tExcluding "
                 << constraint->duration_constraint.excluded_values_count
                 << L" Value(s):";
            for( piint i = 0;
                 i < constraint->duration_constraint.excluded_values_count;
                 ++i )
            {
                woss << L"\r\n\t\t\t"
                     << constraint->
                        duration_constraint.excluded_values_array[i];
            }
        }

        // - generate frequency constraint message
        woss << L"\r\n\tFrequency Constraint:\r\n";
        woss << L"\t\tMinimum: "
             << constraint->frequency_constraint.minimum
             << L"\r\n";
        woss << L"\t\tMaximum: "
             << constraint->frequency_constraint.maximum
             << L"\r\n";
        woss << L"\t\tIncrement: "
             << constraint->frequency_constraint.increment;
        if( constraint->frequency_constraint.outlying_values_count )
        {
            woss << L"\r\n\t\tIncluding "
                 << constraint->frequency_constraint.outlying_values_count
                 << L" Value(s):";
            for( piint i = 0;
                 i < constraint->frequency_constraint.outlying_values_count;
                 ++i )
            {
                woss << L"\r\n\t\t\t"
                     << constraint->
                        frequency_constraint.outlying_values_array[i];
            }
        }
        if( constraint->frequency_constraint.excluded_values_count )
        {
            woss << L"\r\n\t\tExcluding "
                 << constraint->frequency_constraint.excluded_values_count
                 << L" Value(s):";
            for( piint i = 0;
                 i < constraint->frequency_constraint.excluded_values_count;
                 ++i )
            {
                woss << L"\r\n\t\t\t"
                     << constraint->
                        frequency_constraint.excluded_values_array[i];
            }
        }

        // - generate phase constraint message
        woss << L"\r\n\tPhase Constraint:\r\n";
        woss << L"\t\tMinimum: "
             << constraint->phase_constraint.minimum
             << L"\r\n";
        woss << L"\t\tMaximum: "
             << constraint->phase_constraint.maximum
             << L"\r\n";
        woss << L"\t\tIncrement: "
             << constraint->phase_constraint.increment;
        if( constraint->phase_constraint.outlying_values_count )
        {
            woss << L"\r\n\t\tIncluding "
                 << constraint->phase_constraint.outlying_values_count
                 << L" Value(s):";
            for( piint i = 0;
                 i < constraint->phase_constraint.outlying_values_count;
                 ++i )
            {
                woss << L"\r\n\t\t\t"
                     << constraint->phase_constraint.outlying_values_array[i];
            }
        }
        if( constraint->phase_constraint.excluded_values_count )
        {
            woss << L"\r\n\t\tExcluding "
                 << constraint->phase_constraint.excluded_values_count
                 << L" Value(s):";
            for( piint i = 0;
                 i < constraint->phase_constraint.excluded_values_count;
                 ++i )
            {
                woss << L"\r\n\t\t\t"
                     << constraint->phase_constraint.excluded_values_array[i];
            }
        }

        // - generate output signal frequency constraint message
        woss << L"\r\n\tOutput Signal Frequency Constraint:\r\n";
        woss << L"\t\tMinimum: "
             << constraint->output_signal_frequency_constraint.minimum
             << L"\r\n";
        woss << L"\t\tMaximum: "
             << constraint->output_signal_frequency_constraint.maximum
             << L"\r\n";
        woss << L"\t\tIncrement: "
             << constraint->output_signal_frequency_constraint.increment;
        if( constraint->
            output_signal_frequency_constraint.outlying_values_count )
        {
            woss << L"\r\n\t\tIncluding "
                 << constraint->
                    output_signal_frequency_constraint.outlying_values_count
                 << L" Value(s):";
            for( piint i = 0;
                 i < constraint->
                     output_signal_frequency_constraint.outlying_values_count;
                 ++i )
            {
                woss << L"\r\n\t\t\t"
                     << constraint->
                        output_signal_frequency_constraint.
                        outlying_values_array[i];
            }
        }
        if( constraint->output_signal_frequency_constraint.excluded_values_count )
        {
            woss << L"\r\n\t\tExcluding "
                 << constraint->
                    output_signal_frequency_constraint.excluded_values_count
                 << L" Value(s):";
            for( piint i = 0;
                 i < constraint->
                     output_signal_frequency_constraint.excluded_values_count;
                 ++i )
            {
                woss << L"\r\n\t\t\t"
                     << constraint->
                        output_signal_frequency_constraint.
                        excluded_values_array[i];
            }
        }
    }

    LogEvent( woss.str() );

    return PicamError_None;
}

////////////////////////////////////////////////////////////////////////////////
// AcquisitionUpdated
// - called when any of the following occur during acquisition:
//   - a new readout arrives
//   - acquisition completes due to total readouts acquired
//   - acquisition completes due to a stop request
//   - acquisition completes due to an acquisition error
//   - an acquisition error occurs
// - called on another thread
// - all update callbacks are serialized
// - takes the lock
////////////////////////////////////////////////////////////////////////////////
PicamError PIL_CALL AcquisitionUpdated(
    PicamHandle device,
    const PicamAvailableData* available,
    const PicamAcquisitionStatus* status )
{
    if( available && available->readout_count )
    {
        // - copy the last available frame to the shared image buffer and notify
        AutoLock al( lock_ );
		availabledata.readout_count = available->readout_count;
		availabledata.initial_readout = available->initial_readout;
        pi64s lastReadoutOffset = readoutStride_ * (available->readout_count-1);
        pi64s lastFrameOffset = frameStride_ * (framesPerReadout_-1);
        const pibyte* frame =
            static_cast<const pibyte*>( available->initial_readout ) +
            lastReadoutOffset + lastFrameOffset;
        std::memcpy( &imageData_[0], frame, frameSize_ );
        ++imageDataVersion_;
        WakeConditionVariable( &imageDataAvailable_ );
        al.Release();

        // - check for overrun after copying
        pibln overran;
        PicamError error =
            PicamAdvanced_HasAcquisitionBufferOverrun( device, &overran );
        if( error != PicamError_None )
        {
            std::wostringstream woss;
            woss << L"Failed check for buffer overrun. "
                 << L"("
                 << GetEnumString( PicamEnumeratedType_Error, error )
                 << L")";
            PostMessage(
                main_,
                WM_DISPLAY_ERROR,
                reinterpret_cast<WPARAM>( new std::wstring( woss.str() ) ),
                0 );
        }
        else if( overran )
        {
            PostMessage(
                main_,
                WM_DISPLAY_ERROR,
                reinterpret_cast<WPARAM>(
                    new std::wstring( L"Buffer overran." ) ),
                0 );
        }
    }

    // - note when acquisition has completed
    if( !status->running )
    {
        SetEvent( acquisitionInactive_ );
        PostMessage( main_, WM_ACQUISITION_STOPPED, 0, 0 );
    }

    return PicamError_None;
}

//##############################################################################
//##############################################################################
//##############################################################################
//##############################################################################
// Application-Level Features
//##############################################################################
//##############################################################################
//##############################################################################
//##############################################################################
////////////////////////////////////////////////////////////////////////////////
// Initialize
// - initialize state and camera discovery
// - any failure quits the application
////////////////////////////////////////////////////////////////////////////////
pibool Initialize()
{
    // - show wait cursor while in this function
    AutoBusy ab;

    //Initialize Winsock and set up server listening port
    int wserror = ListenOnPort(PORTNO);
	wstring wserrstr = L"ListenOnPort returned error: ";
	wserrstr.append(to_wstring(wserror));
	if (wserror < 0) DisplayError(wserrstr);

    // - initialize state
    InitializeCriticalSection( &lock_ );
    acquisitionInactive_ =
        CreateEvent( 0, true /*manual*/, true /*signaled*/, 0 );
    if( !acquisitionInactive_ )
    {
        DisplayError( L"Failed to create acquisition inactive event." );
        return false;
    }
    InitializeConditionVariable( &imageDataAvailable_ );
    HANDLE thread = reinterpret_cast<HANDLE>(
        _beginthreadex( 0, 0, RenderThreadProc, 0, 0, 0 ) );
    if( !thread )
    {
        DisplayError( L"Failed to create render thread." );
        return false;
    }
    CloseHandle( thread );

    // - initialize picam
    PicamError error = Picam_InitializeLibrary();
    if( error != PicamError_None )
    {
        DisplayError( L"Failed to initialize PICam.", error );
        return false;
    }

    // - initialize available camera list
    const PicamCameraID* available;
    piint availableCount;
    error = Picam_GetAvailableCameraIDs( &available, &availableCount );
    if( error != PicamError_None )
    {
        DisplayError( L"Failed to get available cameras.", error );
        return false;
    }
    if( availableCount > 0 )
    {
        available_.insert(
            available_.end(),
            available,
            available+availableCount );
    }
    Picam_DestroyCameraIDs( available );

    // - initialize unavailable camera list
    const PicamCameraID* unavailable;
    piint unavailableCount;
    error = Picam_GetUnavailableCameraIDs( &unavailable, &unavailableCount );
    if( error != PicamError_None )
    {
        DisplayError( L"Failed to get unavailable cameras.", error );
        return false;
    }
    if( unavailableCount > 0 )
    {
        unavailable_.insert(
            unavailable_.end(),
            unavailable,
            unavailable+unavailableCount );
    }
    Picam_DestroyCameraIDs( unavailable );

    // - initialize camera discovery
    error = PicamAdvanced_RegisterForDiscovery( CameraDiscovered );
    if( error != PicamError_None )
    {
        DisplayError( L"Failed to register camera discovery.", error );
        return false;
    }
    error = PicamAdvanced_DiscoverCameras();
    if( error != PicamError_None )
    {
        DisplayError( L"Failed to start camera discovery.", error );
        return false;
    }

    return true;
}

////////////////////////////////////////////////////////////////////////////////
// Uninitialize
// - clean up camera on exit
// - handles an open and acquiring camera as well
////////////////////////////////////////////////////////////////////////////////
void Uninitialize()
{
    
    //close connection to client
    closesocket(s); //Shut down socket
    WSACleanup(); //Clean up Winsock
    
    if( device_ )
    {
        // - handle an acquiring camera
        pibln running;
        PicamError error = Picam_IsAcquisitionRunning( device_, &running );
        if( error == PicamError_None && running )
        {
            error = Picam_StopAcquisition( device_ );
            running =
                error != PicamError_None ||
                WaitForSingleObject(
                    acquisitionInactive_,
                    10000 ) != WAIT_OBJECT_0;
            if( running )
                DisplayError( L"Failed to stop camera.", error );
        }

        // - handle an open camera
        if( !running )
            PicamAdvanced_CloseCameraDevice( device_ );
    }

    // - clean up library
    // - this is especially important for other processes using picam
    Picam_UninitializeLibrary();
}

////////////////////////////////////////////////////////////////////////////////
// SelectCamera
// - either selects the default camera or prompts the user for selection
// - takes the lock
////////////////////////////////////////////////////////////////////////////////
void SelectCamera( pibool selectDefault )
{
    const PicamCameraID* id = 0;

    if( selectDefault )
    {
        // - default to the first available camera
        AutoLock al( lock_ );
        if( !available_.empty() )
            id = new PicamCameraID( available_.front() );
    }
    else
    {
        // - show the camera selection dialog
        INT_PTR result =
            DialogBox(
                instance_,
                MAKEINTRESOURCE( IDD_CAMERAS ),
                main_,
                CamerasDialogProc );
        id = reinterpret_cast<PicamCameraID*>( result );
    }

    // - only handle a selection
    if( id )
    {
        PicamError error;

        // - assume selection changed
        pibool selectionChanged = true;

        // - determine if selection changed
        if( device_ )
        {
            PicamCameraID deviceID;
            error = Picam_GetCameraID( device_, &deviceID );
            if( error == PicamError_None && *id == deviceID )
                selectionChanged = false;
        }

        // - open the newly selected camera if selection changed
        if( selectionChanged )
            OpenCamera( *id );

        // - clean up
        delete id;
    }
}

////////////////////////////////////////////////////////////////////////////////
// SetExposureTime
// - shows the modeless exposure time dialog
////////////////////////////////////////////////////////////////////////////////
void SetExposureTime()
{
    // - if dialog already open, bring it to the front
    if( exposure_ )
    {
        SetForegroundWindow( exposure_ );
        return;
    }

    // - create and show the dialog
    exposure_ =
        CreateDialog(
            instance_,
            MAKEINTRESOURCE( IDD_EXPOSURE ),
            main_,
            ExposureDialogProc );
}

////////////////////////////////////////////////////////////////////////////////
// SetRepetitiveGate
// - shows the modeless repetitive gate dialog
////////////////////////////////////////////////////////////////////////////////
void SetRepetitiveGate()
{
    // - if dialog already open, bring it to the front
    if( repetitiveGate_ )
    {
        SetForegroundWindow( repetitiveGate_ );
        return;
    }

    // - create and show the dialog
    repetitiveGate_ =
        CreateDialog(
            instance_,
            MAKEINTRESOURCE( IDD_REPETITIVEGATE ),
            main_,
            RepetitiveGateDialogProc );
}

////////////////////////////////////////////////////////////////////////////////
// SetParameters
// - prompts the user to change parameter values
////////////////////////////////////////////////////////////////////////////////
void SetParameters()
{
    // - show the camera parameters dialog
    DialogBox(
        instance_,
        MAKEINTRESOURCE( IDD_PARAMETERS ),
        main_,
        ParametersDialogProc );
}

////////////////////////////////////////////////////////////////////////////////
// Preview
// - runs a continuous acquisition until stop is requested
////////////////////////////////////////////////////////////////////////////////
void Preview()
{
    // - set up readouts appropriately
    if( !SetReadoutCount( false /*acquire*/ ) )
        return;

    // - start the asynchronous acquisition
    Start();
}

////////////////////////////////////////////////////////////////////////////////
// Acquire
// - runs an acquisition for the previously specified number of readouts
////////////////////////////////////////////////////////////////////////////////
void Acquire()
{
    // - set up readouts appropriately
    if( !SetReadoutCount( true /*acquire*/ ) )
        return;

    // - start the asynchronous acquisition
    Start();
}

////////////////////////////////////////////////////////////////////////////////
// Stop
// - requests for an asynchronous acquisition to stop
////////////////////////////////////////////////////////////////////////////////
void Stop()
{
    PicamError error = Picam_StopAcquisition( device_ );
    if( error != PicamError_None )
        DisplayError( L"Failed to stop acquisition.", error );
}

////////////////////////////////////////////////////////////////////////////////
// SaveFrame
// - saves the last frame acquired
// - takes the lock
////////////////////////////////////////////////////////////////////////////////
void SaveFrame()
{
    // - show wait cursor while in this function
    AutoBusy ab;

    // - take lock before accessing shared state
    AutoLock al( lock_ );

    // - validate image data is present
    if( !imageDataVersion_ )
    {
        DisplayError( L"No image data." );
        return;
    }

    // - build the path
    wchar_t current[MAX_PATH];
    if( !GetCurrentDirectory( MAX_PATH, current ) )
    {
        DisplayError( L"Failed to get current directory." );
        return;
    }
    SYSTEMTIME time;
    GetLocalTime( &time );
    std::wostringstream woss;
    woss << current << L"\\"
         << L"Advanced Data - "
         << time.wYear << L"_" << time.wMonth << L"_" << time.wDay
         << L" - "
         << time.wHour << L"_" << time.wMinute << L"_" << time.wSecond
         << L".raw";
    std::wstring path( woss.str() );

    // - write the file with a basic header
    std::ofstream file( path.c_str(), std::ios::binary | std::ios::out );
    file.write(
        reinterpret_cast<pichar*>( &imageDataWidth_ ),
        sizeof( imageDataWidth_ ) );
    file.write(
        reinterpret_cast<pichar*>( &imageDataHeight_ ),
        sizeof( imageDataHeight_ ) );

    // - write the image data
    file.write(
        reinterpret_cast<pichar*>( &imageData_[0] ),
        imageData_.size() * sizeof( imageData_[0] ) );
}

//##############################################################################
//##############################################################################
//##############################################################################
//##############################################################################
// Camera Parameters Dialog
//##############################################################################
//##############################################################################
//##############################################################################
//##############################################################################
////////////////////////////////////////////////////////////////////////////////
// UpdateParameterInformation
// - updates the parameter-dependent controls in the parameters dialog
////////////////////////////////////////////////////////////////////////////////
void UpdateParameterInformation( HWND dialog )
{
    // - get the selected parameter
    LRESULT index =
        SendDlgItemMessage( dialog, IDC_PARAMETER, CB_GETCURSEL, 0, 0 );
    LRESULT result =
        SendDlgItemMessage( dialog, IDC_PARAMETER, CB_GETITEMDATA, index, 0 );

    // - handle no selection
    if( result == CB_ERR )
    {
        SetDlgItemText( dialog, IDC_FORMAT,          0 );
        SetDlgItemText( dialog, IDC_VALUE,           0 );
        SetDlgItemText( dialog, IDC_FORMATTED_VALUE, 0 );
        SetDlgItemText( dialog, IDC_ACCESS,          0 );
        SetDlgItemText( dialog, IDC_DYNAMICS,        0 );
        return;
    }

    PicamParameter parameter = static_cast<PicamParameter>( result );

    // - get the camera model
    PicamHandle model;
    PicamError error = PicamAdvanced_GetCameraModel( device_, &model );
    if( error != PicamError_None )
    {
        DisplayError( L"Failed to get camera model.", error );
        return;
    }

    std::wstring text;

    // - show the format
    PicamValueType valueType;
    error = Picam_GetParameterValueType( model, parameter, &valueType );
    if( error != PicamError_None )
    {
        DisplayError( L"Failed to get parameter value type.", error );
        return;
    }
    text = GetEnumString( PicamEnumeratedType_ValueType, valueType );
    switch( valueType )
    {
        case PicamValueType_Integer:
        case PicamValueType_LargeInteger:
        case PicamValueType_FloatingPoint:
            break;
        case PicamValueType_Boolean:
            text += L" (false = 0, true = non-0)";
            break;
        case PicamValueType_Enumeration:
            text += L" (as integer value)";
            break;
        case PicamValueType_Rois:
            text += L" (as 'x,y w,h xb,yb')";
            break;
        case PicamValueType_Pulse:
            text += L" (as 'd,w')";
            break;
        case PicamValueType_Modulations:
            text += L" (as 'd,f,p,osf d,f,p,osf...')";
            break;
    }
    SetDlgItemText( dialog, IDC_FORMAT, text.c_str() );

    // - show the value
    std::wstring formatted;
    if( !GetParameterValue( parameter, text, formatted ) )
        return;
    SetDlgItemText( dialog, IDC_VALUE, text.c_str() );
    SetDlgItemText( dialog, IDC_FORMATTED_VALUE, formatted.c_str() );

    // - show the access
    PicamValueAccess access;
    error = Picam_GetParameterValueAccess( model, parameter, &access );
    if( error != PicamError_None )
    {
        DisplayError( L"Failed to get parameter value access.", error );
        return;
    }
    text = GetEnumString( PicamEnumeratedType_ValueAccess, access );
    SetDlgItemText( dialog, IDC_ACCESS, text.c_str() );

    // - show the dynamics
    PicamDynamicsMask dynamics;
    error = PicamAdvanced_GetParameterDynamics( model, parameter, &dynamics );
    if( error != PicamError_None )
    {
        DisplayError( L"Failed to get parameter dynamics.", error );
        return;
    }
    text = GetEnumString( PicamEnumeratedType_DynamicsMask, dynamics );
    SetDlgItemText( dialog, IDC_DYNAMICS, text.c_str() );
}

////////////////////////////////////////////////////////////////////////////////
// InitializeParametersDialog
// - initializes the parameters dialog just before it is shown
////////////////////////////////////////////////////////////////////////////////
void InitializeParametersDialog( HWND dialog )
{
    parameters_ = dialog;

    // - get the camera model
    PicamHandle model;
    PicamError error = PicamAdvanced_GetCameraModel( device_, &model );
    if( error != PicamError_None )
    {
        DisplayError( L"Failed to get camera model.", error );
        return;
    }

    // - initialize the parameter combo box
    const PicamParameter* parameters;
    piint count;
    error = Picam_GetParameters( model, &parameters, &count );
    if( error != PicamError_None )
    {
        DisplayError( L"Failed to get camera parameters.", error );
        return;
    }
    for( piint i = 0; i < count; ++i )
    {
        // - create a wstring version of the parameter
        std::wstring item =
            GetEnumString( PicamEnumeratedType_Parameter, parameters[i] );

        // - add the wstring to the combo box
        LPARAM lParam = reinterpret_cast<LPARAM>( item.c_str() );
        LRESULT index =
            SendDlgItemMessage(
                dialog,
                IDC_PARAMETER,
                CB_ADDSTRING,
                0,
                lParam );

        // - set the underlying id value
        SendDlgItemMessage(
            dialog,
            IDC_PARAMETER,
            CB_SETITEMDATA,
            index,
            parameters[i] );
    }
    Picam_DestroyParameters( parameters );

    UpdateParameterInformation( dialog );
}

////////////////////////////////////////////////////////////////////////////////
// ApplyValueText
// - sets the parameter value from the edit control
////////////////////////////////////////////////////////////////////////////////
void ApplyValueText( HWND dialog )
{
    // - get the selected parameter
    LRESULT index =
        SendDlgItemMessage( dialog, IDC_PARAMETER, CB_GETCURSEL, 0, 0 );
    LRESULT result =
        SendDlgItemMessage( dialog, IDC_PARAMETER, CB_GETITEMDATA, index, 0 );

    // - handle no selection
    if( result == CB_ERR )
    {
        DisplayError( L"No parameter selected." );
        return;
    }

    PicamParameter parameter = static_cast<PicamParameter>( result );

    // - get the text from the edit control
    wchar_t text[1024];
    if( !GetDlgItemText( dialog, IDC_VALUE, text, sizeof( text ) ) )
    {
        DisplayError( L"Invalid format." );
        return;
    }

    // - set the value and update information if successful
    if( SetParameterValue( parameter, text ) )
        UpdateParameterInformation( dialog );
}

////////////////////////////////////////////////////////////////////////////////
// LogEvent
// - appends a message to the event log
////////////////////////////////////////////////////////////////////////////////
void LogEvent( const std::wstring& message )
{
    // - move caret to the beginning
    SendDlgItemMessage(
        parameters_,
        IDC_EVENTS, 
        EM_SETSEL, 
        static_cast<WPARAM>( 0 ), 
        static_cast<LPARAM>( 0 ) );

    // - prepend to the log
    std::wstring line( message + L"\r\n" );
    SendDlgItemMessage(
        parameters_,
        IDC_EVENTS,
        EM_REPLACESEL,
        false /*undo*/,
        reinterpret_cast<LPARAM>( line.c_str() ) );
}

////////////////////////////////////////////////////////////////////////////////
// ClearEventLog
// - clears the event log
////////////////////////////////////////////////////////////////////////////////
void ClearEventLog( HWND dialog )
{
    // - clear the edit control
    SetDlgItemText( dialog, IDC_EVENTS, 0 );
}

////////////////////////////////////////////////////////////////////////////////
// ValidateParameters
// - validates camera model parameters and shows results in the parameters
//   dialog
////////////////////////////////////////////////////////////////////////////////
void ValidateParameters()
{
    // - get the camera model
    PicamHandle model;
    PicamError error = PicamAdvanced_GetCameraModel( device_, &model );
    if( error != PicamError_None )
    {
        DisplayError( L"Failed to get camera model.", error );
        return;
    }

    // - validate the model
    const PicamValidationResults* results;
    error = PicamAdvanced_ValidateParameters( model, &results );
    if( error != PicamError_None )
    {
        DisplayError( L"Failed to validate to camera model.", error );
        return;
    }

    // - generate log message
    std::wstring message;
    if( results->is_valid )
        message = L"Validation succeeded";
    else
    {
        std::wostringstream woss;
        woss << L"Validation failed:";
        for( piint i = 0; i < results->validation_result_count; ++i )
        {
            const PicamValidationResult* result =
                &results->validation_result_array[i];
            if( result->error_constraining_parameter_count )
            {
                woss << L"\r\n\t"
                     << GetEnumString(
                            PicamEnumeratedType_Parameter,
                            *result->failed_parameter )
                     << L" is in "
                     << GetEnumString(
                            PicamEnumeratedType_ConstraintSeverity,
                            PicamConstraintSeverity_Error )
                     << L" due to "
                     << result->error_constraining_parameter_count
                     << L" Parameter(s):";
                for( piint j = 0;
                     j < result->error_constraining_parameter_count;
                     ++j )
                {
                    woss << L"\r\n\t\t"
                         << GetEnumString(
                                PicamEnumeratedType_Parameter,
                                result->error_constraining_parameter_array[j] );
                }
            }
            if( result->warning_constraining_parameter_count )
            {
                woss << L"\r\n\t"
                     << GetEnumString(
                            PicamEnumeratedType_Parameter,
                            *result->failed_parameter )
                     << L" is in "
                     << GetEnumString(
                            PicamEnumeratedType_ConstraintSeverity,
                            PicamConstraintSeverity_Warning )
                     << L" due to "
                     << result->warning_constraining_parameter_count
                     << L" Parameter(s):";
                for( piint j = 0;
                     j < result->warning_constraining_parameter_count;
                     ++j )
                {
                    woss << L"\r\n\t\t"
                         << GetEnumString(
                                PicamEnumeratedType_Parameter,
                                result->warning_constraining_parameter_array[j] );
                }
            }
        }
        message = woss.str();
    }
    Picam_DestroyValidationResults( results );

    LogEvent( message );
}

////////////////////////////////////////////////////////////////////////////////
// CommitParameters
// - commits the camera model and shows results in the parameters dialog
////////////////////////////////////////////////////////////////////////////////
pibool CommitParameters()
{
    // - get the camera model
    PicamHandle model;
    PicamError error = PicamAdvanced_GetCameraModel( device_, &model );
    if( error != PicamError_None )
    {
        DisplayError( L"Failed to get camera model.", error );
        return false;
    }

    // - apply changes to the device
    // - any changes to the model will be handled through change callbacks
    error = PicamAdvanced_CommitParametersToCameraDevice( model );
    if( error != PicamError_None )
    {
        DisplayError( L"Failed to commit to camera device.", error );
        return false;
    }

    // - refresh the modeless dialogs if open
    if( exposure_ )
        RefreshExposureDialog( exposure_ );
    if( repetitiveGate_ )
        RefreshRepetitiveGateDialog( repetitiveGate_ );

    LogEvent( L"Parameters committed" );

    return true;
}

////////////////////////////////////////////////////////////////////////////////
// RefreshParameters
// - refreshes the camera model and shows results in the parameters dialog
////////////////////////////////////////////////////////////////////////////////
void RefreshParameters( HWND dialog ) 
{
    // - get the camera model
    PicamHandle model;
    PicamError error = PicamAdvanced_GetCameraModel( device_, &model );
    if( error != PicamError_None )
    {
        DisplayError( L"Failed to get camera model.", error );
        return;
    }

    // - revert changes on the model
    // - any changes to the model will be handled through change callbacks
    error = PicamAdvanced_RefreshParametersFromCameraDevice( model );
    if( error != PicamError_None )
    {
        DisplayError( L"Failed to refresh camera model.", error );
        return;
    }

    // - reflect any changes
    UpdateParameterInformation( dialog );

    LogEvent( L"Parameters refreshed" );
}

////////////////////////////////////////////////////////////////////////////////
// ApplyParametersDialog
// - handles acceptance from the parameters dialog
////////////////////////////////////////////////////////////////////////////////
void ApplyParametersDialog( HWND dialog )
{
    if( !CommitParameters() )
        return;

    // - close the dialog (only on success)
    parameters_ = 0;
    EndDialog( dialog, true /*result*/ );
}

////////////////////////////////////////////////////////////////////////////////
// CancelParametersDialog
// - handles cancelation from the parameters dialog
////////////////////////////////////////////////////////////////////////////////
void CancelParametersDialog( HWND dialog )
{
    RefreshParameters( dialog );

    // - close the dialog (regardless of success)
    parameters_ = 0;
    EndDialog( dialog, false /*result*/ );
}

////////////////////////////////////////////////////////////////////////////////
// ParametersDialogProc
// - camera parameters dialog window procedure
////////////////////////////////////////////////////////////////////////////////
INT_PTR CALLBACK ParametersDialogProc(
    HWND hwndDlg,
    UINT uMsg,
    WPARAM wParam,
    LPARAM lParam )
{
    UNREFERENCED_PARAMETER( lParam );

    switch( uMsg )
    {
        case WM_INITDIALOG:
            InitializeParametersDialog( hwndDlg );
            break;
        case WM_CLOSE:
            wParam = IDCANCEL;
            // - fall through
        case WM_COMMAND:
            switch( LOWORD( wParam ) )
            {
                case IDC_PARAMETER:
                    if( HIWORD( wParam ) == CBN_SELCHANGE )
                        UpdateParameterInformation( hwndDlg );
                    else
                        return false;
                    break;
                case IDC_SUBMIT:
                    ApplyValueText( hwndDlg );
                    break;
                case IDC_CLEAR:
                    ClearEventLog( hwndDlg );
                    break;
                case IDC_VALIDATE:
                    ValidateParameters();
                    break;
                case IDC_COMMIT:
                    CommitParameters();
                    break;
                case IDC_REFRESH:
                    RefreshParameters( hwndDlg );
                    break;
                case IDOK:
                    ApplyParametersDialog( hwndDlg );
                    break;
                case IDCANCEL:
                    CancelParametersDialog( hwndDlg );
                    break;
                default:
                    return false;
            }
            break;
        default:
            return false;
    }

    return true;
}

//##############################################################################
//##############################################################################
//##############################################################################
//##############################################################################
// Exposure Time Dialog
//##############################################################################
//##############################################################################
//##############################################################################
//##############################################################################
////////////////////////////////////////////////////////////////////////////////
// InitializeExposureDialog
// - initializes the exposure dialog just before it is shown
////////////////////////////////////////////////////////////////////////////////
void InitializeExposureDialog( HWND dialog )
{
    // - set slider range from 1-1000 ms
    LPARAM range = MAKELPARAM( 1, 1000 );
    SendDlgItemMessage(
        dialog,
        IDC_SLIDER,
        TBM_SETRANGE,
        true /*redraw*/,
        range );

    // - set slider page to 100 ms
    SendDlgItemMessage( dialog, IDC_SLIDER, TBM_SETPAGESIZE, 0, 100 );

    // - reflect current exposure time
    RefreshExposureDialog( dialog );
}

////////////////////////////////////////////////////////////////////////////////
// RefreshExposureDialog
// - refreshes the exposure information in the exposure dialog
////////////////////////////////////////////////////////////////////////////////
void RefreshExposureDialog( HWND dialog )
{
    // - get the current set up exposure time
    PicamHandle model;
    PicamError error = PicamAdvanced_GetCameraModel( device_, &model );
    if( error != PicamError_None )
    {
        DisplayError( L"Failed to get camera model.", error );
        return;
    }
    piflt exposure;
    error =
        Picam_GetParameterFloatingPointValue(
            model,
            PicamParameter_ExposureTime,
            &exposure );
    if( error != PicamError_None )
    {
        DisplayError( L"Failed to get exposure time.", error );
        return;
    }

    // - set exposure text in edit control
    std::wostringstream woss;
    woss << exposure;
    SetDlgItemText( dialog, IDC_EXPOSURE, woss.str().c_str() );

    // - set to nearest slider position based on exposure time
    piint position = static_cast<piint>( exposure + 0.5 );
    SendDlgItemMessage(
        dialog,
        IDC_SLIDER,
        TBM_SETPOS,
        true /*redraw*/,
        position );
}

////////////////////////////////////////////////////////////////////////////////
// ApplyExposureTimeText
// - sets the exposure time from the edit control
////////////////////////////////////////////////////////////////////////////////
void ApplyExposureTimeText( HWND dialog )
{
    // - get the text from the edit control
    wchar_t text[1024];
    if( !GetDlgItemText( dialog, IDC_EXPOSURE, text, sizeof( text ) ) )
    {
        DisplayError( L"Invalid format." );
        return;
    }

    // - parse the text
    piflt exposure;
    std::wistringstream wiss( text );
    wiss >> exposure >> std::ws;
    if( wiss.fail() || !wiss.eof() )
    {
        DisplayError( L"Invalid format." );
        return;
    }

    // - reposition the slider
    piint position = static_cast<piint>( exposure + 0.5 );
    SendDlgItemMessage(
        dialog,
        IDC_SLIDER,
        TBM_SETPOS,
        true /*redraw*/,
        position );

    // - set exposure in the camera
    ApplyExposureTime( exposure );
}

////////////////////////////////////////////////////////////////////////////////
// ApplyExposureTimePosition
// - sets the exposure time from the slider
////////////////////////////////////////////////////////////////////////////////
void ApplyExposureTimePosition( HWND dialog )
{
    // - get the exposure from the slider position
    piint exposure = static_cast<piint>(
        SendDlgItemMessage( dialog, IDC_SLIDER, TBM_GETPOS, 0, 0 ) );

    // - synchronize the text in the edit control
    SetDlgItemInt( dialog, IDC_EXPOSURE, exposure, false /*signed*/ );

    // - set exposure in the camera
    ApplyExposureTime( exposure );
}

////////////////////////////////////////////////////////////////////////////////
// CloseExposureDialog
// - handles closing of the exposure dialog
////////////////////////////////////////////////////////////////////////////////
void CloseExposureDialog( HWND dialog )
{
    EndDialog( dialog, 0 );
    exposure_ = 0;
}

////////////////////////////////////////////////////////////////////////////////
// ExposureDialogProc
// - exposure time dialog window procedure
////////////////////////////////////////////////////////////////////////////////
INT_PTR CALLBACK ExposureDialogProc(
    HWND hwndDlg,
    UINT uMsg,
    WPARAM wParam,
    LPARAM lParam )
{
    UNREFERENCED_PARAMETER( lParam );

    switch( uMsg )
    {
        case WM_INITDIALOG:
            InitializeExposureDialog( hwndDlg );
            break;
        case WM_CLOSE:
            wParam = IDCANCEL;
            // - fall through
        case WM_COMMAND:
            switch( LOWORD( wParam ) )
            {
                case IDC_SUBMIT:
                    ApplyExposureTimeText( hwndDlg );
                    break;
                case IDCANCEL:
                    CloseExposureDialog( hwndDlg );
                    break;
                default:
                    return false;
            }
            break;
        case WM_HSCROLL:
            ApplyExposureTimePosition( hwndDlg );
            break;
        default:
            return false;
    }

    return true;
}

//##############################################################################
//##############################################################################
//##############################################################################
//##############################################################################
// Repetitive Gate Dialog
//##############################################################################
//##############################################################################
//##############################################################################
//##############################################################################
////////////////////////////////////////////////////////////////////////////////
// InitializeRepetitiveGateDialog
// - initializes the repetitive gate dialog just before it is shown
////////////////////////////////////////////////////////////////////////////////
void InitializeRepetitiveGateDialog( HWND dialog )
{
    // - set slider range from 1-1000 us
    LPARAM range = MAKELPARAM( 1, 1000 );
    SendDlgItemMessage(
        dialog,
        IDC_DELAY_SLIDER,
        TBM_SETRANGE,
        true /*redraw*/,
        range );
    SendDlgItemMessage(
        dialog,
        IDC_WIDTH_SLIDER,
        TBM_SETRANGE,
        true /*redraw*/,
        range );

    // - set slider page to 100 us
    SendDlgItemMessage( dialog, IDC_DELAY_SLIDER, TBM_SETPAGESIZE, 0, 100 );
    SendDlgItemMessage( dialog, IDC_WIDTH_SLIDER, TBM_SETPAGESIZE, 0, 100 );

    // - reflect current pulse
    RefreshRepetitiveGateDialog( dialog );
}

////////////////////////////////////////////////////////////////////////////////
// RefreshRepetitiveDialog
// - refreshes the pulse information in the repetitive gate dialog
////////////////////////////////////////////////////////////////////////////////
void RefreshRepetitiveGateDialog( HWND dialog )
{
    // - get the current set up repetitive gate
    PicamHandle model;
    PicamError error = PicamAdvanced_GetCameraModel( device_, &model );
    if( error != PicamError_None )
    {
        DisplayError( L"Failed to get camera model.", error );
        return;
    }
    const PicamPulse* pulse;
    error =
        Picam_GetParameterPulseValue(
            model,
            PicamParameter_RepetitiveGate,
            &pulse );
    if( error != PicamError_None )
    {
        DisplayError( L"Failed to get repetitive gate.", error );
        return;
    }
    piflt delay = pulse->delay/1000.;
    piflt width = pulse->width/1000.;
    Picam_DestroyPulses( pulse );

    // - set delay and width text in edit controls
    std::wostringstream woss1;
    woss1 << delay;
    SetDlgItemText( dialog, IDC_DELAY, woss1.str().c_str() );
    std::wostringstream woss2;
    woss2 << width;
    SetDlgItemText( dialog, IDC_WIDTH, woss2.str().c_str() );

    // - set to nearest slider positions based on pulse
    piint position = static_cast<piint>( delay + 0.5 );
    SendDlgItemMessage(
        dialog,
        IDC_DELAY_SLIDER,
        TBM_SETPOS,
        true /*redraw*/,
        position );
    position = static_cast<piint>( width + 0.5 );
    SendDlgItemMessage(
        dialog,
        IDC_WIDTH_SLIDER,
        TBM_SETPOS,
        true /*redraw*/,
        position );
}

////////////////////////////////////////////////////////////////////////////////
// ApplyRepetitiveGateDelayText
// - sets the repetitive gate delay from the edit control
////////////////////////////////////////////////////////////////////////////////
void ApplyRepetitiveGateDelayText( HWND dialog )
{
    // - get the text from the edit control
    wchar_t text[1024];
    if( !GetDlgItemText( dialog, IDC_DELAY, text, sizeof( text ) ) )
    {
        DisplayError( L"Invalid format for delay." );
        return;
    }

    // - parse the text
    piflt delay;
    std::wistringstream wiss( text );
    wiss >> delay >> std::ws;
    if( wiss.fail() || !wiss.eof() )
    {
        DisplayError( L"Invalid format for delay." );
        return;
    }

    // - reposition the sliders
    piint position = static_cast<piint>( delay + 0.5 );
    SendDlgItemMessage(
        dialog,
        IDC_DELAY_SLIDER,
        TBM_SETPOS,
        true /*redraw*/,
        position );

    // - get the current set up repetitive gate width
    PicamHandle model;
    PicamError error = PicamAdvanced_GetCameraModel( device_, &model );
    if( error != PicamError_None )
    {
        DisplayError( L"Failed to get camera model.", error );
        return;
    }
    const PicamPulse* currentPulse;
    error =
        Picam_GetParameterPulseValue(
            model,
            PicamParameter_RepetitiveGate,
            &currentPulse );
    if( error != PicamError_None )
    {
        DisplayError( L"Failed to get repetitive gate.", error );
        return;
    }
    piflt width = currentPulse->width;
    Picam_DestroyPulses( currentPulse );

    // - set repetitive gate in the camera
    PicamPulse pulse = { delay*1000., width };
    ApplyRepetitiveGate( pulse );
}

////////////////////////////////////////////////////////////////////////////////
// ApplyRepetitiveGateWidthText
// - sets the repetitive gate width from the edit control
////////////////////////////////////////////////////////////////////////////////
void ApplyRepetitiveGateWidthText( HWND dialog )
{
    // - get the text from the edit control
    wchar_t text[1024];
    if( !GetDlgItemText( dialog, IDC_WIDTH, text, sizeof( text ) ) )
    {
        DisplayError( L"Invalid format for width." );
        return;
    }

    // - parse the text
    piflt width;
    std::wistringstream wiss( text );
    wiss >> width >> std::ws;
    if( wiss.fail() || !wiss.eof() )
    {
        DisplayError( L"Invalid format for width." );
        return;
    }

    // - reposition the sliders
    piint position = static_cast<piint>( width + 0.5 );
    SendDlgItemMessage(
        dialog,
        IDC_WIDTH_SLIDER,
        TBM_SETPOS,
        true /*redraw*/,
        position );

    // - get the current set up repetitive gate delay
    PicamHandle model;
    PicamError error = PicamAdvanced_GetCameraModel( device_, &model );
    if( error != PicamError_None )
    {
        DisplayError( L"Failed to get camera model.", error );
        return;
    }
    const PicamPulse* currentPulse;
    error =
        Picam_GetParameterPulseValue(
            model,
            PicamParameter_RepetitiveGate,
            &currentPulse );
    if( error != PicamError_None )
    {
        DisplayError( L"Failed to get repetitive gate.", error );
        return;
    }
    piflt delay = currentPulse->delay;
    Picam_DestroyPulses( currentPulse );

    // - set repetitive gate in the camera
    PicamPulse pulse = { delay, width*1000. };
    ApplyRepetitiveGate( pulse );
}

////////////////////////////////////////////////////////////////////////////////
// ApplyRepetitiveGateDelayPosition
// - sets the repetitive gate delay from the slider
////////////////////////////////////////////////////////////////////////////////
void ApplyRepetitiveGateDelayPosition( HWND dialog )
{
    // - get the current set up repetitive gate width
    PicamHandle model;
    PicamError error = PicamAdvanced_GetCameraModel( device_, &model );
    if( error != PicamError_None )
    {
        DisplayError( L"Failed to get camera model.", error );
        return;
    }
    const PicamPulse* pulse;
    error =
        Picam_GetParameterPulseValue(
            model,
            PicamParameter_RepetitiveGate,
            &pulse );
    if( error != PicamError_None )
    {
        DisplayError( L"Failed to get repetitive gate.", error );
        return;
    }
    piflt width = pulse->width;
    Picam_DestroyPulses( pulse );

    // - get the delay from the slider position
    piint delay = static_cast<piint>(
        SendDlgItemMessage( dialog, IDC_DELAY_SLIDER, TBM_GETPOS, 0, 0 ) );

    // - synchronize the text in the edit control
    SetDlgItemInt( dialog, IDC_DELAY, delay, false /*signed*/ );

    // - set repetitive gate in the camera
    PicamPulse value = { delay*1000., width };
    ApplyRepetitiveGate( value );
}

////////////////////////////////////////////////////////////////////////////////
// ApplyRepetitiveGateWidthPosition
// - sets the repetitive gate width from the slider
////////////////////////////////////////////////////////////////////////////////
void ApplyRepetitiveGateWidthPosition( HWND dialog )
{
    // - get the current set up repetitive gate delay
    PicamHandle model;
    PicamError error = PicamAdvanced_GetCameraModel( device_, &model );
    if( error != PicamError_None )
    {
        DisplayError( L"Failed to get camera model.", error );
        return;
    }
    const PicamPulse* pulse;
    error =
        Picam_GetParameterPulseValue(
            model,
            PicamParameter_RepetitiveGate,
            &pulse );
    if( error != PicamError_None )
    {
        DisplayError( L"Failed to get repetitive gate.", error );
        return;
    }
    piflt delay = pulse->delay;
    Picam_DestroyPulses( pulse );

    // - get the width from the slider position
    piint width = static_cast<piint>(
        SendDlgItemMessage( dialog, IDC_WIDTH_SLIDER, TBM_GETPOS, 0, 0 ) );

    // - synchronize the text in the edit control
    SetDlgItemInt( dialog, IDC_WIDTH, width, false /*signed*/ );

    // - set repetitive gate in the camera
    PicamPulse value = { delay, width*1000. };
    ApplyRepetitiveGate( value );
}

////////////////////////////////////////////////////////////////////////////////
// CloseRepetitiveGateDialog
// - handles closing of the repetitive gate dialog
////////////////////////////////////////////////////////////////////////////////
void CloseRepetitiveGateDialog( HWND dialog )
{
    EndDialog( dialog, 0 );
    repetitiveGate_ = 0;
}

////////////////////////////////////////////////////////////////////////////////
// RepetitiveGateDialogProc
// - repetitive gate dialog window procedure
////////////////////////////////////////////////////////////////////////////////
INT_PTR CALLBACK RepetitiveGateDialogProc(
    HWND hwndDlg,
    UINT uMsg,
    WPARAM wParam,
    LPARAM lParam )
{
    switch( uMsg )
    {
        case WM_INITDIALOG:
            InitializeRepetitiveGateDialog( hwndDlg );
            break;
        case WM_CLOSE:
            wParam = IDCANCEL;
            // - fall through
        case WM_COMMAND:
            switch( LOWORD( wParam ) )
            {
                case IDC_SUBMIT_DELAY:
                    ApplyRepetitiveGateDelayText( hwndDlg );
                    break;
                case IDC_SUBMIT_WIDTH:
                    ApplyRepetitiveGateWidthText( hwndDlg );
                    break;
                case IDCANCEL:
                    CloseRepetitiveGateDialog( hwndDlg );
                    break;
                default:
                    return false;
            }
            break;
        case WM_HSCROLL:
        {
            HWND slider = reinterpret_cast<HWND>( lParam );
            if( slider == ::GetDlgItem( hwndDlg, IDC_DELAY_SLIDER ) )
                ApplyRepetitiveGateDelayPosition( hwndDlg );
            else if( slider == ::GetDlgItem( hwndDlg, IDC_WIDTH_SLIDER ) )
                ApplyRepetitiveGateWidthPosition( hwndDlg );
            break;
        }
        default:
            return false;
    }

    return true;
}

//##############################################################################
//##############################################################################
//##############################################################################
//##############################################################################
// Camera Selection Dialog
//##############################################################################
//##############################################################################
//##############################################################################
//##############################################################################
////////////////////////////////////////////////////////////////////////////////
// InitializeCamerasDialog
// - initializes the cameras dialog just before it is shown
// - takes the lock
////////////////////////////////////////////////////////////////////////////////
void InitializeCamerasDialog( HWND dialog )
{
    // - store cameras dialog window handle
    AutoLock al( lock_ );
    cameras_ = dialog;
    al.Release();

    // - populate dynamic controls
    RefreshCamerasDialog( dialog );

    // - populate the available demo models
    const PicamModel* models;
    piint modelCount;
    PicamError error =
        Picam_GetAvailableDemoCameraModels( &models, &modelCount );
    if( error != PicamError_None )
    {
        DisplayError( L"Failed to get demo camera models.", error );
        return;
    }
    for( piint i = 0; i < modelCount; ++i )
    {
        // - create a wstring version of the model
        std::wstring item =
            GetEnumString( PicamEnumeratedType_Model, models[i] );

        // - add the wstring to the control
        LRESULT index =
            SendDlgItemMessage(
                dialog,
                IDC_DEMO,
                CB_ADDSTRING,
                0,
                reinterpret_cast<LPARAM>( item.c_str() ) );

        // - set the underlying model value
        SendDlgItemMessage(
            dialog,
            IDC_DEMO,
            CB_SETITEMDATA,
            index,
            models[i] );
    }
    Picam_DestroyModels( models );

    // - set a default serial number
    SetDlgItemText( dialog, IDC_SERIAL_NUMBER, L"00000" );
}

////////////////////////////////////////////////////////////////////////////////
// RefreshCamerasDialog
// - refreshes the camera information in the cameras dialog
// - takes the lock
////////////////////////////////////////////////////////////////////////////////
void RefreshCamerasDialog( HWND dialog )
{
    // - clear the controls
    SendDlgItemMessage( dialog, IDC_SELECTED,    CB_RESETCONTENT, 0, 0 );
    SendDlgItemMessage( dialog, IDC_AVAILABLE,   LB_RESETCONTENT, 0, 0 );
    SendDlgItemMessage( dialog, IDC_UNAVAILABLE, LB_RESETCONTENT, 0, 0 );

    // - lock before accessing shared state
    AutoLock al( lock_ );

    // - populate the selected and available controls
    for( std::list<PicamCameraID>::const_iterator i = available_.begin();
         i != available_.end();
         ++i )
    {
        // - create a wstring version of the camera id
        std::wostringstream woss;
        woss << GetEnumString( PicamEnumeratedType_Model, i->model )
             << L" (SN: " << i->serial_number << L")";
        std::wstring item( woss.str() );

        // - add the wstring to the controls
        LPARAM lParam = reinterpret_cast<LPARAM>( item.c_str() );
        SendDlgItemMessage(
            dialog,
            IDC_SELECTED,
            CB_ADDSTRING,
            0,
            lParam );
        SendDlgItemMessage(
            dialog,
            IDC_AVAILABLE,
            LB_ADDSTRING,
            0,
            lParam );
    }

    // - populate the unavailable control
    for( std::list<PicamCameraID>::const_iterator i = unavailable_.begin();
         i != unavailable_.end();
         ++i )
    {
        // - create a wstring version of the camera id
        std::wostringstream woss;
        woss << GetEnumString( PicamEnumeratedType_Model, i->model )
             << L" (SN: " << i->serial_number << L")";
        std::wstring item( woss.str() );

        // - add the wstring to the control
        SendDlgItemMessage(
            dialog,
            IDC_UNAVAILABLE,
            LB_ADDSTRING,
            0,
            reinterpret_cast<LPARAM>( item.c_str() ) );
    }

    // - select the open camera
    PicamCameraID deviceID;
    if( device_ && Picam_GetCameraID( device_, &deviceID ) == PicamError_None )
    {
        piint index = 0;
        for( std::list<PicamCameraID>::const_iterator i = available_.begin();
             i != available_.end();
             ++i, ++index )
        {
            if( *i == deviceID )
            {
                SendDlgItemMessage(
                    dialog,
                    IDC_SELECTED,
                    CB_SETCURSEL,
                    index,
                    0 );
                break;
            }
        }
    }
}

////////////////////////////////////////////////////////////////////////////////
// ConnectDemoCamera
// - connects a demo camera defined in the cameras dialog
////////////////////////////////////////////////////////////////////////////////
void ConnectDemoCamera( HWND dialog )
{
    // - get selected demo camera model (if any)
    INT_PTR index =
        SendDlgItemMessage( dialog, IDC_DEMO, CB_GETCURSEL, 0, 0 );
    LRESULT data =
        SendDlgItemMessage( dialog, IDC_DEMO, CB_GETITEMDATA, index, 0 );
    if( index == -1 ||data == CB_ERR )
        return;

    // - get the serial number
    wchar_t text[1024];
    if( !GetDlgItemText( dialog, IDC_SERIAL_NUMBER, text, sizeof( text ) ) )
    {
        DisplayError( L"Serial number required." );
        return;
    }
    std::wstring wideSerialNumber( text );

    // - connect the model
    PicamModel model = static_cast<PicamModel>( data );
    std::string serialNumber(
        wideSerialNumber.begin(),
        wideSerialNumber.end() );
    PicamError error =
        Picam_ConnectDemoCamera( model, serialNumber.c_str(), 0 );
    if( error != PicamError_None )
        DisplayError( L"Failed to connect demo camera.", error );
}

////////////////////////////////////////////////////////////////////////////////
// ApplyCamerasDialog
// - handles acceptance from the cameras dialog
// - takes the lock
////////////////////////////////////////////////////////////////////////////////
void ApplyCamerasDialog( HWND dialog )
{
    // - lock before accessing shared state
    AutoLock al( lock_ );

    // - reset cameras dialog window handle
    cameras_ = 0;

    // - set result to selected camera id (if any)
    INT_PTR result = 0;
    INT_PTR index =
        SendDlgItemMessage( dialog, IDC_SELECTED, CB_GETCURSEL, 0, 0 );
    LRESULT size =
        SendDlgItemMessage( dialog, IDC_SELECTED, CB_GETLBTEXTLEN, index, 0 );
    if( index != -1 && size != CB_ERR )
    {
        // - copy the selected string
        std::wstring selected;
        std::vector<wchar_t> buffer( size+1 );
        LPARAM lParam = reinterpret_cast<LPARAM>( &buffer[0] );
        LRESULT status =
            SendDlgItemMessage(
                dialog,
                IDC_SELECTED,
                CB_GETLBTEXT,
                index,
                lParam );
        if( status != CB_ERR )
        {
            selected.resize( buffer.size()-1 );
            std::copy( buffer.begin(), buffer.end()-1, selected.begin() );
        }

        // - find a matching available id
        for( std::list<PicamCameraID>::const_iterator i = available_.begin();
             i != available_.end() && !selected.empty();
             ++i )
        {
            // - create a wstring version of the camera id
            std::wostringstream woss;
            woss << GetEnumString( PicamEnumeratedType_Model, i->model )
                 << L" (SN: " << i->serial_number << L")";

            // - set the result if a match is found
            if( selected == woss.str() )
            {
                result = reinterpret_cast<INT_PTR>( new PicamCameraID( *i ) );
                break;
            }
        }
    }

    // - release lock after accessing shared state
    al.Release();

    EndDialog( dialog, result );
}

////////////////////////////////////////////////////////////////////////////////
// CancelCamerasDialog
// - handles cancelation from the cameras dialog
// - takes the lock
////////////////////////////////////////////////////////////////////////////////
void CancelCamerasDialog( HWND dialog )
{
    // - reset cameras dialog window handle
    AutoLock al( lock_ );
    cameras_ = 0;
    al.Release();

    EndDialog( dialog, 0 );
}

////////////////////////////////////////////////////////////////////////////////
// CamerasDialogProc
// - camera selection dialog window procedure
////////////////////////////////////////////////////////////////////////////////
INT_PTR CALLBACK CamerasDialogProc(
    HWND hwndDlg,
    UINT uMsg,
    WPARAM wParam,
    LPARAM lParam )
{
    UNREFERENCED_PARAMETER( lParam );

    switch( uMsg )
    {
        case WM_INITDIALOG:
            InitializeCamerasDialog( hwndDlg );
            break;
        case WM_CLOSE:
            wParam = IDCANCEL;
            // - fall through
        case WM_COMMAND:
            switch( LOWORD( wParam ) )
            {
                case IDC_CONNECT:
                    ConnectDemoCamera( hwndDlg );
                    break;
                case IDOK:
                    ApplyCamerasDialog( hwndDlg );
                    break;
                case IDCANCEL:
                    CancelCamerasDialog( hwndDlg );
                    break;
                default:
                    return false;
            }
            break;
        case WM_REFRESH_CAMERAS:
            RefreshCamerasDialog( hwndDlg );
            break;
        default:
            return false;
    }

    return true;
}

//##############################################################################
//##############################################################################
//##############################################################################
//##############################################################################
// Main Window
//##############################################################################
//##############################################################################
//##############################################################################
//##############################################################################
////////////////////////////////////////////////////////////////////////////////
// ProcessMenuCommand
// - handles main window menu
////////////////////////////////////////////////////////////////////////////////
void ProcessMenuCommand( piint id )
{
    switch( id )
    {
        case ID_FILE_SAVEFRAME:
            SaveFrame();
            break;
        case ID_FILE_QUIT:
            DestroyWindow( main_ );
            break;
        case ID_CONFIGURE_SETEXPOSURETIME:
            SetExposureTime();
            break;
        case ID_CONFIGURE_SETREPETITIVEGATE:
            SetRepetitiveGate();
            break;
        case ID_CONFIGURE_SETPARAMETERS:
            SetParameters();
            break;
        case ID_CONFIGURE_SELECTCAMERA:
            SelectCamera( false /*selectDefault*/ );
            break;
        case ID_ACQUISITION_PREVIEW:
            Preview();
            break;
        case ID_ACQUISITION_ACQUIRE:
            Acquire();
            break;
        case ID_ACQUISITION_STOP:
            Stop();
            break;
    }
}

////////////////////////////////////////////////////////////////////////////////
// Redraw
// - repaints the main window
// - takes the lock
////////////////////////////////////////////////////////////////////////////////
void Redraw()
{
    PAINTSTRUCT ps;
    BeginPaint( main_, &ps );

    // - do nothing if no bitmap created yet
    if( !bmp_ )
    {
        EndPaint( main_, &ps );
        return;
    }

    // - get the bounding area
    RECT bounds;
    if( !GetClientRect( main_, &bounds ) )
    {
        EndPaint( main_, &ps );
        return;
    }

    // - update shared bitmap information
    piint bitmapWidth, bitmapHeight;
    AutoLock al( lock_ );
    if( !renderedImage_ )
    {
        EndPaint( main_, &ps );
        return;
    }
    bitmapWidth = imageDataWidth_;
    bitmapHeight = imageDataHeight_;
    if( bitmapVersion_ != renderedImageVersion_ )
    {
        std::memcpy( bmpBits_, &(*renderedImage_)[0], renderedImage_->size() );
        bitmapVersion_ = renderedImageVersion_;
    }
    al.Release();

    // - determine best-fit scaling
    piflt scaleWidth  = static_cast<piflt>( bounds.right  ) / bitmapWidth;
    piflt scaleHeight = static_cast<piflt>( bounds.bottom ) / bitmapHeight;
    piflt scale = std::min( scaleWidth, scaleHeight );

    // - determine image area
    piint width  = static_cast<piint>( bitmapWidth*scale  + 0.5 );
    piint height = static_cast<piint>( bitmapHeight*scale + 0.5 );
    piint x = static_cast<piint>( std::abs( width-bounds.right   )/2 + 0.5 );
    piint y = static_cast<piint>( std::abs( height-bounds.bottom )/2 + 0.5 );

    // - update window
    StretchBlt(
        dc_,
        x,
        y,
        width,
        height,
        backSurface_,
        0,
        0,
        bitmapWidth,
        bitmapHeight,
        SRCCOPY );

    EndPaint( main_, &ps );
}


string GetParametersAsString() {

	string returnstring = "";
	// - get the camera model
	PicamHandle model;
	PicamError error = PicamAdvanced_GetCameraModel(device_, &model);
	if (error != PicamError_None)
	{
		DisplayError(L"Failed to get camera model.", error);
		return "Failed to get camera model.";
	}

	// - initialize the parameter combo box
	const PicamParameter* parameters;
	piint count;
	error = Picam_GetParameters(model, &parameters, &count);
	if (error != PicamError_None)
	{
		DisplayError(L"Failed to get camera parameters.", error);
		return "Failed to get camera parameters.";
	}
	for (piint i = 0; i < count; ++i)
	{
		// - create a wstring version of the parameter
		std::wstring item =
			GetEnumString(PicamEnumeratedType_Parameter, parameters[i]) + L": ";
		
		// - show the format
		PicamValueType valueType;
		error = Picam_GetParameterValueType(model, parameters[i], &valueType);
		if (error != PicamError_None)
		{
			DisplayError(L"Failed to get parameter value type.", error);
			return "Failed to get parameter value type.";
		}
		wstring text = GetEnumString(PicamEnumeratedType_ValueType, valueType);
		switch (valueType)
		{
		case PicamValueType_Integer:
		case PicamValueType_LargeInteger:
		case PicamValueType_FloatingPoint:
			break;
		case PicamValueType_Boolean:
			text += L" (false = 0, true = non-0)";
			break;
		case PicamValueType_Enumeration:
			text += L" (as integer value)";
			break;
		case PicamValueType_Rois:
			text += L" (as 'x,y w,h xb,yb')";
			break;
		case PicamValueType_Pulse:
			text += L" (as 'd,w')";
			break;
		case PicamValueType_Modulations:
			text += L" (as 'd,f,p,osf d,f,p,osf...')";
			break;
		}
		item=item+text+L": ";

		// - show the value
		std::wstring formatted;
		if (!GetParameterValue(parameters[i], text, formatted))
			break;
		item = item + text + L" ";
		item = item + formatted;

		returnstring = returnstring + ws2s(item) + "\n";
	}
	Picam_DestroyParameters(parameters);

	return returnstring;
} 

void RefreshParametersNoDialog()
{
	// - get the camera model
	PicamHandle model;
	PicamError error = PicamAdvanced_GetCameraModel(device_, &model);
	if (error != PicamError_None)
	{
		DisplayError(L"Failed to get camera model.", error);
		return;
	}

	// - revert changes on the model
	// - any changes to the model will be handled through change callbacks
	error = PicamAdvanced_RefreshParametersFromCameraDevice(model);
	if (error != PicamError_None)
	{
		DisplayError(L"Failed to refresh camera model.", error);
		return;
	}

	return;
}

//////////////////////////////////////////////////////////////////////////////////
//   ListenOnPort(int PortNo)
//
//   This function initializes Winsock and starts a listening socket on the
//      port specified by PortNo. It returns an integer which indicates whether
//      an error occurred, and if so, which error. If successful, returns 1.
//      -1: Could not initialize Winsock
//      -2: Invalid Winsock version
//      -3: Could not create socket
//      -4: Could not bind to IP
//////////////////////////////////////////////////////////////////////////////////
int ListenOnPort(short int PortNo)
{
	
    WSADATA w;
	
    int error = WSAStartup (0x0202, &w);   // Fill in WSA info
     
    if (error)
    { // there was an error
        //SendMessage(hStatus, WM_SETTEXT, 0, (LPARAM)"Could not initialize Winsock.");
      return -1;
    }
    if (w.wVersion != 0x0202)
    { // wrong WinSock version!
      WSACleanup (); // unload ws2_32.dll
      //SendMessage(hStatus, WM_SETTEXT, 0, (LPARAM)"Wrong Winsock version.");
      return -2;
    }
    
    SOCKADDR_IN addr; // the address structure for a TCP socket
    //SOCKET client; //The connected socket handle
    
    addr.sin_family = AF_INET;      // Address family Internet
    addr.sin_port = htons (PortNo);   // Assign port to this socket
    addr.sin_addr.s_addr = inet_addr ("127.0.0.1");   // No destination
    
    s = socket (AF_INET, SOCK_STREAM, IPPROTO_TCP); // Create socket
    
    if (s == INVALID_SOCKET)
    {
        //SendMessage(hStatus, WM_SETTEXT, 0, (LPARAM)"Could not create socket.");
        return -3;
    }
    
    if (bind(s, (LPSOCKADDR)&addr, sizeof(addr)) == SOCKET_ERROR) //Try binding
    { // error
        //SendMessage(hStatus, WM_SETTEXT, 0, (LPARAM)"Could not bind to IP.");
        return -4;
    }
    
    listen(s, 10); //Start listening
    WSAAsyncSelect (s, main_, WINSOCK_MESSAGE, FD_READ | FD_CONNECT | FD_CLOSE | FD_ACCEPT); //Switch to Non-Blocking mode
    
    //char szTemp[100];
    //wsprintf(szTemp, "Listening on port %d...", PortNo);
    
    //SendMessage(hStatus, WM_SETTEXT, 0, (LPARAM)szTemp);  
    return 1;
}

///////////////////////////////////////////////////////////////////
//   ParseInput
//   Parses input received from Python.
//   Input is passed in a character array 'buffer'
//        Length of input is passed in int 'datalen'
//   Commands are of the form:
//        byte num		Function
//		  0-3			MESG: indicates the packet contains a message
//		  4-7			4-byte int indicating the length of the message
//		  8-11			4-character command code
//		  13-			Argument list for command, separated by spaces (char 12 is also a space)
//
//  Valid command codes:
//		ROI : Set a region of interest
//		CMTP: Commit parameters to camera
//		STAQ: Start Acquisition
//		STVD: Start Video
//		HLAQ: Halt Acquisition
//		ACQI: Acquire Image
//		SPFP: Set Parameter, Floating Point
//		SPIN: Set Parameter, Integer
//		SPLI: Set Parameter, Long Integer
//		GPFP: Get Parameter, Floating Point
//		GPIN: Get Parameter, Integer
//		GPLI: Get Parameter, Long Integer
//		ISAR: Is Acquisition Running
//		COOL: Cooling Fan On/Off (True->On)
//		OFCM: Open First Camera
//		CDMC: Connect Demo Camera
//		Hell: Repeat 'Hello' message to client process
///////////////////////////////////////////////////////////////////
int ParseInput(char* buffer, int datalen)
{

	

	char command[5];
	strncpy_s(command, &buffer[8], 4);

	if (strcmp(command,"ROI ")==0)
	{ 
	   //use arguments given in remainder of data to set ROI

		string arglist;
		arglist = &buffer[13];
		vector<string> splitarglist;
		splitarglist = split(arglist, ' ');
		if (splitarglist.size() != 6)
		{
			wsmessage formatmesg;
			int len;
			formatmessage("Incorrect number of arguments for Set Single ROI (ROI ). Expected 6.", len, formatmesg);
			sendmessage(formatmesg);
			return -2;
		}

		PicamRoi roi;
		roi.x = stoi(splitarglist[0]);
		roi.width = stoi(splitarglist[1]);
		roi.x_binning = stoi(splitarglist[2]);
		roi.y = stoi(splitarglist[3]);
		roi.height = stoi(splitarglist[4]);
		roi.y_binning = stoi(splitarglist[5]);

		PicamRois rois = { &roi, 1 };
		PicamError error = Picam_SetParameterRoisValue(device_, PicamParameter_Rois, &rois);
		test_picam_error(error, "Failed to set single ROI.");
		string ack = "ACK ROI ";
		int len;
		wsmessage formatmesg;
		formatmessage(ack, len, formatmesg);
		sendmessage(formatmesg);

	}
	else if (strcmp(command, "ROIS") == 0)
	{
		//use arguments given in remainder of data to set ROIs

		string arglist;
		arglist = &buffer[13];
		vector<string> splitarglist;
		splitarglist = split(arglist, ' ');
		if (splitarglist.size() % 6 != 0)
		{
			wsmessage formatmesg;
			int len;
			formatmessage("Incorrect number of arguments for Set Multiple ROIs (ROIS). Expected a multiple of 6.", len, formatmesg);
			sendmessage(formatmesg);
			return -2;
		}

		int numrois = static_cast<int>(splitarglist.size()) / 6;
		PicamRoi* roi;
		roi = new PicamRoi[numrois];
		for (int roinum = 0; roinum < numrois; roinum++)
		{
			roi[roinum].x = stoi(splitarglist[0 + roinum*6]);
			roi[roinum].width = stoi(splitarglist[1 + roinum * 6]);
			roi[roinum].x_binning = stoi(splitarglist[2 + roinum * 6]);
			roi[roinum].y = stoi(splitarglist[3 + roinum * 6]);
			roi[roinum].height = stoi(splitarglist[4 + roinum * 6]);
			roi[roinum].y_binning = stoi(splitarglist[5 + roinum * 6]);
		}

		PicamRois rois = { roi, numrois };
		PicamError error = Picam_SetParameterRoisValue(device_, PicamParameter_Rois, &rois);
		test_picam_error(error, "Failed to set ROIs.");
		string ack = "ACK ROIS";
		int len;
		wsmessage formatmesg;
		formatmessage(ack, len, formatmesg);
		sendmessage(formatmesg);

	}
	else if (strcmp(command,"PARS")==0)
	{
		//Get All Parameters As String
		string parms;
		parms = GetParametersAsString();
		wsmessage formatmesg;
		int len;
		formatmessage(parms,len,formatmesg);
		sendmessage(formatmesg);
		RefreshParametersNoDialog();
	}
	else if (strcmp(command, "AQMI") == 0)
	{
		//Acquire multiple images

		string arglist;
		arglist = &buffer[13];
		vector<string> splitarglist;
		splitarglist = split(arglist, ' ');
		if (splitarglist.size() != 1)
		{
			wsmessage formatmesg;
			int len;
			formatmessage("Incorrect number of arguments for Acquire Multiple Images (AQMI). Expected 1.", len, formatmesg);
			sendmessage(formatmesg);
			return -2;
		}
		piint numreads = stoi(splitarglist[0]);

		PicamAcquisitionErrorsMask errormask;
		PicamAvailableData avail;
		PicamError error;
		error = Picam_Acquire(device_, numreads, 5000, &avail, &errormask);
		test_picam_error(error, "Could not acquire images ");

		if (errormask != 0)
		{
			wsmessage formatmesg;
			int len;
			string readouterr = "Acquisition Error: ";
			readouterr.append(to_string((int)errormask));
			formatmessage(readouterr, len, formatmesg);
			sendmessage(formatmesg);
			return -9;
		}

		if (avail.readout_count < numreads)
		{
			wsmessage formatmesg;
			int len;
			string readouterr = "Too few readouts available: ";
			readouterr.append(to_string(avail.readout_count));
			formatmessage(readouterr, len, formatmesg);
			sendmessage(formatmesg);
			return -8;
		}
		

		string ack = "ACK AQMI ";
		int len;
		std::vector<pi16u>* idat;
		idat = new vector<pi16u>[numreads];
		
		CacheFrameNavigation();

		for (int i = 0; i < numreads; i++)
		{
			
			
			idat[i].resize(frameSize_ / sizeof(pi16u));
			pi64s lastReadoutOffset = readoutStride_ * (avail.readout_count - numreads + i);
			pi64s lastFrameOffset = frameStride_ * (framesPerReadout_ - 1);
			const pibyte* frame =
				static_cast<const pibyte*>(avail.initial_readout) +
				lastReadoutOffset + lastFrameOffset;

			//MessageBox(main_, to_wstring(static_cast<int>((&idat[i])->size())).c_str(), L"idat", 0);
			//MessageBox(main_, to_wstring(lastReadoutOffset).c_str(), L"", 0);

			std::memcpy(&(idat[i][0]), frame, frameSize_);

			//MessageBox(main_, to_wstring(lastFrameOffset).c_str(), L"", 0);
			//MessageBox(main_, to_wstring((int)frame).c_str(), L"", 0);
		}
		wsmessageimagedata formatmesg;
		formatmessageimagemult(ack, len, formatmesg, idat[0], static_cast<int>((&idat[0])->size()));
		sendmessageimagemult(formatmesg, idat, numreads);

	}
	else if (strcmp(command, "GNNI") == 0)
	{
		//Get Number of New Images
		
		pi64s numreadouts = availabledata.readout_count;
		string ack = "ACK GNNI ";
		ack.append(to_string(numreadouts));
		int len;
		wsmessage formatmesg;
		formatmessage(ack, len, formatmesg);
		sendmessage(formatmesg);
	}
	else if (strcmp(command, "STVD") == 0)
	{
		//Start Video (used in place of Start Acquisition for displaying continuous video)
		Preview();
		string ack = "ACK STVD";
		int len;
		wsmessage formatmesg;
		formatmessage(ack, len, formatmesg);
		sendmessage(formatmesg);
	}
	else if (strcmp(command, "CLOS") == 0)
	{
		//Close Camera
		if (device_)
		{
			// - close the current camera
			PicamError error = PicamAdvanced_CloseCameraDevice(device_);
			if (error != PicamError_None)
				DisplayError(L"Failed to close camera.", error);
			string ack = "ACK CLOS";
			int len;
			wsmessage formatmesg;
			formatmessage(ack, len, formatmesg);
			sendmessage(formatmesg);
		}
		else
		{
			string ack = "Failed to close camera; No camera open.";
			int len;
			wsmessage formatmesg;
			formatmessage(ack, len, formatmesg);
			sendmessage(formatmesg);
		}
		if (client)
		{
			char yes = '1';
			if (setsockopt(client, SOL_SOCKET, SO_REUSEADDR, &yes, sizeof(yes)) == -1) {
				perror("setsockopt");
				exit(1);
			}
			closesocket(client);
		}
	}
	else if (strcmp(command, "CMTP") == 0)
	{
		//Commit Parameters
		piint failedparamcount;
		const PicamParameter *failedparams;
		PicamError error = Picam_CommitParameters(device_, &failedparams, &failedparamcount);
		test_picam_error(error,"Failed to commit parameters. ");
		if (failedparamcount > 0)
		{
			wsmessage formatmesg;
			int len;
			formatmessage("Some parameters failed to be committed.", len, formatmesg);
			sendmessage(formatmesg);
			return -5;
		}
		string ack = "ACK CMTP";
		int len;
		wsmessage formatmesg;
		formatmessage(ack, len, formatmesg);
		sendmessage(formatmesg);
	}
	else if (strcmp(command, "STAQ") == 0)
	{
		//Start Acquisition
		/*PicamError error =
			PicamAdvanced_RegisterForAcquisitionUpdated(
			device_,
			AcquisitionUpdated);
		if (error != PicamError_None)
			DisplayError(L"Failed to register for acquisition updated.", error);*/
		Start();
		string ack = "ACK STAQ";
		int len;
		wsmessage formatmesg;
		formatmessage(ack, len, formatmesg);
		sendmessage(formatmesg);
	}
	else if (strcmp(command, "RFAU") == 0)
	{
		//Kill Callback (used in Experiment mode when shotsPerMeasurement > 1), 
		//to prevent the callback function from clearing the acquisition buffer after each readout.
		PicamError error =
			PicamAdvanced_RegisterForAcquisitionUpdated(
			device_,
			AcquisitionUpdated);
		if (error != PicamError_None)
			DisplayError(L"Failed to register for acquisition updated.", error);

		string ack = "ACK RFAU";
		int len;
		wsmessage formatmesg;
		formatmessage(ack, len, formatmesg);
		sendmessage(formatmesg);
	}
	else if (strcmp(command, "KLCB") == 0)
	{
		//Kill Callback (used in Experiment mode when shotsPerMeasurement > 1), 
		//to prevent the callback function from clearing the acquisition buffer after each readout.
		PicamError error =
			PicamAdvanced_UnregisterForAcquisitionUpdated(
			device_,
			AcquisitionUpdated);
		if (error != PicamError_None)
			DisplayError(L"Failed to unregister for acquisition updated.", error);

		string ack = "ACK KLCB";
		int len;
		wsmessage formatmesg;
		formatmessage(ack, len, formatmesg);
		sendmessage(formatmesg);
	}
	else if (strcmp(command, "HLAQ") == 0)
	{
		//Halt Acquisition
		Stop();
		string ack = "ACK HLAQ";
		int len;
		wsmessage formatmesg;
		formatmessage(ack, len, formatmesg);
		sendmessage(formatmesg);
	}
	else if (strcmp(command, "ACQI") == 0)
	{
		//Acquire Image
		if (!bmpBits_)
		{
			wsmessage formatmesg;
			int len;
			formatmessage("bmpBits_ not initialized.",len,formatmesg);
			sendmessage(formatmesg);
			return -1;
		}
		Redraw();

		string ack = "ACK ACQI ";
		int len;
		wsmessageimagedata formatmesg;
		formatmessageimage(ack, len, formatmesg, (imageData_)[0], static_cast<int>((&imageData_)->size()));
		sendmessageimage(formatmesg);


	}
	else if (strcmp(command, "ACQJ") == 0)
	{
		string arglist;
		arglist = &buffer[13];
		vector<string> splitarglist;
		splitarglist = split(arglist, ' ');
		if (splitarglist.size() != 2)
		{
			wsmessage formatmesg;
			int len;
			formatmessage("Incorrect number of arguments for Index Acquire Image (ACQJ). Expected 1.", len, formatmesg);
			sendmessage(formatmesg);
			return -2;
		}
		piint imnum = stoi(splitarglist[0]);
		//Acquire Image
		if (!bmpBits_)
		{
			wsmessage formatmesg;
			int len;
			formatmessage("bmpBits_ not initialized.", len, formatmesg);
			sendmessage(formatmesg);
			return -1;
		}
		Redraw();

		string ack = "ACK ACQJ ";
		int len;
		wsmessageimagedata formatmesg;
		formatmessageimage(ack, len, formatmesg, (imageData_)[imnum], static_cast<int>((&imageData_)->size()));
		sendmessageimage(formatmesg);


	}
	else if (strcmp(command, "SPFP") == 0)
	{
		//Set Parameter, Floating Point
		string arglist;
		arglist = &buffer[13];
		vector<string> splitarglist;
		splitarglist = split(arglist, ' ');
		if (splitarglist.size() != 2)
		{
			wsmessage formatmesg;
			int len;
			formatmessage("Incorrect number of arguments for Set Floating Point Parameter (SPFP). Expected 2.", len, formatmesg);
			sendmessage(formatmesg);
			return -2;
		}

		PicamParameter param = (enum PicamParameter)stoi(splitarglist[0]);
		piflt value = stod(splitarglist[1]);

		PicamError error = Picam_SetParameterFloatingPointValue(device_, param, value);
		test_picam_error(error, "Failed to Set Floating Point Parameter. ");
		string ack = "ACK SPFP";
		int len;
		wsmessage formatmesg;
		formatmessage(ack, len, formatmesg);
		sendmessage(formatmesg);
	}
	else if (strcmp(command, "SPIN") == 0)
	{
		//Set Parameter, Integer
		string arglist;
		arglist = &buffer[13];
		vector<string> splitarglist;
		splitarglist = split(arglist, ' ');
		if (splitarglist.size() != 2)
		{
			wsmessage formatmesg;
			int len;
			formatmessage("Incorrect number of arguments for Set Floating Point Parameter (SPFP). Expected 2.", len, formatmesg);
			sendmessage(formatmesg);
			return -2;
		}

		PicamParameter param = (enum PicamParameter)stoi(splitarglist[0]);
		piint value = stoi(splitarglist[1]);

		PicamError error = Picam_SetParameterIntegerValue(device_, param, value);
		test_picam_error(error, "Failed to Set Integer Parameter. ");
		string ack = "ACK SPIN";
		int len;
		wsmessage formatmesg;
		formatmessage(ack, len, formatmesg);
		sendmessage(formatmesg);
	}
	else if (strcmp(command, "SPLI") == 0)
	{
		//Set Parameter, Long Integer
		string arglist;
		arglist = &buffer[13];
		vector<string> splitarglist;
		splitarglist = split(arglist, ' ');
		if (splitarglist.size() != 2)
		{
			wsmessage formatmesg;
			int len;
			formatmessage("Incorrect number of arguments for Set Long Integer Parameter (SPLI). Expected 2.", len, formatmesg);
			sendmessage(formatmesg);
			return -2;
		}

		PicamParameter param = (enum PicamParameter)stoi(splitarglist[0]);
		pi64s value = stol(splitarglist[1]);

		PicamError error = Picam_SetParameterLargeIntegerValue(device_, param, value);
		test_picam_error(error, "Failed to Set Long Integer Parameter. ");
		string ack = "ACK SPLI";
		int len;
		wsmessage formatmesg;
		formatmessage(ack, len, formatmesg);
		sendmessage(formatmesg);
	}
	else if (strcmp(command, "GPFP") == 0)
	{
		//Get Parameter, Floating Point
		string arglist;
		arglist = &buffer[13];
		vector<string> splitarglist;
		splitarglist = split(arglist, ' ');
		if (splitarglist.size() != 1)
		{
			wsmessage formatmesg;
			int len;
			formatmessage("Incorrect number of arguments for Get Floating Point Parameter (GPFP). Expected 1.", len, formatmesg);
			sendmessage(formatmesg);
			return -2;
		}

		PicamParameter param = (enum PicamParameter)stoi(splitarglist[0]);
		piflt value;

		PicamError error = Picam_GetParameterFloatingPointValue(device_, param, &value);
		test_picam_error(error, "Failed to Get Floating Point Parameter. ");
		string ack = "ACK GPFP ";
		ack.append(to_string(value));
		int len;
		wsmessage formatmesg;
		formatmessage(ack, len, formatmesg);
		sendmessage(formatmesg);
	}
	else if (strcmp(command, "GPIN") == 0)
	{
		//Get Parameter, Integer
		string arglist;
		arglist = &buffer[13];
		vector<string> splitarglist;
		splitarglist = split(arglist, ' ');
		if (splitarglist.size() != 1)
		{
			wsmessage formatmesg;
			int len;
			formatmessage("Incorrect number of arguments for Get Integer Parameter (GPIN). Expected 1.", len, formatmesg);
			sendmessage(formatmesg);
			return -2;
		}

		PicamParameter param = (enum PicamParameter)stoi(splitarglist[0]);
		piint value;

		PicamError error = Picam_GetParameterIntegerValue(device_, param, &value);
		test_picam_error(error, "Failed to Get Integer Parameter. ");
		string ack = "ACK GPIN ";
		ack.append(to_string(value));
		int len;
		wsmessage formatmesg;
		formatmessage(ack, len, formatmesg);
		sendmessage(formatmesg);
	}
	else if (strcmp(command, "GPLI") == 0)
	{
		//Get Parameter, Long Int
		string arglist;
		arglist = &buffer[13];
		vector<string> splitarglist;
		splitarglist = split(arglist, ' ');
		if (splitarglist.size() != 1)
		{
			wsmessage formatmesg;
			int len;
			formatmessage("Incorrect number of arguments for Get Long Integer Parameter (GPLI). Expected 1.", len, formatmesg);
			sendmessage(formatmesg);
			return -2;
		}

		PicamParameter param = (enum PicamParameter)stoi(splitarglist[0]);
		pi64s value;

		PicamError error = Picam_GetParameterLargeIntegerValue(device_, param, &value);
		test_picam_error(error, "Failed to Get Floating Point Parameter. ");
		string ack = "ACK GPLI ";
		ack.append(to_string(value));
		int len;
		wsmessage formatmesg;
		formatmessage(ack, len, formatmesg);
		sendmessage(formatmesg);
	}
	else if (strcmp(command, "ISAR") == 0)
	{
		//IsAcquisitionRunning
		pibln running;
		PicamError error =
			Picam_IsAcquisitionRunning(device_, &running);
		test_picam_error(error, "Failed to determine if acquiring.");
		
		wsmessage formatmesg;
		int len;
		string runst;
		if (running)
		{
			runst = '1';
		}
		else
		{
			runst = '0';
		}
		string ackisar = "ACK ISAR ";
		ackisar.append(runst);
		formatmessage(ackisar, len, formatmesg);
		sendmessage(formatmesg);
	}
	else if (strcmp(command, "COOL") == 0)
	{
		//Turn Cooling Fan on/off
		string arglist;
		arglist = &buffer[13];
		vector<string> splitarglist;
		splitarglist = split(arglist, ' ');
		if (splitarglist.size() != 1)
		{
			wsmessage formatmesg;
			int len;
			formatmessage("Incorrect number of arguments for Cooling Fan (COOL). Expected 1.", len, formatmesg);
			sendmessage(formatmesg);
			return -2;
		}

		int cooling = stoi(splitarglist[0]);

		PicamError error = Picam_SetParameterIntegerValue(device_,PicamParameter_DisableCoolingFan,!cooling);
		test_picam_error(error, "Failed to Set Cooling Fan: ");

		wsmessage formatmesg;
		int len;
		formatmessage("ACK COOL",len,formatmesg);
		sendmessage(formatmesg);
	}
	else if (strcmp(command, "OFCM") == 0)
	{
		//Open First Camera
		//Takes no arguments
		const PicamCameraID* id = 0;
		if (!available_.empty())
		{
			id = new PicamCameraID(available_.front());
		}
		else
		{
			wsmessage formatmesg;
			int len;
			formatmessage("No available cameras.", len, formatmesg);
			sendmessage(formatmesg);
			return -1;
		}
		OpenCamera(*id);
		//test_picam_error(error, "Failed to Open First Camera: ");

		wsmessage formatmesg;
		int len;
		formatmessage("ACK OFCM", len, formatmesg);
		sendmessage(formatmesg);
	}
	else if (strcmp(command, "CDMC") == 0)
	{
		//Connect Demo Camera
		//Expects two arguments:
		//  int: model number
		//  string: serial number
		string arglist;
		arglist = &buffer[13];
		vector<string> splitarglist;
		splitarglist = split(arglist, ' ');
		if (splitarglist.size() != 2)
		{
			wsmessage formatmesg;
			int len;
			formatmessage("Incorrect number of arguments for Connect Demo Camera (CDMC). Expected 2.",len,formatmesg);
			sendmessage(formatmesg);
			return -2;
		}
		PicamModel democammodel = (PicamModel)stoi(splitarglist[0]);
		string democamserial = splitarglist[1];

		PicamError error =
			Picam_ConnectDemoCamera(democammodel, democamserial.c_str(), 0);
		if (error != PicamError_None)
		{
			wsmessage formatmesg;
			int len;
			formatmessage("Failed to connect demo camera.",len,formatmesg);
			sendmessage(formatmesg);
			return -3;
		}

		wsmessage formatmesg;
		int len;
		formatmessage("ACK CDMC", len, formatmesg);
		sendmessage(formatmesg);

	}
	else if (strcmp(command, "Hell") == 0)
	{
		//Repeats "Hello" message from Python as a test.
		string dispmess;
		dispmess.append(&buffer[8]);
		
		int len;
		len = datalen;
		wsmessage formatmesg;
		formatmessage(dispmess, len, formatmesg);
		sendmessage(formatmesg);
		
	}
    
    
   return 0;   
}

int test_picam_error(PicamError error, string errmess)
{
	if (error != PicamError_None)
	{
		wsmessage formatmesg;
		int len;
		char errnum[50];
		sprintf_s(errnum, "%d", (int)error);
		errmess.append(ws2s(GetEnumString(PicamEnumeratedType_Error, error)));
		formatmessage(errmess, len, formatmesg);
		sendmessage(formatmesg);
		return -3;
	}
	return 0;
}



std::vector<std::string> &split(const std::string &s, char delim, std::vector<std::string> &elems) {
	std::stringstream ss(s);
	std::string item;
	while (std::getline(ss, item, delim)) {
		elems.push_back(item);
	}
	return elems;
}


std::vector<std::string> split(const std::string &s, char delim) {
	std::vector<std::string> elems;
	split(s, delim, elems);
	return elems;
}



int formatmessage(string message, int &length, wsmessage &formattedmessage)
{
	length = static_cast<int>(message.length());
	formattedmessage.message = new char[length+1];
	strncpy_s(formattedmessage.mesg,5,"MESG",4);
	formattedmessage.len = length;
	strncpy_s(formattedmessage.message, length + 1, message.c_str(), length);

	return 0;
}

int sendmessage(wsmessage formatmesg)
{
	INT32 chicken = htonl(formatmesg.len);

	send(client, (char *)&formatmesg.mesg, sizeof(formatmesg.mesg) - 1, 0);
	send(client, (char *)&chicken, sizeof(formatmesg.len), 0);
	send(client, formatmesg.message, formatmesg.len, 0);

	return 0;
}


int formatmessageimage(string message, int &length, wsmessageimagedata &formattedmessage, char16_t &imagedat, int imagelen)
{
	length = static_cast<int>(message.length());
	formattedmessage.message = new char[length + 1];
	//int totallength = length + imagelen;
	strncpy_s(formattedmessage.mesg, 5, "MESG", 4);
	formattedmessage.len = length;
	strncpy_s(formattedmessage.message, length + 1, message.c_str(), length);
	formattedmessage.imagedat = &imagedat;
	formattedmessage.imagelen = imagelen;

	return 0;
}

int sendmessageimage(wsmessageimagedata formatmesg)
{
	INT32 chicken = htonl(formatmesg.len+formatmesg.imagelen*2);
	char16_t *image;
	image = new char16_t[formatmesg.imagelen];
	for (int i = 0; i < formatmesg.imagelen; i=i+1)
	{
		image[i] = formatmesg.imagedat[i];
	}

	send(client, (char *)&formatmesg.mesg, sizeof(formatmesg.mesg) - 1, 0);
	send(client, (char *)&chicken, sizeof(chicken), 0);
	send(client, formatmesg.message, formatmesg.len, 0);
	send(client, (char *)image, formatmesg.imagelen * 2, 0);

	/*
	string munchy = to_string(formatmesg.imagelen);
	wstring wmunchy;
	StringToWString(wmunchy, munchy);
	DisplayError(wmunchy);
	*/

	return 0;
}

int formatmessageimagemult(string message, int &length, wsmessageimagedata &formattedmessage, vector<char16_t> &imagedat, int imagelen)
{
	length = static_cast<int>(message.length());
	formattedmessage.message = new char[length + 1];
	//int totallength = length + imagelen;
	strncpy_s(formattedmessage.mesg, 5, "MESG", 4);
	formattedmessage.len = length;
	strncpy_s(formattedmessage.message, length + 1, message.c_str(), length);
	formattedmessage.imagedat = &imagedat[0];
	formattedmessage.imagelen = imagelen;

	return 0;
}

int sendmessageimagemult(wsmessageimagedata formatmesg, vector<pi16u>* imgs, int imgssize)
{
	
	INT32 chicken = htonl(formatmesg.len + (imgssize)*formatmesg.imagelen * 2);
	//MessageBox(main_, to_wstring(imgssize).c_str(), L"imgssize", 0);
	//MessageBox(main_, to_wstring(formatmesg.imagelen*2).c_str(), L"imagelen*2", 0);
	/*char16_t *image;
	image = new char16_t[formatmesg.imagelen];
	for (int i = 0; i < formatmesg.imagelen; i = i + 1)
	{
		image[i] = formatmesg.imagedat[i];
	}*/

	send(client, (char *)&formatmesg.mesg, sizeof(formatmesg.mesg) - 1, 0);
	send(client, (char *)&chicken, sizeof(chicken), 0);
	send(client, formatmesg.message, formatmesg.len, 0);
	stringstream imgout;
	for (int i = 0; i < imgssize; i++)
	{
		imgout << (char *)&(imgs[i][0]);
	}
	send(client, imgout.str().c_str(), imgssize * formatmesg.imagelen * 2, 0);


	return 0;
}



int StringToWString(std::wstring &ws, const std::string &s)
{
	std::wstring wsTmp(s.begin(), s.end());

	ws = wsTmp;

	return 0;
}



////////////////////////////////////////////////////////////////////////////////
// MainWindowProc
// - main window procedure
////////////////////////////////////////////////////////////////////////////////
LRESULT CALLBACK MainWindowProc(
    __in  HWND hwnd,
    __in  UINT uMsg,
    __in  WPARAM wParam,
    __in  LPARAM lParam )
{
    switch( uMsg )
    {
        case WM_DESTROY:
            PostQuitMessage( ExitCode_Success );
            break;
        case WM_COMMAND:
            ProcessMenuCommand( LOWORD( wParam ) );
            break;
        case WM_SETCURSOR:
            if( LOWORD( lParam ) == HTCLIENT )
            {
                if( busy_ )
                {
                    SetCursor( waitCursor_ );
                    return true;
                }
                else if( acquiring_ )
                {
                    SetCursor( acquiringCursor_ );
                    return true;
                }
            }
            return DefWindowProc( hwnd, uMsg, wParam, lParam );
        case WM_PAINT:
            Redraw();
            break;
        case WM_DISPLAY_ERROR:
        {
            std::wstring* message = reinterpret_cast<std::wstring*>( wParam );
            DisplayError( *message );
            delete message;
            break;
        }
        case WM_ACQUISITION_STOPPED:
            acquiring_ = false;
            break;
        case WINSOCK_MESSAGE:
			//ParseInput("WINSOCK_MESSAGE");
            switch(lParam)
                {
                case FD_CONNECT:
					//ParseInput("Connection made");
                    break;
                    
                case FD_CLOSE:
					DisplayError(L"Connection closed");
					if (s) closesocket(s);
					WSACleanup();
					ListenOnPort(PORTNO);
                    break;
                    
				case FD_READ:
				{
					//ParseInput("Reading...");
					char buffer[80];
					memset(buffer, 0, sizeof(buffer)); //Clear the buffer

					recv(client, buffer, sizeof(buffer) - 1, 0); //Get the text
					ParseInput(buffer, sizeof(buffer));// , sizeof(buffer));
				}
                    break;
                    
                case FD_ACCEPT:
					//ParseInput("Connection accepted");
					SOCKET TempSock = accept(s, (struct sockaddr*)&from, &fromlen);
					client = TempSock; //Switch our old socket to the new one
                    break;
                    
                }
            break;
        default:
            return DefWindowProc( hwnd, uMsg, wParam, lParam );
    }

    return 0;
}

////////////////////////////////////////////////////////////////////////////////
// RegisterMainWindowClass
// - registers the main window's class
////////////////////////////////////////////////////////////////////////////////
pibool RegisterMainWindowClass()
{
    // - fill the window class information
    WNDCLASSEX wc = { 0 };
    wc.cbSize = sizeof( wc );
    wc.lpszClassName = mainWindowClassName_;
    wc.lpfnWndProc = MainWindowProc;
    wc.hInstance = instance_;
    wc.style = CS_HREDRAW|CS_VREDRAW|CS_OWNDC;
    wc.hCursor = LoadCursor( 0, IDC_ARROW ); 
    wc.hIcon = LoadIcon( 0, IDI_APPLICATION ); 
    wc.hbrBackground =
        reinterpret_cast<HBRUSH>( GetStockObject( BLACK_BRUSH ) );
    wc.lpszMenuName = MAKEINTRESOURCE( IDR_MENU );

    return RegisterClassEx( &wc ) != 0;
}

////////////////////////////////////////////////////////////////////////////////
// InitializeMainWindow
// - creates and shows the main window
////////////////////////////////////////////////////////////////////////////////
pibool InitializeMainWindow( piint cmdShow )
{
    // - create the main window to be shown at default size and location
    main_ =
        CreateWindowEx(
            WS_EX_APPWINDOW,
            mainWindowClassName_,
            L"Advanced Sample",
            WS_OVERLAPPEDWINDOW,
            CW_USEDEFAULT,
            CW_USEDEFAULT,
            CW_USEDEFAULT,
            CW_USEDEFAULT,
            0,
            0,
            instance_,
            0 );
    if( !main_ ) 
        return false;

    // - initialize device contexts
    dc_ = GetDC( main_ );
    if( !dc_ )
        return false;
    if( !SetStretchBltMode( dc_, COLORONCOLOR ) )
        return false;
    backSurface_ = CreateCompatibleDC( dc_ );
    if( !backSurface_ )
        return false;

    // - create the accelerator table for the main window
    accel_ = LoadAccelerators( instance_, MAKEINTRESOURCE( IDR_ACCELERATOR ) );
    if( accel_ == 0 )
        return false;

    // - create the wait cursor
    waitCursor_ = LoadCursor( 0, IDC_WAIT );
    if( waitCursor_ == 0 )
        return false;

    // - create the acquiring cursor
    acquiringCursor_ = LoadCursor( 0, IDC_APPSTARTING );
    if( acquiringCursor_ == 0 )
        return false;

	if (cmdShow) { int i = 1; i++; }  //BS command to silence "unreferenced formal parameter" warning
    // - show the main window
    ShowWindow( main_, cmdShow );
    UpdateWindow( main_ );

    return true;
}

//##############################################################################
//##############################################################################
//##############################################################################
//##############################################################################
// Application
//##############################################################################
//##############################################################################
//##############################################################################
//##############################################################################
////////////////////////////////////////////////////////////////////////////////
// RunMessageLoop
// - application message loop
////////////////////////////////////////////////////////////////////////////////
piint RunMessageLoop()
{
    // - run until application is quit or an error in message access occurs
    for( ;; )
    {
        MSG msg;
        piint status = GetMessage( &msg, 0, 0, 0 );
        if( status == 0 )
        {
            // - application has quit, error code is stored in wParam
            return static_cast<piint>( msg.wParam );
        }
        else if( status == -1 )
        {
            // - failed to get message so exit
            return ExitCode_GetMessageFailed;
        }
        else if( (!exposure_ || !IsDialogMessage( exposure_, &msg )) &&
                 (!repetitiveGate_ || !IsDialogMessage( repetitiveGate_, &msg)))
        {
            // - process message
            if( !TranslateAccelerator( main_, accel_, &msg ) )
            {
                TranslateMessage( &msg ); 
                DispatchMessage( &msg ); 
            }
        }
    }
}

////////////////////////////////////////////////////////////////////////////////
// WinMain
// - operating system entry point
////////////////////////////////////////////////////////////////////////////////
piint CALLBACK WinMain(
    __in  HINSTANCE hInstance,
    __in  HINSTANCE hPrevInstance,
    __in  LPSTR lpCmdLine,
    __in  piint nCmdShow )
{
    UNREFERENCED_PARAMETER( hPrevInstance ); 
    UNREFERENCED_PARAMETER( lpCmdLine );

    // - store application instance
    instance_ = hInstance;

    // - create and show the main application window
    if( !RegisterMainWindowClass() )
        return ExitCode_RegisterWindowClassFailed;
    if( !InitializeMainWindow( nCmdShow ) )
        return ExitCode_InitializeMainWindowFailed;

    // - initialize state and picam
    if( !Initialize() )
        return ExitCode_FailedInitialize;

    // - try to select a default camera
    SelectCamera( true /*selectDefault*/ );

    // - process window messages until application is quit
    piint exitCode = RunMessageLoop();

    // - clean up camera
    // - note other state is reclaimed by operating system when process exits
    Uninitialize();

    return exitCode;
}
