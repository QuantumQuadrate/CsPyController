////////////////////////////////////////////////////////////////////////////////
// Advanced Sample
// - exercises the picam advanced api in a basic linux GTK application
////////////////////////////////////////////////////////////////////////////////

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
// GTK Header
////////////////////////////////////////////////////////////////////////////////
#include <gtk/gtk.h>

////////////////////////////////////////////////////////////////////////////////
// Standard C++ Library Headers
////////////////////////////////////////////////////////////////////////////////
#include <cmath>
#include <cstring>
#include <ctime>
#include <algorithm>
#include <fstream>
#include <iterator>
#include <list>
#include <sstream>
#include <string>
#include <vector>

////////////////////////////////////////////////////////////////////////////////
// Picam Header
////////////////////////////////////////////////////////////////////////////////
#include "picam_advanced.h"

//##############################################################################
//##############################################################################
//##############################################################################
//##############################################################################
// GTK Application Constants
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
    ExitCode_InitializeGtkFailed        = -1,
    ExitCode_InitializeMainWindowFailed = -2,
    ExitCode_FailedInitialize           = -3
};

////////////////////////////////////////////////////////////////////////////////
// Embedded User Interface XML
////////////////////////////////////////////////////////////////////////////////
extern "C" const gchar _binary_advanced_main_window_ui_start[];
extern "C" const gchar _binary_advanced_main_window_ui_end[];
extern "C" const gchar _binary_advanced_cameras_dialog_ui_start[];
extern "C" const gchar _binary_advanced_cameras_dialog_ui_end[];
extern "C" const gchar _binary_advanced_repetitive_gate_dialog_ui_start[];
extern "C" const gchar _binary_advanced_repetitive_gate_dialog_ui_end[];
extern "C" const gchar _binary_advanced_exposure_dialog_ui_start[];
extern "C" const gchar _binary_advanced_exposure_dialog_ui_end[];
extern "C" const gchar _binary_advanced_parameters_dialog_ui_start[];
extern "C" const gchar _binary_advanced_parameters_dialog_ui_end[];

////////////////////////////////////////////////////////////////////////////////
// Dialog Function Prototypes
////////////////////////////////////////////////////////////////////////////////
const PicamCameraID* SelectFromCamerasDialog();
void RefreshCamerasDialog();
void ConnectDemoCamera( GtkButton* button, gpointer user_data );
const PicamCameraID* ApplyCamerasDialog();
void InitializeExposureDialog();
void RefreshExposureDialog();
void ApplyExposureTimeText( GtkButton* button, gpointer user_data );
void ApplyExposureTimePosition( GtkRange* range, gpointer user_data );
void CloseExposureDialog(
    GtkDialog* dialog,
    gint response_id,
    gpointer user_data );
void InitializeRepetitiveGateDialog();
void RefreshRepetitiveGateDialog();
void ApplyRepetitiveGateDelayText( GtkButton* button, gpointer user_data );
void ApplyRepetitiveGateWidthText( GtkButton* button, gpointer user_data );
void ApplyRepetitiveGateDelayPosition( GtkRange* range, gpointer user_data );
void ApplyRepetitiveGateWidthPosition( GtkRange* range, gpointer user_data );
void CloseRepetitiveGateDialog(
    GtkDialog* dialog,
    gint response_id,
    gpointer user_data );
void ConfigureFromParametersDialog();
void UpdateParameterInformation(
    GtkComboBox* combo_box = 0,
    gpointer user_data = 0 );
void ApplyValueText( GtkButton* button, gpointer user_data );
void ClearEventLog( GtkButton* button, gpointer user_data );
void ValidateParameters( GtkButton* button, gpointer user_data );
void CommitParameters( GtkButton* button, gpointer user_data );
void RefreshParameters( GtkButton* button = 0, gpointer user_data = 0 );
void ApplyParametersDialog( GtkButton* button, gpointer user_data );
void CancelParametersDialog( GtkButton* button, gpointer user_data );

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
void LogEvent( const std::string& message );

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
// GTK Application State
////////////////////////////////////////////////////////////////////////////////
GtkWindow* main_ = 0;                   // - the main window
GdkWindow* drawingWindow_ = 0;          // - the area the image is displayed
cairo_surface_t* surface_ = 0;          // - image surface to display
pibyte* surfaceData_ = 0;               // - image surface pixel data
pi64s surfaceVersion_ = 0;              // - current version of displayed image
GdkCursor* waitCursor_ = 0;             // - the wait cursor
piint busy_ = 0;                        // - controls the wait cursor
GdkCursor* acquiringCursor_ = 0;        // - the cursor shown when acquiring
PicamHandle device_ = 0;                // - the selected camera (open)
std::vector<pibyte> buffer_;            // - acquisition circular buffer
pi64s calculatedBufferSize_ = 0;        // - calculated buffer size (bytes)
GtkBuilder* exposure_ = 0;              // - the exposure time dialog
GtkBuilder* repetitiveGate_ = 0;        // - the repetitive gate dialog
GtkBuilder* parameters_ = 0;            // - the camera parameters dialog
pibool synchronizeHScale_ = false;      // - controls entry/hscale behavior

////////////////////////////////////////////////////////////////////////////////
// Shared State
////////////////////////////////////////////////////////////////////////////////
GMutex* lock_ = 0;                      // - protects all shared state below
GtkBuilder* cameras_ = 0;               // - the camera selection dialog
std::list<PicamCameraID> available_;    // - available cameras
std::list<PicamCameraID> unavailable_;  // - unavailable cameras
piint readoutStride_ = 0;               // - stride to next readout (bytes)
piint framesPerReadout_ = 0;            // - number of frames in a readout
piint frameStride_ = 0;                 // - stride to next frame (bytes)
piint frameSize_ = 0;                   // - size of frame (bytes)
GCond* acquisitionStatusChanged_ = 0;   // - signals start/stop of acquisition
pibool acquisitionActive_ = false;      // - indicates acquisition in progress
GCond* imageDataAvailable_ = 0;         // - signals fresh image data acquired
std::vector<pi16u> imageData_;          // - data from last frame
pi64s imageDataVersion_ = 0;            // - current version of image data
piint imageDataWidth_ = 0;              // - image data width (pixels)
piint imageDataHeight_ = 0;             // - image data height (pixels)
piint surfaceDataStride_ = 0;           // - surface image stride (bytes)
std::vector<pibyte>* renderedImage_ = 0;// - rendered image surface pixel data
pi64s renderedImageVersion_ = 0;        // - current version of rendered image

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
    AutoBusy() :
        previous_(
            gdk_window_get_cursor(
                gtk_widget_get_window( GTK_WIDGET(main_) ) ) ),
        released_( false )
    {
        ++busy_;
        if( busy_ == 1 )
        {
            gdk_window_set_cursor(
                gtk_widget_get_window( GTK_WIDGET(main_) ),
                waitCursor_ );
        }
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
                gdk_window_set_cursor(
                    gtk_widget_get_window( GTK_WIDGET(main_) ),
                    previous_ );
            released_ = true;
        }
    }
    //--------------------------------------------------------------------------
private:
    AutoBusy( const AutoBusy& );            // - not implemented
    AutoBusy& operator=( const AutoBusy& ); // - not implemented
    GdkCursor* previous_;
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
    AutoLock( GMutex* lock ) : lock_( lock ), released_( false )
    { g_mutex_lock( lock_ ); }
    //--------------------------------------------------------------------------
    ~AutoLock()
    { Release(); }
    //--------------------------------------------------------------------------
    void Release()
    {
        if( !released_ )
        {
            g_mutex_unlock( lock_ );
            released_ = true;
        }
    }
    //--------------------------------------------------------------------------
private:
    AutoLock( const AutoLock& );            // - not implemented
    AutoLock& operator=( const AutoLock& ); // - not implemented
    GMutex* lock_;
    pibool released_;
};

////////////////////////////////////////////////////////////////////////////////
// Action
// - helper to post simple functions to the main thread
////////////////////////////////////////////////////////////////////////////////
class Action
{
public:
    static void Post( void (*function)() )
    {
        g_idle_add_full( G_PRIORITY_HIGH, Execute, new Action( function ), 0 );
    }
private:
    explicit Action( void (*function)() ) : function_( function )
    { }
    static gboolean Execute( gpointer user_data )
    {
        Action* action = static_cast<Action*>( user_data );
        action->function_();
        delete action;
        return false;
    }
    void (*function_)();
};

////////////////////////////////////////////////////////////////////////////////
// RgbColor
// - represents 24-bit color
////////////////////////////////////////////////////////////////////////////////
struct RgbColor
{
    pibyte blue;
    pibyte green;
    pibyte red;
    pibyte unused;
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
// - returns a string version of a picam enum
////////////////////////////////////////////////////////////////////////////////
std::string GetEnumString( PicamEnumeratedType type, piint value )
{
    const pichar* string;
    if( Picam_GetEnumerationString( type, value, &string ) == PicamError_None )
    {
        std::string s( string );
        Picam_DestroyString( string );
        return s;
    }
    return std::string();
}

////////////////////////////////////////////////////////////////////////////////
// ShowMessageDialog
// - displays a message dialog
////////////////////////////////////////////////////////////////////////////////
void ShowMessageDialog( const gchar* message )
{
    GtkWidget* dialog =
        gtk_message_dialog_new(
            main_,
            GTK_DIALOG_DESTROY_WITH_PARENT,
            GTK_MESSAGE_ERROR,
            GTK_BUTTONS_OK,
            message );
    gtk_dialog_run( GTK_DIALOG(dialog) );
    gtk_widget_destroy( dialog );
}

////////////////////////////////////////////////////////////////////////////////
// ShowPostedError
// - displays an error that was posted to the main thread
////////////////////////////////////////////////////////////////////////////////
gboolean ShowPostedError( gpointer user_data )
{
    std::string* message = static_cast<std::string*>( user_data );
    ShowMessageDialog( message->c_str() );
    delete message;

    return false;
}

////////////////////////////////////////////////////////////////////////////////
// DisplayError
// - displays an error (with optional picam error code) in a message dialog
////////////////////////////////////////////////////////////////////////////////
void DisplayError(
    const std::string& message,
    PicamError error = PicamError_None )
{
    std::string details( message );
    if( error != PicamError_None )
        details += " ("+GetEnumString( PicamEnumeratedType_Error, error )+")";
    ShowMessageDialog( details.c_str() );
}

////////////////////////////////////////////////////////////////////////////////
// PostError
// - posts an error to display in the main thread
////////////////////////////////////////////////////////////////////////////////
void PostError( const std::string& message )
{
    g_idle_add_full(
        G_PRIORITY_HIGH,
        ShowPostedError,
        new std::string( message ),
        0 );
}

////////////////////////////////////////////////////////////////////////////////
// IndicateAcquisitionCompleted
// - called to show acquisition is over
////////////////////////////////////////////////////////////////////////////////
void IndicateAcquisitionCompleted()
{
    // - nothing to indicate if main window has already closed
    if( !main_ )
        return;

    gdk_window_set_cursor( gtk_widget_get_window( GTK_WIDGET(main_) ), 0 );
}

////////////////////////////////////////////////////////////////////////////////
// WaitForAcquisitionCompleted
// - waits a long time for acquisition to complete
// - takes the lock
////////////////////////////////////////////////////////////////////////////////
pibool WaitForAcquisitionCompleted()
{
    // - set ten second time out
    GTimeVal time;
    g_get_current_time( &time );
    g_time_val_add( &time, 10 * 1e6 );

    // - take lock before accessing shared state
    AutoLock al( lock_ );
                
    // - wait for acquisition to complete
    pibool running, timedOut = false;
    do
    {
        running = acquisitionActive_;
        if( running )
            timedOut =
                !g_cond_timed_wait( acquisitionStatusChanged_, lock_, &time );
    } while( running && !timedOut );

    return !timedOut;
}

////////////////////////////////////////////////////////////////////////////////
// LoadDialog
// - loads a dialog from embedded xml and returns the builder
////////////////////////////////////////////////////////////////////////////////
GtkBuilder* LoadDialog( const gchar* uiStart, const gchar* uiEnd )
{
    // - load the dialog
    GtkBuilder* builder = gtk_builder_new();
    gint size = uiEnd - uiStart;
    GError* error = 0;
    if( !gtk_builder_add_from_string( builder, uiStart, size, &error ) )
    {
        DisplayError( error->message );
        g_error_free( error );
        g_object_unref( G_OBJECT(builder) );
        return 0;
    }

    // - set the parent
    GtkDialog* dialog = GTK_DIALOG(gtk_builder_get_object( builder, "dialog" ));
    gtk_window_set_transient_for( GTK_WINDOW(dialog), main_ );

    return builder;
}

////////////////////////////////////////////////////////////////////////////////
// ShowModalDialog
// - displays a modal dialog and returns the response
////////////////////////////////////////////////////////////////////////////////
gint ShowModalDialog( GtkDialog* dialog )
{
    // - show the modal dialog and return the response
    gtk_widget_show_all( gtk_dialog_get_content_area( dialog ) );
    gtk_widget_show_all( gtk_dialog_get_action_area( dialog ) );
    return gtk_dialog_run( dialog );
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
        al.Release();
        DisplayError( "Failed to get frame size.", error );
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
        al.Release();
        DisplayError( "Failed to get rois.", error );
        return false;
    }
    imageDataWidth_  = rois->roi_array[0].width  / rois->roi_array[0].x_binning;
    imageDataHeight_ = rois->roi_array[0].height / rois->roi_array[0].y_binning;
    Picam_DestroyRois( rois );

    // - initialize image surface
    if( surface_ )
        cairo_surface_destroy( surface_ );
    surface_ =
        cairo_image_surface_create(
            CAIRO_FORMAT_RGB24,
            imageDataWidth_,
            imageDataHeight_ );
    surfaceData_       = cairo_image_surface_get_data(   surface_ );
    surfaceDataStride_ = cairo_image_surface_get_stride( surface_ );
    renderedImage_     = 0;
    surfaceVersion_    = -1;

    // - redraw
    g_cond_signal( imageDataAvailable_ );

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
// RequestRedraw
// - requests the image drawing area to redraw
////////////////////////////////////////////////////////////////////////////////
void RequestRedraw()
{
    gdk_window_invalidate_rect(
        drawingWindow_,
        0,
        false /*invalidateChildren*/ );
}

////////////////////////////////////////////////////////////////////////////////
// UpdateImage
// - generates image surface data based on image data
// - takes the lock
////////////////////////////////////////////////////////////////////////////////
void UpdateImage(
    const std::vector<pi16u>& renderImageData,
    pi64s renderImageDataVersion,
    piint width,
    piint height,
    piint stride,
    std::vector<pibyte>* renderedImage )
{
    // - resize if necessary
    std::size_t size = stride * height;
    if( renderedImage->size() != size )
        renderedImage->resize( size );

    // - update surface pixels
    pibyte* start = &(*renderedImage)[0];
    if( !renderImageDataVersion )
    {
        // - indicate no image present
        const RgbColor noImageDataColor = { 0xE0, 0x00, 0x00, 0 };
        for( piint y = 0; y < height; ++y )
        {
            RgbColor* pixel = reinterpret_cast<RgbColor*>( start + stride*y );
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
            RgbColor* pixel = reinterpret_cast<RgbColor*>( start + stride*y );
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
                RgbColor gray = { intensity, intensity, intensity, 0 };
                *pixel++ = gray;
            }
        }
    }

    // - publish the new surface data and post a request to redraw
    AutoLock al( lock_ );
    renderedImage_ = renderedImage;
    renderedImageVersion_ = renderImageDataVersion;
    al.Release();
    Action::Post( RequestRedraw );
}

////////////////////////////////////////////////////////////////////////////////
// RenderThread
// - generates image surface data based on image data and redraws the window
// - takes the lock
////////////////////////////////////////////////////////////////////////////////
gpointer RenderThread( gpointer /*data*/ )
{
    std::vector<pi16u> renderImageData;
    pi64s renderImageDataVersion = 0;
    piint renderImageDataWidth;
    piint renderImageDataHeight;
    piint surfaceDataStride;
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
                g_cond_wait( imageDataAvailable_, lock_ );
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
        surfaceDataStride      = surfaceDataStride_;

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
            surfaceDataStride,
            renderedImage );
    }

    return 0;
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
        DisplayError( "Failed to get online readout rate.", error );

    // - get the current readout stride
    piint readoutStride;
    error =
        Picam_GetParameterIntegerValue(
            device_,
            PicamParameter_ReadoutStride,
            &readoutStride );
    if( error != PicamError_None )
        DisplayError( "Failed to get readout stride.", error );

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
        al.Release();
        DisplayError( "Failed to get readout stride.", error );
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
        al.Release();
        DisplayError( "Failed to get frame stride.", error );
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
        al.Release();
        DisplayError( "Failed to get frames per readout.", error );
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
        DisplayError( "Failed to get parameter value type.", error );
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
            std::stringstream oss;
            oss << "Unexpected value type. "
                << "(" << valueType << ")";
            DisplayError( oss.str() );
            return false;
        }
    }

    if( error != PicamError_None )
    {
        DisplayError( "Failed to register for value changes.", error );
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
        DisplayError( "Failed to get parameter constraint type.", error );
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
            std::stringstream oss;
            oss << "Unexpected constraint type. "
                << "(" << constraintType << ")";
            DisplayError( oss.str() );
            return false;
        }
    }

    if( error != PicamError_None )
    {
        DisplayError(
            "Failed to register for constraint changes.",
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
        DisplayError( "Failed to get camera model.", error );
        return;
    }

    // - register with each parameter
    const PicamParameter* parameters;
    piint count;
    error = Picam_GetParameters( model, &parameters, &count );
    if( error != PicamError_None )
    {
        DisplayError( "Failed to get camera model.", error );
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
            DisplayError( "Failed to register for relevance changes.", error );
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
            DisplayError( "Failed to register for access changes.", error );
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
            "Failed to register for online readout rate changed.",
            error );

    // - register readout stride changed
    error =
        PicamAdvanced_RegisterForIntegerValueChanged(
            device_,
            PicamParameter_ReadoutStride,
            ReadoutStrideChanged );
    if( error != PicamError_None )
        DisplayError(
            "Failed to register for readout stride changed.",
            error );

    // - register parameter changed
    RegisterParameterCallbacks();

    // - register acquisition updated
    error =
        PicamAdvanced_RegisterForAcquisitionUpdated(
            device_,
            AcquisitionUpdated );
    if( error != PicamError_None )
        DisplayError( "Failed to register for acquisition updated.", error );
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
            DisplayError( "Failed to close camera.", error );
    }

    // - open the newly selected camera
    error = PicamAdvanced_OpenCameraDevice( &id, &device_ );
    if( error != PicamError_None )
        DisplayError( "Failed to open camera.", error );

    // - initialize with the open camera
    if( device_ )
    {
        RegisterCameraCallbacks();
        InitializeCalculatedBufferSize();
        InitializeImage();

        // - refresh the modeless dialogs (if open)
        if( exposure_ )
            RefreshExposureDialog();
        if( repetitiveGate_ )
            RefreshRepetitiveGateDialog();
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
        DisplayError( "Cannot set readout count.", error );
        return false;
    }

    return true;
}

////////////////////////////////////////////////////////////////////////////////
// Start
// - starts acquisition with the selected camera
// - takes the lock
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
            "Cannot determine if parameters need to be committed.",
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
            DisplayError( "Cannot get the camera model.", error );
            return;
        }

        error = PicamAdvanced_CommitParametersToCameraDevice( model );
        if( error != PicamError_None )
        {
            DisplayError(
                "Failed to commit the camera model parameters.",
                error );
            return;
        }
    }

    // - reallocate circular buffer if necessary
    if( calculatedBufferSize_ == 0 )
    {
        DisplayError( "Cannot start with a circular buffer of no length." );
        return;
    }
    if( static_cast<pi64s>( buffer_.size() ) != calculatedBufferSize_ )
        buffer_.resize( calculatedBufferSize_ );

    // - get current circular buffer
    PicamAcquisitionBuffer buffer;
    error = PicamAdvanced_GetAcquisitionBuffer( device_, &buffer );
    if( error != PicamError_None )
    {
        DisplayError( "Failed to get circular buffer.", error );
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
            DisplayError( "Failed to set circular buffer.", error );
            return;
        }
    }

    // - cache information used to extract frames during acquisition
    if( !CacheFrameNavigation() )
        return;

    // - initialize image data and display
    if( !InitializeImage() )
        return;

    // - mark acquisition active just before acquisition begins
    AutoLock al( lock_ );
    acquisitionActive_ = true;
    g_cond_signal( acquisitionStatusChanged_ );
    al.Release();

    // - start
    error = Picam_StartAcquisition( device_ );
    if( error != PicamError_None )
    {
        DisplayError( "Failed to start acquisition.", error );
        return;
    }

    // - indicate acquisition has begun
    gdk_window_set_cursor(
        gtk_widget_get_window( GTK_WIDGET(main_) ),
        acquiringCursor_ );
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
        DisplayError( "Failed to determine if acquiring.", error );
        return;
    }

    // - set the exposure time appropriately
    PicamHandle model;
    error = PicamAdvanced_GetCameraModel( device_, &model );
    if( error != PicamError_None )
    {
        DisplayError( "Failed to get camera model.", error );
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
            DisplayError( "Failed to set exposure time online.", error );
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
            DisplayError( "Failed to set exposure time.", error );
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
        DisplayError( "Failed to determine if acquiring.", error );
        return;
    }

    // - set the repetitive appropriately
    PicamHandle model;
    error = PicamAdvanced_GetCameraModel( device_, &model );
    if( error != PicamError_None )
    {
        DisplayError( "Failed to get camera model.", error );
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
            DisplayError( "Failed to set repetitive gate online.", error );
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
            DisplayError( "Failed to set repetitive gate.", error );
            return;
        }
    }
}

////////////////////////////////////////////////////////////////////////////////
// GetParameterValue
// - gets the selected camera model's parameter value as two strings
////////////////////////////////////////////////////////////////////////////////
pibool GetParameterValue(
    PicamParameter parameter,
    std::string& text,
    std::string& formatted )
{
    // - clear strings in case of errors
    text.clear();
    formatted.clear();

    // - get the camera model
    PicamHandle model;
    PicamError error = PicamAdvanced_GetCameraModel( device_, &model );
    if( error != PicamError_None )
    {
        DisplayError( "Failed to get camera model.", error );
        return false;
    }

    // - get the value type
    PicamValueType valueType;
    error = Picam_GetParameterValueType( model, parameter, &valueType );
    if( error != PicamError_None )
    {
        DisplayError( "Failed to get parameter value type.", error );
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
                DisplayError( "Failed to get parameter value.", error );
                return false;
            }
            std::ostringstream oss;
            oss << value;
            formatted = text = oss.str();
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
                DisplayError( "Failed to get parameter value.", error );
                return false;
            }
            std::ostringstream oss;
            oss << value;
            text = oss.str();
            formatted = value ? "true" : "false";
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
                DisplayError( "Failed to get parameter value.", error );
                return false;
            }
            std::ostringstream oss;
            oss << value;
            text = oss.str();
            PicamEnumeratedType enumType;
            error =
                Picam_GetParameterEnumeratedType(
                    model,
                    parameter,
                    &enumType );
            if( error != PicamError_None )
            {
                DisplayError( "Failed to get enumerated type.", error );
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
                DisplayError( "Failed to get parameter value.", error );
                return false;
            }
            std::ostringstream oss;
            oss << value;
            formatted = text = oss.str();
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
                DisplayError( "Failed to get parameter value.", error );
                return false;
            }
            std::ostringstream oss;
            oss << value;
            formatted = text = oss.str();
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
                DisplayError( "Failed to get parameter value.", error );
                return false;
            }
            std::ostringstream oss1;
            oss1 << value->roi_array[0].x
                 << ","
                 << value->roi_array[0].y
                 << " "
                 << value->roi_array[0].width
                 << ","
                 << value->roi_array[0].height
                 << " "
                 << value->roi_array[0].x_binning
                 << ","
                 << value->roi_array[0].y_binning;
            text = oss1.str();
            std::ostringstream oss2;
            oss2 << "("
                 << value->roi_array[0].x
                 << ", "
                 << value->roi_array[0].y
                 << ") - "
                 << value->roi_array[0].width
                 << " x "
                 << value->roi_array[0].height
                 << " - "
                 << value->roi_array[0].x_binning
                 << " x "
                 << value->roi_array[0].y_binning
                 << " bin";
            formatted = oss2.str();
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
                DisplayError( "Failed to get parameter value.", error );
                return false;
            }
            std::ostringstream oss1;
            oss1 << value->delay
                 << ","
                 << value->width;
            text = oss1.str();
            std::ostringstream oss2;
            oss2 << "delayed to "
                 << value->delay
                 << " of width "
                 << value->width;
            formatted = oss2.str();
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
                DisplayError( "Failed to get parameter value.", error );
                return false;
            }
            std::ostringstream oss1;
            for( piint m = 0; m < value->modulation_count; ++m )
            {
                oss1 << value->modulation_array[m].duration
                     << ","
                     << value->modulation_array[m].frequency
                     << ","
                     << value->modulation_array[m].phase
                     << ","
                     << value->modulation_array[m].output_signal_frequency;
                if( m != value->modulation_count-1 )
                    oss1 << " ";
            }
            text = oss1.str();
            std::ostringstream oss2;
            oss2 << "cos("
                 << value->modulation_array[0].frequency
                 << "t + "
                 << value->modulation_array[0].phase
                 << "pi/180) lasting "
                 << value->modulation_array[0].duration
                 << " with output signal cos("
                 << value->modulation_array[0].output_signal_frequency
                 << "t)";
            if( value->modulation_count > 1 )
                oss2 << "...";
            formatted = oss2.str();
            Picam_DestroyModulations( value );
            break;
        }
        default:
            formatted = text = "'unknown value'";
            break;
    }

    return true;
}

////////////////////////////////////////////////////////////////////////////////
// SetParameterValue
// - sets the selected camera model's parameter value via string
////////////////////////////////////////////////////////////////////////////////
pibool SetParameterValue( PicamParameter parameter, const std::string& text )
{
    // - get the camera model
    PicamHandle model;
    PicamError error = PicamAdvanced_GetCameraModel( device_, &model );
    if( error != PicamError_None )
    {
        DisplayError( "Failed to get camera model.", error );
        return false;
    }

    // - get the value type
    PicamValueType valueType;
    error = Picam_GetParameterValueType( model, parameter, &valueType );
    if( error != PicamError_None )
    {
        DisplayError( "Failed to get parameter value type.", error );
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
            std::istringstream iss( text );
            iss >> value >> std::ws;
            if( iss.fail() || !iss.eof() )
            {
                DisplayError( "Invalid format." );
                return false;
            }

            // - set the value
            error = Picam_SetParameterIntegerValue( model, parameter, value );
            if( error != PicamError_None )
            {
                DisplayError( "Failed to set parameter value.", error );
                return false;
            }
            break;
        }
        case PicamValueType_LargeInteger:
        {
            // - parse the text
            pi64s value;
            std::istringstream iss( text );
            iss >> value >> std::ws;
            if( iss.fail() || !iss.eof() )
            {
                DisplayError( "Invalid format." );
                return false;
            }

            // - set the value
            error =
                Picam_SetParameterLargeIntegerValue( model, parameter, value );
            if( error != PicamError_None )
            {
                DisplayError( "Failed to set parameter value.", error );
                return false;
            }
            break;
        }
        case PicamValueType_FloatingPoint:
        {
            // - parse the text
            piflt value;
            std::istringstream iss( text );
            iss >> value >> std::ws;
            if( iss.fail() || !iss.eof() )
            {
                DisplayError( "Invalid format." );
                return false;
            }

            // - set the value
            error =
                Picam_SetParameterFloatingPointValue( model, parameter, value );
            if( error != PicamError_None )
            {
                DisplayError( "Failed to set parameter value.", error );
                return false;
            }
            break;
        }
        case PicamValueType_Rois:
        {
            // - parse the text
            PicamRoi roi;
            pichar comma1, comma2, comma3;
            std::istringstream iss( text );
            iss >> roi.x         >> comma1 >> roi.y
                >> roi.width     >> comma2 >> roi.height 
                >> roi.x_binning >> comma3 >> roi.y_binning
                >> std::ws;
            if( iss.fail() || !iss.eof() ||
                comma1 != ',' || comma2 != ',' || comma3 != ',' )
            {
                DisplayError( "Invalid format." );
                return false;
            }

            // - set the value
            PicamRois value = { &roi, 1 };
            error = Picam_SetParameterRoisValue( model, parameter, &value );
            if( error != PicamError_None )
            {
                DisplayError( "Failed to set parameter value.", error );
                return false;
            }
            break;
        }
        case PicamValueType_Pulse:
        {
            // - parse the text
            PicamPulse value;
            pichar comma;
            std::istringstream iss( text );
            iss >> value.delay >> comma >> value.width >> std::ws;
            if( iss.fail() || !iss.eof() || comma != ',' )
            {
                DisplayError( "Invalid format." );
                return false;
            }

            // - set the value
            error = Picam_SetParameterPulseValue( model, parameter, &value );
            if( error != PicamError_None )
            {
                DisplayError( "Failed to set parameter value.", error );
                return false;
            }
            break;
        }
        case PicamValueType_Modulations:
        {
            // - parse the text
            std::vector<PicamModulation> modulations;
            std::istringstream iss( text );
            do
            {
                PicamModulation modulation;
                pichar comma1, comma2, comma3;
                iss >> modulation.duration  >> comma1
                    >> modulation.frequency >> comma2
                    >> modulation.phase     >> comma3
                    >> modulation.output_signal_frequency
                    >> std::ws;
                if( iss.fail() ||
                    comma1 != ',' || comma2 != ',' || comma3 != ',' )
                {
                    DisplayError( "Invalid format." );
                    return false;
                }
                modulations.push_back( modulation );
            }
            while( !iss.eof() );

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
                DisplayError( "Failed to set parameter value.", error );
                return false;
            }
            break;
        }
        default:
        {
            std::ostringstream oss;
            oss << "Failed to parse parameter type. "
                << "(" << valueType << ")";
            DisplayError( oss.str() );
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
    PicamHandle /*device*/,
    PicamDiscoveryAction action )
{
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
                Action::Post( RefreshCamerasDialog );
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
                Action::Post( RefreshCamerasDialog );
            break;
        }
        default:
        {
            std::ostringstream oss;
            oss << "Received unexpected discovery action. "
                 << "(" << static_cast<piint>( action ) << ")";
            PostError( oss.str() );
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
    PicamParameter /*parameter*/,
    piflt value )
{
    piint readoutStride;
    PicamError error =
        Picam_GetParameterIntegerValue(
            camera,
            PicamParameter_ReadoutStride,
            &readoutStride );
    if( error != PicamError_None )
    {
        DisplayError( "Failed to get readout stride.", error );
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
    PicamParameter /*parameter*/,
    piint value )
{
    piflt onlineReadoutRate;
    PicamError error =
        Picam_GetParameterFloatingPointValue(
            camera,
            PicamParameter_OnlineReadoutRateCalculation,
            &onlineReadoutRate );
    if( error != PicamError_None )
    {
        DisplayError( "Failed to get online readout rate.", error );
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
        DisplayError( "Failed to get parameter value type.", error );
        return PicamError_None;
    }

    // - generate log message
    std::string message =
        GetEnumString( PicamEnumeratedType_Parameter, parameter ) +
        " value changed to ";
    switch( valueType )
    {
        case PicamValueType_Integer:
        {
            std::ostringstream oss;
            oss << value;
            message += oss.str();
            break;
        }
        case PicamValueType_Boolean:
            message += value ? "true" : "false";
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
                DisplayError( "Failed to get enumerated type.", error );
                return PicamError_None;
            }
            message += GetEnumString( enumType, value );
            break;
        }
        default:
        {
            std::ostringstream oss;
            oss << value << " (unknown value type " << valueType << ")";
            message += oss.str();
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
    PicamHandle /*camera*/,
    PicamParameter parameter,
    pi64s value )
{
    // - do nothing if parameters dialog is not open
    if( !parameters_ )
        return PicamError_None;

    // - generate log message
    std::string message =
        GetEnumString( PicamEnumeratedType_Parameter, parameter ) +
        " value changed to ";
    std::ostringstream oss;
    oss << value;
    message += oss.str();

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
    PicamHandle /*camera*/,
    PicamParameter parameter,
    piflt value )
{
    // - do nothing if parameters dialog is not open
    if( !parameters_ )
        return PicamError_None;

    // - generate log message
    std::string message =
        GetEnumString( PicamEnumeratedType_Parameter, parameter ) +
        " value changed to ";
    std::ostringstream oss;
    oss << value;
    message += oss.str();

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
    PicamHandle /*camera*/,
    PicamParameter parameter,
    const PicamRois* value )
{
    // - do nothing if parameters dialog is not open
    if( !parameters_ )
        return PicamError_None;

    // - generate log message
    std::string message =
        GetEnumString( PicamEnumeratedType_Parameter, parameter ) +
        " value changed to ";
    std::ostringstream oss;
    oss << "("
        << value->roi_array[0].x
        << ", "
        << value->roi_array[0].y
        << ") - "
        << value->roi_array[0].width
        << " x "
        << value->roi_array[0].height
        << " - "
        << value->roi_array[0].x_binning
        << " x "
        << value->roi_array[0].y_binning
        << " bin";
    message += oss.str();

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
    PicamHandle /*camera*/,
    PicamParameter parameter,
    const PicamPulse* value )
{
    // - do nothing if parameters dialog is not open
    if( !parameters_ )
        return PicamError_None;

    // - generate log message
    std::string message =
        GetEnumString( PicamEnumeratedType_Parameter, parameter ) +
        " value changed to ";
    std::ostringstream oss;
    oss << "delayed to "
        << value->delay
        << " of width "
        << value->width;
    message += oss.str();

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
    PicamHandle /*camera*/,
    PicamParameter parameter,
    const PicamModulations* value )
{
    // - do nothing if parameters dialog is not open
    if( !parameters_ )
        return PicamError_None;

    // - generate log message
    std::string message =
        GetEnumString( PicamEnumeratedType_Parameter, parameter ) +
        " value changed to:\r\n";
    std::ostringstream oss;
    for( piint m = 0; m < value->modulation_count; ++m )
    {
        oss << "\tcos("
            << value->modulation_array[m].frequency
            << "t + "
            << value->modulation_array[m].phase
            << "pi/180) lasting "
            << value->modulation_array[m].duration
            << " with output signal cos("
            << value->modulation_array[m].output_signal_frequency
            << "t)";
        if( m != value->modulation_count-1 )
            oss << "\r\n";
    }
    message += oss.str();

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
    PicamHandle /*camera*/,
    PicamParameter parameter,
    pibln relevant )
{
    // - do nothing if parameters dialog is not open
    if( !parameters_ )
        return PicamError_None;

    // - generate log message
    std::string message =
        GetEnumString( PicamEnumeratedType_Parameter, parameter ) +
        " relevance changed to ";
    message += relevant ? "true" : "false";

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
    PicamHandle /*camera*/,
    PicamParameter parameter,
    PicamValueAccess access )
{
    // - do nothing if parameters dialog is not open
    if( !parameters_ )
        return PicamError_None;

    // - generate log message
    std::string message =
        GetEnumString( PicamEnumeratedType_Parameter, parameter ) +
        " value access changed to ";
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
        DisplayError( "Failed to get parameter value type.", error );
        return PicamError_None;
    }

    // - generate log message
    std::ostringstream oss;
    oss << GetEnumString( PicamEnumeratedType_Parameter, parameter )
        << " collection constraint changed to:\r\n";
    if( !constraint->values_count )
        oss << "\t<empty set>";
    else
    {
        oss << "\t" << constraint->values_count << " Value(s):";
        for( piint i = 0; i < constraint->values_count; ++i )
        {
            oss << "\r\n\t\t";
            switch( valueType )
            {
                case PicamValueType_Integer:
                    oss << static_cast<piint>( constraint->values_array[i] );
                    break;
                case PicamValueType_Boolean:
                    oss << (constraint->values_array[i] ? "true" : "false");
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
                            "Failed to get enumerated type.",
                            error );
                        return PicamError_None;
                    }
                    oss <<
                        GetEnumString(
                            enumType,
                            static_cast<piint>( constraint->values_array[i] ) );
                    break;
                }
                case PicamValueType_LargeInteger:
                    oss << static_cast<pi64s>( constraint->values_array[i] );
                    break;
                case PicamValueType_FloatingPoint:
                    oss << constraint->values_array[i];
                    break;
                default:
                    oss << constraint->values_array[i]
                        << " (unknown value type " << valueType << ")";
                    break;
            }
        }
    }

    LogEvent( oss.str() );

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
        DisplayError( "Failed to get parameter value type.", error );
        return PicamError_None;
    }

    // - generate log message
    std::ostringstream oss;
    oss << GetEnumString( PicamEnumeratedType_Parameter, parameter )
        << " range constraint changed to:\r\n";
    if( constraint->empty_set )
        oss << "\t<empty set>";
    else
    {
        switch( valueType )
        {
            case PicamValueType_Integer:
                oss << "\tMinimum: "
                    << static_cast<piint>( constraint->minimum ) << "\r\n";
                oss << "\tMaximum: "
                    << static_cast<piint>( constraint->maximum ) << "\r\n";
                oss << "\tIncrement: "
                    << static_cast<piint>( constraint->increment );
                if( constraint->outlying_values_count )
                {
                    oss << "\r\n\tIncluding "
                        << constraint->outlying_values_count << " Value(s):";
                    for( piint i = 0;
                         i < constraint->outlying_values_count;
                         ++i )
                    {
                        oss << "\r\n\t\t"
                            << static_cast<piint>(
                                constraint->outlying_values_array[i] );
                    }
                }
                if( constraint->excluded_values_count )
                {
                    oss << "\r\n\tExcluding "
                        << constraint->excluded_values_count << " Value(s):";
                    for( piint i = 0;
                         i < constraint->excluded_values_count;
                         ++i )
                    {
                        oss << "\r\n\t\t"
                            << static_cast<piint>(
                                constraint->excluded_values_array[i] );
                    }
                }
                break;
            case PicamValueType_LargeInteger:
                oss << "\tMinimum: "
                    << static_cast<pi64s>( constraint->minimum ) << "\r\n";
                oss << "\tMaximum: "
                    << static_cast<pi64s>( constraint->maximum ) << "\r\n";
                oss << "\tIncrement: "
                    << static_cast<pi64s>( constraint->increment );
                if( constraint->outlying_values_count )
                {
                    oss << "\r\n\tIncluding "
                        << constraint->outlying_values_count << " Value(s):";
                    for( piint i = 0;
                         i < constraint->outlying_values_count;
                         ++i )
                    {
                        oss << "\r\n\t\t"
                            << static_cast<pi64s>(
                                constraint->outlying_values_array[i] );
                    }
                }
                if( constraint->excluded_values_count )
                {
                    oss << "\r\n\tExcluding "
                         << constraint->excluded_values_count << " Value(s):";
                    for( piint i = 0;
                         i < constraint->excluded_values_count;
                         ++i )
                    {
                        oss << "\r\n\t\t"
                            << static_cast<pi64s>(
                                constraint->excluded_values_array[i] );
                    }
                }
                break;
            case PicamValueType_FloatingPoint:
                oss << "\tMinimum: " << constraint->minimum << "\r\n";
                oss << "\tMaximum: " << constraint->maximum << "\r\n";
                oss << "\tIncrement: " << constraint->increment;
                if( constraint->outlying_values_count )
                {
                    oss << "\r\n\tIncluding "
                        << constraint->outlying_values_count << " Value(s):";
                    for( piint i = 0;
                         i < constraint->outlying_values_count;
                         ++i )
                    {
                        oss << "\r\n\t\t"
                            << constraint->outlying_values_array[i];
                    }
                }
                if( constraint->excluded_values_count )
                {
                    oss << "\r\n\tExcluding "
                        << constraint->excluded_values_count << " Value(s):";
                    for( piint i = 0;
                         i < constraint->excluded_values_count;
                         ++i )
                    {
                        oss << "\r\n\t\t"
                            << constraint->excluded_values_array[i];
                    }
                }
                break;
            default:
                oss << "\tMinimum: "
                    << constraint->minimum 
                    << " (unknown value type " << valueType << ")\r\n";
                oss << "\tMaximum: "
                    << constraint->maximum
                    << " (unknown value type " << valueType << ")\r\n";
                oss << "\tIncrement: "
                    << constraint->increment
                    << " (unknown value type " << valueType << ")";
                if( constraint->outlying_values_count )
                {
                    oss << "\r\n\tIncluding "
                        << constraint->outlying_values_count << " Value(s):";
                    for( piint i = 0;
                         i < constraint->outlying_values_count;
                         ++i )
                    {
                        oss << "\r\n\t\t"
                            << constraint->outlying_values_array[i]
                            << " (unknown value type " << valueType << ")";
                    }
                }
                if( constraint->excluded_values_count )
                {
                    oss << "\r\n\tExcluding "
                        << constraint->excluded_values_count << " Value(s):";
                    for( piint i = 0;
                         i < constraint->excluded_values_count;
                         ++i )
                    {
                        oss << "\r\n\t\t"
                            << constraint->excluded_values_array[i]
                            << " (unknown value type " << valueType << ")";
                    }
                }
                break;
        }
    }

    LogEvent( oss.str() );

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
    PicamHandle /*camera*/,
    PicamParameter parameter,
    const PicamRoisConstraint* constraint )
{
    // - do nothing if parameters dialog is not open
    if( !parameters_ )
        return PicamError_None;

    // - generate log message
    std::ostringstream oss;
    oss << GetEnumString( PicamEnumeratedType_Parameter, parameter )
        << " rois constraint changed to:\r\n";
    if( constraint->empty_set )
        oss << "\t<empty set>";
    else
    {
        // - generate maximum count message
        oss << "\tMaximum Count: "
             << constraint->maximum_roi_count << "\r\n";

        // - generate rois rules message
        oss << "\tRules: "
            << GetEnumString(
                    PicamEnumeratedType_RoisConstraintRulesMask,
                    constraint->rules )
            << "\r\n";

        // - generate x constraint message
        oss << "\tX Constraint:\r\n";
        oss << "\t\tMinimum: "
            << static_cast<piint>( constraint->x_constraint.minimum )
            << "\r\n";
        oss << "\t\tMaximum: "
            << static_cast<piint>( constraint->x_constraint.maximum )
            << "\r\n";
        oss << "\t\tIncrement: "
            << static_cast<piint>( constraint->x_constraint.increment );
        if( constraint->x_constraint.outlying_values_count )
        {
            oss << "\r\n\t\tIncluding "
                << constraint->x_constraint.outlying_values_count
                << " Value(s):";
            for( piint i = 0;
                 i < constraint->x_constraint.outlying_values_count;
                 ++i )
            {
                oss << "\r\n\t\t\t"
                    << static_cast<piint>(
                        constraint->x_constraint.outlying_values_array[i] );
            }
        }
        if( constraint->x_constraint.excluded_values_count )
        {
            oss << "\r\n\t\tExcluding "
                << constraint->x_constraint.excluded_values_count
                << " Value(s):";
            for( piint i = 0;
                 i < constraint->x_constraint.excluded_values_count;
                 ++i )
            {
                oss << "\r\n\t\t\t"
                    << static_cast<piint>(
                        constraint->x_constraint.excluded_values_array[i] );
            }
        }

        // - generate y constraint message
        oss << "\r\n\tY Constraint:\r\n";
        oss << "\t\tMinimum: "
            << static_cast<piint>( constraint->y_constraint.minimum )
            << "\r\n";
        oss << "\t\tMaximum: "
            << static_cast<piint>( constraint->y_constraint.maximum )
            << "\r\n";
        oss << "\t\tIncrement: "
            << static_cast<piint>( constraint->y_constraint.increment );
        if( constraint->y_constraint.outlying_values_count )
        {
            oss << "\r\n\t\tIncluding "
                << constraint->y_constraint.outlying_values_count
                << " Value(s):";
            for( piint i = 0;
                 i < constraint->y_constraint.outlying_values_count;
                 ++i )
            {
                oss << "\r\n\t\t\t"
                    << static_cast<piint>(
                        constraint->y_constraint.outlying_values_array[i] );
            }
        }
        if( constraint->y_constraint.excluded_values_count )
        {
            oss << "\r\n\t\tExcluding "
                << constraint->y_constraint.excluded_values_count
                << " Value(s):";
            for( piint i = 0;
                 i < constraint->y_constraint.excluded_values_count;
                 ++i )
            {
                oss << "\r\n\t\t\t"
                    << static_cast<piint>(
                        constraint->y_constraint.excluded_values_array[i] );
            }
        }

        // - generate width constraint message
        oss << "\r\n\tWidth Constraint:\r\n";
        oss << "\t\tMinimum: "
            << static_cast<piint>( constraint->width_constraint.minimum )
            << "\r\n";
        oss << "\t\tMaximum: "
            << static_cast<piint>( constraint->width_constraint.maximum )
            << "\r\n";
        oss << "\t\tIncrement: "
            << static_cast<piint>( constraint->width_constraint.increment );
        if( constraint->width_constraint.outlying_values_count )
        {
            oss << "\r\n\t\tIncluding "
                << constraint->width_constraint.outlying_values_count
                << " Value(s):";
            for( piint i = 0;
                 i < constraint->width_constraint.outlying_values_count;
                 ++i )
            {
                oss << "\r\n\t\t\t"
                    << static_cast<piint>(
                        constraint->width_constraint.outlying_values_array[i] );
            }
        }
        if( constraint->width_constraint.excluded_values_count )
        {
            oss << "\r\n\t\tExcluding "
                << constraint->width_constraint.excluded_values_count
                << " Value(s):";
            for( piint i = 0;
                 i < constraint->width_constraint.excluded_values_count;
                 ++i )
            {
                oss << "\r\n\t\t\t"
                    << static_cast<piint>(
                        constraint->width_constraint.excluded_values_array[i] );
            }
        }

        // - generate height constraint message
        oss << "\r\n\tHeight Constraint:\r\n";
        oss << "\t\tMinimum: "
            << static_cast<piint>( constraint->height_constraint.minimum )
            << "\r\n";
        oss << "\t\tMaximum: "
            << static_cast<piint>( constraint->height_constraint.maximum )
            << "\r\n";
        oss << "\t\tIncrement: "
            << static_cast<piint>( constraint->height_constraint.increment );
        if( constraint->height_constraint.outlying_values_count )
        {
            oss << "\r\n\t\tIncluding "
                << constraint->height_constraint.outlying_values_count
                << " Value(s):";
            for( piint i = 0;
                 i < constraint->height_constraint.outlying_values_count;
                 ++i )
            {
                oss << "\r\n\t\t\t"
                    << static_cast<piint>(
                        constraint->height_constraint.outlying_values_array[i] );
            }
        }
        if( constraint->height_constraint.excluded_values_count )
        {
            oss << "\r\n\t\tExcluding "
                << constraint->height_constraint.excluded_values_count
                << " Value(s):";
            for( piint i = 0;
                 i < constraint->height_constraint.excluded_values_count;
                 ++i )
            {
                oss << "\r\n\t\t\t"
                    << static_cast<piint>(
                        constraint->height_constraint.excluded_values_array[i] );
            }
        }

        // - generate x-binning constraint message
        if( constraint->x_binning_limits_count )
        {
            oss << "\r\n\tX-Binning Limitted to "
                << constraint->x_binning_limits_count << " Value(s):";
            for( piint i = 0; i < constraint->x_binning_limits_count; ++i )
                oss << "\r\n\t\t" << constraint->x_binning_limits_array[i];
        }

        // - generate y-binning constraint message
        if( constraint->y_binning_limits_count )
        {
            oss << "\r\n\tY-Binning Limitted to "
                << constraint->y_binning_limits_count << " Value(s):";
            for( piint i = 0; i < constraint->y_binning_limits_count; ++i )
                oss << "\r\n\t\t" << constraint->y_binning_limits_array[i];
        }
    }

    LogEvent( oss.str() );

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
    PicamHandle /*camera*/,
    PicamParameter parameter,
    const PicamPulseConstraint* constraint )
{
    // - do nothing if parameters dialog is not open
    if( !parameters_ )
        return PicamError_None;

    // - generate log message
    std::ostringstream oss;
    oss << GetEnumString( PicamEnumeratedType_Parameter, parameter )
        << " pulse constraint changed to:\r\n";
    if( constraint->empty_set )
        oss << "\t<empty set>";
    else
    {
        // - generate minimum duration message
        oss << "\tMinimum Duration: "
            << constraint->minimum_duration << "\r\n";

        // - generate maximum duration message
        oss << "\tMaximum Duration: "
            << constraint->maximum_duration << "\r\n";

        // - generate delay constraint message
        oss << "\tDelay Constraint:\r\n";
        oss << "\t\tMinimum: "
            << constraint->delay_constraint.minimum
            << "\r\n";
        oss << "\t\tMaximum: "
            << constraint->delay_constraint.maximum
            << "\r\n";
        oss << "\t\tIncrement: "
            << constraint->delay_constraint.increment;
        if( constraint->delay_constraint.outlying_values_count )
        {
            oss << "\r\n\t\tIncluding "
                << constraint->delay_constraint.outlying_values_count
                << " Value(s):";
            for( piint i = 0;
                 i < constraint->delay_constraint.outlying_values_count;
                 ++i )
            {
                oss << "\r\n\t\t\t"
                    << constraint->delay_constraint.outlying_values_array[i];
            }
        }
        if( constraint->delay_constraint.excluded_values_count )
        {
            oss << "\r\n\t\tExcluding "
                << constraint->delay_constraint.excluded_values_count
                << " Value(s):";
            for( piint i = 0;
                 i < constraint->delay_constraint.excluded_values_count;
                 ++i )
            {
                oss << "\r\n\t\t\t"
                    << constraint->delay_constraint.excluded_values_array[i];
            }
        }

        // - generate width constraint message
        oss << "\r\n\tWidth Constraint:\r\n";
        oss << "\t\tMinimum: "
            << constraint->width_constraint.minimum
            << "\r\n";
        oss << "\t\tMaximum: "
            << constraint->width_constraint.maximum
            << "\r\n";
        oss << "\t\tIncrement: "
            << constraint->width_constraint.increment;
        if( constraint->width_constraint.outlying_values_count )
        {
            oss << "\r\n\t\tIncluding "
                << constraint->width_constraint.outlying_values_count
                << " Value(s):";
            for( piint i = 0;
                 i < constraint->width_constraint.outlying_values_count;
                 ++i )
            {
                oss << "\r\n\t\t\t"
                    << constraint->width_constraint.outlying_values_array[i];
            }
        }
        if( constraint->width_constraint.excluded_values_count )
        {
            oss << "\r\n\t\tExcluding "
                << constraint->width_constraint.excluded_values_count
                << " Value(s):";
            for( piint i = 0;
                 i < constraint->width_constraint.excluded_values_count;
                 ++i )
            {
                oss << "\r\n\t\t\t"
                    << constraint->width_constraint.excluded_values_array[i];
            }
        }
    }

    LogEvent( oss.str() );

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
    PicamHandle /*camera*/,
    PicamParameter parameter,
    const PicamModulationsConstraint* constraint )
{
    // - do nothing if parameters dialog is not open
    if( !parameters_ )
        return PicamError_None;

    // - generate log message
    std::ostringstream oss;
    oss << GetEnumString( PicamEnumeratedType_Parameter, parameter )
        << " modulations constraint changed to:\r\n";
    if( constraint->empty_set )
        oss << "\t<empty set>";
    else
    {
        // - generate maximum count message
        oss << "\tMaximum Count: "
            << constraint->maximum_modulation_count << "\r\n";

        // - generate duration constraint message
        oss << "\tDuration Constraint:\r\n";
        oss << "\t\tMinimum: "
            << constraint->duration_constraint.minimum
            << "\r\n";
        oss << "\t\tMaximum: "
            << constraint->duration_constraint.maximum
            << "\r\n";
        oss << "\t\tIncrement: "
            << constraint->duration_constraint.increment;
        if( constraint->duration_constraint.outlying_values_count )
        {
            oss << "\r\n\t\tIncluding "
                << constraint->duration_constraint.outlying_values_count
                << " Value(s):";
            for( piint i = 0;
                 i < constraint->duration_constraint.outlying_values_count;
                 ++i )
            {
                oss << "\r\n\t\t\t"
                    << constraint->
                        duration_constraint.outlying_values_array[i];
            }
        }
        if( constraint->duration_constraint.excluded_values_count )
        {
            oss << "\r\n\t\tExcluding "
                << constraint->duration_constraint.excluded_values_count
                << " Value(s):";
            for( piint i = 0;
                 i < constraint->duration_constraint.excluded_values_count;
                 ++i )
            {
                oss << "\r\n\t\t\t"
                    << constraint->
                        duration_constraint.excluded_values_array[i];
            }
        }

        // - generate frequency constraint message
        oss << "\r\n\tFrequency Constraint:\r\n";
        oss << "\t\tMinimum: "
            << constraint->frequency_constraint.minimum
            << "\r\n";
        oss << "\t\tMaximum: "
            << constraint->frequency_constraint.maximum
            << "\r\n";
        oss << "\t\tIncrement: "
            << constraint->frequency_constraint.increment;
        if( constraint->frequency_constraint.outlying_values_count )
        {
            oss << "\r\n\t\tIncluding "
                << constraint->frequency_constraint.outlying_values_count
                << " Value(s):";
            for( piint i = 0;
                 i < constraint->frequency_constraint.outlying_values_count;
                 ++i )
            {
                oss << "\r\n\t\t\t"
                    << constraint->
                        frequency_constraint.outlying_values_array[i];
            }
        }
        if( constraint->frequency_constraint.excluded_values_count )
        {
            oss << "\r\n\t\tExcluding "
                << constraint->frequency_constraint.excluded_values_count
                << " Value(s):";
            for( piint i = 0;
                 i < constraint->frequency_constraint.excluded_values_count;
                 ++i )
            {
                oss << "\r\n\t\t\t"
                    << constraint->
                        frequency_constraint.excluded_values_array[i];
            }
        }

        // - generate phase constraint message
        oss << "\r\n\tPhase Constraint:\r\n";
        oss << "\t\tMinimum: "
            << constraint->phase_constraint.minimum
            << "\r\n";
        oss << "\t\tMaximum: "
            << constraint->phase_constraint.maximum
            << "\r\n";
        oss << "\t\tIncrement: "
            << constraint->phase_constraint.increment;
        if( constraint->phase_constraint.outlying_values_count )
        {
            oss << "\r\n\t\tIncluding "
                << constraint->phase_constraint.outlying_values_count
                << " Value(s):";
            for( piint i = 0;
                 i < constraint->phase_constraint.outlying_values_count;
                 ++i )
            {
                oss << "\r\n\t\t\t"
                    << constraint->phase_constraint.outlying_values_array[i];
            }
        }
        if( constraint->phase_constraint.excluded_values_count )
        {
            oss << "\r\n\t\tExcluding "
                << constraint->phase_constraint.excluded_values_count
                << " Value(s):";
            for( piint i = 0;
                 i < constraint->phase_constraint.excluded_values_count;
                 ++i )
            {
                oss << "\r\n\t\t\t"
                    << constraint->phase_constraint.excluded_values_array[i];
            }
        }

        // - generate output signal frequency constraint message
        oss << "\r\n\tOutput Signal Frequency Constraint:\r\n";
        oss << "\t\tMinimum: "
            << constraint->output_signal_frequency_constraint.minimum
            << "\r\n";
        oss << "\t\tMaximum: "
            << constraint->output_signal_frequency_constraint.maximum
            << "\r\n";
        oss << "\t\tIncrement: "
            << constraint->output_signal_frequency_constraint.increment;
        if( constraint->
            output_signal_frequency_constraint.outlying_values_count )
        {
            oss << "\r\n\t\tIncluding "
                << constraint->
                    output_signal_frequency_constraint.outlying_values_count
                << " Value(s):";
            for( piint i = 0;
                 i < constraint->
                     output_signal_frequency_constraint.outlying_values_count;
                 ++i )
            {
                oss << "\r\n\t\t\t"
                    << constraint->
                        output_signal_frequency_constraint.
                        outlying_values_array[i];
            }
        }
        if( constraint->output_signal_frequency_constraint.excluded_values_count )
        {
            oss << "\r\n\t\tExcluding "
                << constraint->
                    output_signal_frequency_constraint.excluded_values_count
                << " Value(s):";
            for( piint i = 0;
                 i < constraint->
                     output_signal_frequency_constraint.excluded_values_count;
                 ++i )
            {
                oss << "\r\n\t\t\t"
                    << constraint->
                        output_signal_frequency_constraint.
                        excluded_values_array[i];
            }
        }
    }

    LogEvent( oss.str() );

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
        pi64s lastReadoutOffset = readoutStride_ * (available->readout_count-1);
        pi64s lastFrameOffset = frameStride_ * (framesPerReadout_-1);
        const pibyte* frame =
            static_cast<const pibyte*>( available->initial_readout ) +
            lastReadoutOffset + lastFrameOffset;
        std::memcpy( &imageData_[0], frame, frameSize_ );
        ++imageDataVersion_;
        g_cond_signal( imageDataAvailable_ );
        al.Release();

        // - check for overrun after copying
        pibln overran;
        PicamError error =
            PicamAdvanced_HasAcquisitionBufferOverrun( device, &overran );
        if( error != PicamError_None )
        {
            std::ostringstream oss;
            oss << "Failed check for buffer overrun. "
                << "("
                << GetEnumString( PicamEnumeratedType_Error, error )
                << ")";
            PostError( oss.str() );
        }
        else if( overran )
            PostError( "Buffer overran." );
    }

    // - note when acquisition has completed
    if( !status->running )
    {
        AutoLock al( lock_ );
        acquisitionActive_ = false;
        g_cond_signal( acquisitionStatusChanged_ );
        al.Release();
        Action::Post( IndicateAcquisitionCompleted );
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

    // - initialize state
    lock_ = g_mutex_new();
    acquisitionStatusChanged_ = g_cond_new();
    imageDataAvailable_ = g_cond_new();
    GError* threadError = 0;
    GThread* thread =
        g_thread_create(
            RenderThread,
            0,
            false, /*joinable*/
            &threadError );
    if( !thread )
    {
        DisplayError( threadError->message );
        g_error_free( threadError );
        return false;
    }

    // - initialize picam
    PicamError error = Picam_InitializeLibrary();
    if( error != PicamError_None )
    {
        DisplayError( "Failed to initialize PICam.", error );
        return false;
    }

    // - initialize available camera list
    const PicamCameraID* available;
    piint availableCount;
    error = Picam_GetAvailableCameraIDs( &available, &availableCount );
    if( error != PicamError_None )
    {
        DisplayError( "Failed to get available cameras.", error );
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
        DisplayError( "Failed to get unavailable cameras.", error );
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
        DisplayError( "Failed to register camera discovery.", error );
        return false;
    }
    error = PicamAdvanced_DiscoverCameras();
    if( error != PicamError_None )
    {
        DisplayError( "Failed to start camera discovery.", error );
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
    if( device_ )
    {
        // - handle an acquiring camera
        pibln running;
        PicamError error = Picam_IsAcquisitionRunning( device_, &running );
        if( error == PicamError_None && running )
        {
            error = Picam_StopAcquisition( device_ );
            running =
                error != PicamError_None || !WaitForAcquisitionCompleted();
            if( running )
                DisplayError( "Failed to stop camera.", error );
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
        // - get from the camera selection dialog
        id = SelectFromCamerasDialog();
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
        gtk_window_present(
            GTK_WINDOW(gtk_builder_get_object( exposure_, "dialog" )) );
        return;
    }

    // - create and show the dialog
    InitializeExposureDialog();
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
        gtk_window_present(
            GTK_WINDOW(gtk_builder_get_object( repetitiveGate_, "dialog" )) );
        return;
    }

    // - create and show the dialog
    InitializeRepetitiveGateDialog();
}

////////////////////////////////////////////////////////////////////////////////
// SetParameters
// - prompts the user to change parameter values
////////////////////////////////////////////////////////////////////////////////
void SetParameters()
{
    // - create and show the dialog
    ConfigureFromParametersDialog();
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
        DisplayError( "Failed to stop acquisition.", error );
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
        al.Release();
        DisplayError( "No image data." );
        return;
    }

    // - build the path
    gchar* dir = g_get_current_dir();
    std::string current( dir );
    g_free( dir );
    std::time_t time = std::time( 0 );
    pichar formattedTime[20] = { 0 };
    std::strftime(
        formattedTime,
        sizeof( formattedTime ),
        "%Y_%m_%d-%H_%M_%S",
        std::localtime( &time ) );
    std::ostringstream oss;
    oss << current << "/"
        << "advanced_data-" 
        << formattedTime
        << ".raw";
    std::string path( oss.str() );

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
void UpdateParameterInformation(
    GtkComboBox* /*combo_box*/,
    gpointer /*user_data*/ )
{
    // - get the controls
    GtkComboBox* parametersComboBox =
        GTK_COMBO_BOX(
            gtk_builder_get_object( parameters_, "parameters_combo_box" ));
    GtkLabel* formatLabel =
        GTK_LABEL(gtk_builder_get_object( parameters_, "format_label" ));
    GtkEntry* valueEntry =
        GTK_ENTRY(gtk_builder_get_object( parameters_, "value_entry" ));
    GtkLabel* formattedLabel =
        GTK_LABEL(gtk_builder_get_object( parameters_, "value_label" ));
    GtkLabel* accessLabel =
        GTK_LABEL(gtk_builder_get_object( parameters_, "access_label" ));
    GtkLabel* dynamicsLabel =
        GTK_LABEL(gtk_builder_get_object( parameters_, "dynamics_label" ));

    // - handle no selection
    GtkTreeIter selectedIter;
    gboolean selected =
        gtk_combo_box_get_active_iter( parametersComboBox, &selectedIter );
    if( !selected )
    {
        gtk_label_set_text( formatLabel,    "" );
        gtk_entry_set_text( valueEntry,     "" );
        gtk_label_set_text( formattedLabel, "" );
        gtk_label_set_text( accessLabel,    "" );
        gtk_label_set_text( dynamicsLabel,  "" );
        return;
    }

    // - get the selected parameter
    gint selectedParameter;
    gtk_tree_model_get(
        gtk_combo_box_get_model( parametersComboBox ),
        &selectedIter,
        1,
        &selectedParameter,
        -1 );
    PicamParameter parameter = static_cast<PicamParameter>( selectedParameter );

    // - get the camera model
    PicamHandle model;
    PicamError error = PicamAdvanced_GetCameraModel( device_, &model );
    if( error != PicamError_None )
    {
        DisplayError( "Failed to get camera model.", error );
        return;
    }

    std::string text;

    // - show the format
    PicamValueType valueType;
    error = Picam_GetParameterValueType( model, parameter, &valueType );
    if( error != PicamError_None )
    {
        DisplayError( "Failed to get parameter value type.", error );
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
            text += " (false = 0, true = non-0)";
            break;
        case PicamValueType_Enumeration:
            text += " (as integer value)";
            break;
        case PicamValueType_Rois:
            text += " (as 'x,y w,h xb,yb')";
            break;
        case PicamValueType_Pulse:
            text += " (as 'd,w')";
            break;
        case PicamValueType_Modulations:
            text += " (as 'd,f,p,osf d,f,p,osf...')";
            break;
    }
    gtk_label_set_text( formatLabel, text.c_str() );

    // - show the value
    std::string formatted;
    if( !GetParameterValue( parameter, text, formatted ) )
        return;
    gtk_entry_set_text( valueEntry, text.c_str() );
    gtk_label_set_text( formattedLabel, formatted.c_str() );

    // - show the access
    PicamValueAccess access;
    error = Picam_GetParameterValueAccess( model, parameter, &access );
    if( error != PicamError_None )
    {
        DisplayError( "Failed to get parameter value access.", error );
        return;
    }
    text = GetEnumString( PicamEnumeratedType_ValueAccess, access );
    gtk_label_set_text( accessLabel, text.c_str() );

    // - show the dynamics
    PicamDynamicsMask dynamics;
    error = PicamAdvanced_GetParameterDynamics( model, parameter, &dynamics );
    if( error != PicamError_None )
    {
        DisplayError( "Failed to get parameter dynamics.", error );
        return;
    }
    text = GetEnumString( PicamEnumeratedType_DynamicsMask, dynamics );
    gtk_label_set_text( dynamicsLabel, text.c_str() );
}

////////////////////////////////////////////////////////////////////////////////
// ConfigureFromParametersDialog
// - initializes and shows the parameters dialog
////////////////////////////////////////////////////////////////////////////////
void ConfigureFromParametersDialog()
{
    // - create the dialog
    parameters_ =
        LoadDialog(
            _binary_advanced_parameters_dialog_ui_start,
            _binary_advanced_parameters_dialog_ui_end );
    if( !parameters_ )
        return;

    // - get the camera model
    PicamHandle model;
    PicamError error = PicamAdvanced_GetCameraModel( device_, &model );
    if( error != PicamError_None )
    {
        DisplayError( "Failed to get camera model.", error );
        g_object_unref( G_OBJECT(parameters_) );
        parameters_ = 0;
        return;
    }

    // - initialize the parameter combo box
    const PicamParameter* parameters;
    piint count;
    error = Picam_GetParameters( model, &parameters, &count );
    if( error != PicamError_None )
    {
        DisplayError( "Failed to get camera parameters.", error );
        g_object_unref( G_OBJECT(parameters_) );
        parameters_ = 0;
        return;
    }
    GtkListStore* parameterModel =
        GTK_LIST_STORE(
            gtk_builder_get_object( parameters_, "parameters_model" ));
    for( piint i = 0; i < count; ++i )
    {
        // - create a string version of the parameter
        std::string item =
            GetEnumString( PicamEnumeratedType_Parameter, parameters[i] );

        // - add the string and parameter to the list
        GtkTreeIter iter;
        gtk_list_store_append( parameterModel, &iter );
        gtk_list_store_set(
            parameterModel,
            &iter,
            0,
            item.c_str(),
            1,
            parameters[i],
            -1 );
    }
    Picam_DestroyParameters( parameters );
    GtkTreeModel* sortedParameters =
        gtk_tree_model_sort_new_with_model( GTK_TREE_MODEL(parameterModel) );
    gtk_tree_sortable_set_sort_column_id(
        GTK_TREE_SORTABLE(sortedParameters),
        0,
        GTK_SORT_ASCENDING );
    GtkComboBox* parametersComboBox =
        GTK_COMBO_BOX(
            gtk_builder_get_object( parameters_, "parameters_combo_box" ));
    gtk_combo_box_set_model( parametersComboBox, sortedParameters );

    // - populate parameter controls
    UpdateParameterInformation();

    // - connect all signal handlers
    g_signal_connect(
        parametersComboBox,
        "changed",
        G_CALLBACK(UpdateParameterInformation),
        0 );
    g_signal_connect(
        GTK_BUTTON(gtk_builder_get_object( parameters_, "submit_button" )),
        "clicked",
        G_CALLBACK(ApplyValueText),
        0 );
    g_signal_connect(
        GTK_BUTTON(gtk_builder_get_object( parameters_, "cancel_button" )),
        "clicked",
        G_CALLBACK(CancelParametersDialog),
        0 );
    g_signal_connect(
        GTK_BUTTON(gtk_builder_get_object( parameters_, "ok_button" )),
        "clicked",
        G_CALLBACK(ApplyParametersDialog),
        0 );
    g_signal_connect(
        GTK_BUTTON(gtk_builder_get_object( parameters_, "refresh_button" )),
        "clicked",
        G_CALLBACK(RefreshParameters),
        0 );
    g_signal_connect(
        GTK_BUTTON(gtk_builder_get_object( parameters_, "commit_button" )),
        "clicked",
        G_CALLBACK(CommitParameters),
        0 );
    g_signal_connect(
        GTK_BUTTON(gtk_builder_get_object( parameters_, "validate_button" )),
        "clicked",
        G_CALLBACK(ValidateParameters),
        0 );
    g_signal_connect(
        GTK_BUTTON(gtk_builder_get_object( parameters_, "clear_button" )),
        "clicked",
        G_CALLBACK(ClearEventLog),
        0 );

    // - show the modal dialog
    GtkDialog* dialog =
        GTK_DIALOG(gtk_builder_get_object( parameters_, "dialog" ));
    ShowModalDialog( dialog );

    // - clean up
    gtk_widget_destroy( GTK_WIDGET(dialog) );
    g_object_unref( G_OBJECT(parameters_) );
    parameters_ = 0;
}

////////////////////////////////////////////////////////////////////////////////
// ApplyValueText
// - sets the parameter value from the entry
////////////////////////////////////////////////////////////////////////////////
void ApplyValueText( GtkButton* /*button*/, gpointer /*user_data*/ )
{
    // - handle no selection
    GtkComboBox* parametersComboBox =
        GTK_COMBO_BOX(
            gtk_builder_get_object( parameters_, "parameters_combo_box" ));
    GtkTreeIter selectedIter;
    gboolean selected =
        gtk_combo_box_get_active_iter( parametersComboBox, &selectedIter );
    if( !selected )
    {
        DisplayError( "No parameter selected." );
        return;
    }

    // - get the selected parameter
    gint selectedParameter;
    gtk_tree_model_get(
        gtk_combo_box_get_model( parametersComboBox ),
        &selectedIter,
        1,
        &selectedParameter,
        -1 );
    PicamParameter parameter = static_cast<PicamParameter>( selectedParameter );

    // - get the text from the entry
    GtkEntry* valueEntry =
        GTK_ENTRY(gtk_builder_get_object( parameters_, "value_entry" ));
    std::string text( gtk_entry_get_text( valueEntry ) );

    // - set the value and update information if successful
    if( SetParameterValue( parameter, text ) )
        UpdateParameterInformation();
}

////////////////////////////////////////////////////////////////////////////////
// LogEvent
// - appends a message to the event log
////////////////////////////////////////////////////////////////////////////////
void LogEvent( const std::string& message )
{
    // - move cursor to the beginning
    GtkTextBuffer* buffer =
        gtk_text_view_get_buffer(
            GTK_TEXT_VIEW(gtk_builder_get_object(
                parameters_,
                "events_text_view" )) );
    GtkTextIter iter;
    gtk_text_buffer_get_start_iter( buffer, &iter );
    gtk_text_buffer_place_cursor( buffer, &iter );

    // - prepend to the log
    std::string line( message + "\r\n" );
    gtk_text_buffer_insert_at_cursor( buffer, line.c_str(), -1 );
}

////////////////////////////////////////////////////////////////////////////////
// ClearEventLog
// - clears the event log
////////////////////////////////////////////////////////////////////////////////
void ClearEventLog( GtkButton* /*button*/, gpointer /*user_data*/ )
{
    // - clear the text buffer
    GtkTextBuffer* buffer =
        gtk_text_view_get_buffer(
            GTK_TEXT_VIEW(gtk_builder_get_object(
                parameters_,
                "events_text_view" )) );
    gtk_text_buffer_set_text( buffer, "", -1 );
}

////////////////////////////////////////////////////////////////////////////////
// ValidateParameters
// - validates camera model parameters and shows results in the parameters
//   dialog
////////////////////////////////////////////////////////////////////////////////
void ValidateParameters( GtkButton* /*button*/, gpointer /*user_data*/ )
{
    // - get the camera model
    PicamHandle model;
    PicamError error = PicamAdvanced_GetCameraModel( device_, &model );
    if( error != PicamError_None )
    {
        DisplayError( "Failed to get camera model.", error );
        return;
    }

    // - validate the model
    const PicamValidationResults* results;
    error = PicamAdvanced_ValidateParameters( model, &results );
    if( error != PicamError_None )
    {
        DisplayError( "Failed to validate to camera model.", error );
        return;
    }

    // - generate log message
    std::string message;
    if( results->is_valid )
        message = "Validation succeeded";
    else
    {
        std::ostringstream oss;
        oss << "Validation failed:";
        for( piint i = 0; i < results->validation_result_count; ++i )
        {
            const PicamValidationResult* result =
                &results->validation_result_array[i];
            if( result->error_constraining_parameter_count )
            {
                oss << "\r\n\t"
                    << GetEnumString(
                            PicamEnumeratedType_Parameter,
                            *result->failed_parameter )
                    << " is in "
                    << GetEnumString(
                            PicamEnumeratedType_ConstraintSeverity,
                            PicamConstraintSeverity_Error )
                    << " due to "
                    << result->error_constraining_parameter_count
                    << " Parameter(s):";
                for( piint j = 0;
                     j < result->error_constraining_parameter_count;
                     ++j )
                {
                    oss << "\r\n\t\t"
                        << GetEnumString(
                                PicamEnumeratedType_Parameter,
                                result->error_constraining_parameter_array[j] );
                }
            }
            if( result->warning_constraining_parameter_count )
            {
                oss << "\r\n\t"
                    << GetEnumString(
                            PicamEnumeratedType_Parameter,
                            *result->failed_parameter )
                    << " is in "
                    << GetEnumString(
                            PicamEnumeratedType_ConstraintSeverity,
                            PicamConstraintSeverity_Warning )
                    << " due to "
                    << result->warning_constraining_parameter_count
                    << " Parameter(s):";
                for( piint j = 0;
                     j < result->warning_constraining_parameter_count;
                     ++j )
                {
                    oss << "\r\n\t\t"
                        << GetEnumString(
                                PicamEnumeratedType_Parameter,
                                result->warning_constraining_parameter_array[j] );
                }
            }
        }
        message = oss.str();
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
        DisplayError( "Failed to get camera model.", error );
        return false;
    }

    // - apply changes to the device
    // - any changes to the model will be handled through change callbacks
    error = PicamAdvanced_CommitParametersToCameraDevice( model );
    if( error != PicamError_None )
    {
        DisplayError( "Failed to commit to camera device.", error );
        return false;
    }

    // - refresh the modeless dialogs if open
    if( exposure_ )
        RefreshExposureDialog();
    if( repetitiveGate_ )
        RefreshRepetitiveGateDialog();

    LogEvent( "Parameters committed" );

    return true;
}

////////////////////////////////////////////////////////////////////////////////
// CommitParameters
// - commits the camera model and shows results in the parameters dialog
////////////////////////////////////////////////////////////////////////////////
void CommitParameters( GtkButton* /*button*/, gpointer /*user_data*/ )
{
    CommitParameters();
}

////////////////////////////////////////////////////////////////////////////////
// RefreshParameters
// - refreshes the camera model and shows results in the parameters dialog
////////////////////////////////////////////////////////////////////////////////
void RefreshParameters( GtkButton* /*button*/, gpointer /*user_data*/ )
{
    // - get the camera model
    PicamHandle model;
    PicamError error = PicamAdvanced_GetCameraModel( device_, &model );
    if( error != PicamError_None )
    {
        DisplayError( "Failed to get camera model.", error );
        return;
    }

    // - revert changes on the model
    // - any changes to the model will be handled through change callbacks
    error = PicamAdvanced_RefreshParametersFromCameraDevice( model );
    if( error != PicamError_None )
    {
        DisplayError( "Failed to refresh camera model.", error );
        return;
    }

    // - reflect any changes
    UpdateParameterInformation();

    LogEvent( "Parameters refreshed" );
}

////////////////////////////////////////////////////////////////////////////////
// ApplyParametersDialog
// - handles acceptance from the parameters dialog
////////////////////////////////////////////////////////////////////////////////
void ApplyParametersDialog( GtkButton* /*button*/, gpointer /*user_data*/ )
{
    if( !CommitParameters() )
        return;

    // - close the dialog (only on success)
    GtkDialog* dialog =
        GTK_DIALOG(gtk_builder_get_object( parameters_, "dialog" ));
    gtk_dialog_response( dialog, GTK_RESPONSE_OK );
}

////////////////////////////////////////////////////////////////////////////////
// CancelParametersDialog
// - handles cancelation from the parameters dialog
////////////////////////////////////////////////////////////////////////////////
void CancelParametersDialog( GtkButton* /*button*/, gpointer /*user_data*/ )
{
    RefreshParameters();

    // - close the dialog (regardless of success)
    GtkDialog* dialog =
        GTK_DIALOG(gtk_builder_get_object( parameters_, "dialog" ));
    gtk_dialog_response( dialog, GTK_RESPONSE_CANCEL );
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
// - initializes and shows the exposure dialog
////////////////////////////////////////////////////////////////////////////////
void InitializeExposureDialog()
{
    // - create the dialog
    exposure_ =
        LoadDialog(
            _binary_advanced_exposure_dialog_ui_start,
            _binary_advanced_exposure_dialog_ui_end );
    if( !exposure_ )
        return;

    // - set scale range from 1-1000 ms
    GtkHScale* scale =
        GTK_HSCALE(gtk_builder_get_object( exposure_, "exposure_hscale" ));
    gtk_range_set_range( GTK_RANGE(scale), 1., 1000. );

    // - set scale step and page increments to 1 and 100 ms
    gtk_range_set_increments( GTK_RANGE(scale), 1., 100. );

    // - reflect current exposure time
    RefreshExposureDialog();

    // - connect all signal handlers
    GtkButton* submit =
        GTK_BUTTON(
            gtk_builder_get_object( exposure_, "submit_exposure_button" ));
    g_signal_connect(
        submit,
        "clicked",
        G_CALLBACK(ApplyExposureTimeText),
        0 );
    g_signal_connect(
        scale,
        "value-changed",
        G_CALLBACK(ApplyExposureTimePosition),
        0 );
    GtkDialog* dialog =
        GTK_DIALOG(gtk_builder_get_object( exposure_, "dialog" ));
    g_signal_connect(
        dialog,
        "response",
        G_CALLBACK(CloseExposureDialog),
        0 );

    // - show the dialog
    gtk_widget_show_all( GTK_WIDGET(dialog) );
}

////////////////////////////////////////////////////////////////////////////////
// RefreshExposureDialog
// - refreshes the exposure information in the exposure dialog
////////////////////////////////////////////////////////////////////////////////
void RefreshExposureDialog()
{
    // - get the current set up exposure time
    PicamHandle model;
    PicamError error = PicamAdvanced_GetCameraModel( device_, &model );
    if( error != PicamError_None )
    {
        DisplayError( "Failed to get camera model.", error );
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
        DisplayError( "Failed to get exposure time.", error );
        return;
    }

    // - set exposure text in entry
    std::ostringstream oss;
    oss << exposure;
    GtkEntry* entry =
        GTK_ENTRY(gtk_builder_get_object( exposure_, "exposure_entry" ));
    gtk_entry_set_text( entry, oss.str().c_str() );

    // - synchronize scale to nearest step based on exposure time
    piint position = static_cast<piint>( exposure + 0.5 );
    GtkHScale* scale =
        GTK_HSCALE(gtk_builder_get_object( exposure_, "exposure_hscale" ));
    synchronizeHScale_ = true;
    gtk_range_set_value( GTK_RANGE(scale), position );
    synchronizeHScale_ = false;
}

////////////////////////////////////////////////////////////////////////////////
// ApplyExposureTimeText
// - sets the exposure time from the entry
////////////////////////////////////////////////////////////////////////////////
void ApplyExposureTimeText( GtkButton* /*button*/, gpointer /*user_data*/ )
{
    // - get the text from the entry
    GtkEntry* entry =
        GTK_ENTRY(gtk_builder_get_object( exposure_, "exposure_entry" ));
    std::string text( gtk_entry_get_text( entry ) );

    // - parse the text
    piflt exposure;
    std::istringstream iss( text );
    iss >> exposure >> std::ws;
    if( iss.fail() || !iss.eof() )
    {
        DisplayError( "Invalid format." );
        return;
    }

    // - synchronize the scale
    piint position = static_cast<piint>( exposure + 0.5 );
    GtkHScale* scale =
        GTK_HSCALE(gtk_builder_get_object( exposure_, "exposure_hscale" ));
    synchronizeHScale_ = true;
    gtk_range_set_value( GTK_RANGE(scale), position );
    synchronizeHScale_ = false;

    // - set exposure in the camera
    ApplyExposureTime( exposure );
}

////////////////////////////////////////////////////////////////////////////////
// ApplyExposureTimePosition
// - sets the exposure time from the scale
////////////////////////////////////////////////////////////////////////////////
void ApplyExposureTimePosition( GtkRange* range, gpointer /*user_data*/ )
{
    // - do nothing if this update was due to synchronizing from the entry
    if( synchronizeHScale_ )
        return;

    // - get the exposure from the nearest scale position
    piint exposure = static_cast<piint>( gtk_range_get_value( range ) + 0.5 );

    // - update the entry
    std::ostringstream oss;
    oss << exposure;
    GtkEntry* entry =
        GTK_ENTRY(gtk_builder_get_object( exposure_, "exposure_entry" ));
    gtk_entry_set_text( entry, oss.str().c_str() );

    // - set exposure in the camera
    ApplyExposureTime( exposure );
}

////////////////////////////////////////////////////////////////////////////////
// CloseExposureDialog
// - handles closing of the exposure dialog
////////////////////////////////////////////////////////////////////////////////
void CloseExposureDialog(
    GtkDialog* dialog,
    gint /*response_id*/,
    gpointer /*user_data*/ )
{
    // - clean up
    gtk_widget_destroy( GTK_WIDGET(dialog) );
    g_object_unref( G_OBJECT(exposure_) );
    exposure_ = 0;
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
// - initializes and shows the repetitive gate dialog
////////////////////////////////////////////////////////////////////////////////
void InitializeRepetitiveGateDialog()
{
    // - create the dialog
    repetitiveGate_ =
        LoadDialog(
            _binary_advanced_repetitive_gate_dialog_ui_start,
            _binary_advanced_repetitive_gate_dialog_ui_end );
    if( !repetitiveGate_ )
        return;

    // - set scale ranges from 1-1000 us
    GtkHScale* delayScale =
        GTK_HSCALE(gtk_builder_get_object( repetitiveGate_, "delay_hscale" ));
    GtkHScale* widthScale =
        GTK_HSCALE(gtk_builder_get_object( repetitiveGate_, "width_hscale" ));
    gtk_range_set_range( GTK_RANGE(delayScale), 1., 1000. );
    gtk_range_set_range( GTK_RANGE(widthScale), 1., 1000. );

    // - set scale step and page increments to 1 and 100 us
    gtk_range_set_increments( GTK_RANGE(delayScale), 1., 100. );
    gtk_range_set_increments( GTK_RANGE(widthScale), 1., 100. );

    // - reflect current pulse
    RefreshRepetitiveGateDialog();

    // - connect all signal handlers
    GtkButton* submit =
        GTK_BUTTON(
            gtk_builder_get_object( repetitiveGate_, "submit_delay_button" ));
    g_signal_connect(
        submit,
        "clicked",
        G_CALLBACK(ApplyRepetitiveGateDelayText),
        0 );
    submit =
        GTK_BUTTON(
            gtk_builder_get_object( repetitiveGate_, "submit_width_button" ));
    g_signal_connect(
        submit,
        "clicked",
        G_CALLBACK(ApplyRepetitiveGateWidthText),
        0 );
    g_signal_connect(
        delayScale,
        "value-changed",
        G_CALLBACK(ApplyRepetitiveGateDelayPosition),
        0 );
    g_signal_connect(
        widthScale,
        "value-changed",
        G_CALLBACK(ApplyRepetitiveGateWidthPosition),
        0 );
    GtkDialog* dialog =
        GTK_DIALOG(gtk_builder_get_object( repetitiveGate_, "dialog" ));
    g_signal_connect(
        dialog,
        "response",
        G_CALLBACK(CloseRepetitiveGateDialog),
        0 );

    // - show the dialog
    gtk_widget_show_all( GTK_WIDGET(dialog) );
}

////////////////////////////////////////////////////////////////////////////////
// RefreshRepetitiveDialog
// - refreshes the pulse information in the repetitive gate dialog
////////////////////////////////////////////////////////////////////////////////
void RefreshRepetitiveGateDialog()
{
    // - get the current set up repetitive gate
    PicamHandle model;
    PicamError error = PicamAdvanced_GetCameraModel( device_, &model );
    if( error != PicamError_None )
    {
        DisplayError( "Failed to get camera model.", error );
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
        DisplayError( "Failed to get repetitive gate.", error );
        return;
    }
    piflt delay = pulse->delay/1000.;
    piflt width = pulse->width/1000.;
    Picam_DestroyPulses( pulse );

    // - set delay and width text in entries
    std::ostringstream oss1;
    oss1 << delay;
    GtkEntry* entry =
        GTK_ENTRY(gtk_builder_get_object( repetitiveGate_, "delay_entry" ));
    gtk_entry_set_text( entry, oss1.str().c_str() );
    std::ostringstream oss2;
    oss2 << width;
    entry =
        GTK_ENTRY(gtk_builder_get_object( repetitiveGate_, "width_entry" ));
    gtk_entry_set_text( entry, oss2.str().c_str() );

    // - synchronize scale to to nearest steps based on pulse
    piint position = static_cast<piint>( delay + 0.5 );
    GtkHScale* scale =
        GTK_HSCALE(gtk_builder_get_object( repetitiveGate_, "delay_hscale" ));
    synchronizeHScale_ = true;
    gtk_range_set_value( GTK_RANGE(scale), position );
    position = static_cast<piint>( width + 0.5 );
    scale =
        GTK_HSCALE(gtk_builder_get_object( repetitiveGate_, "width_hscale" ));
    gtk_range_set_value( GTK_RANGE(scale), position );
    synchronizeHScale_ = false;
}

////////////////////////////////////////////////////////////////////////////////
// ApplyRepetitiveGateDelayText
// - sets the repetitive gate delay from the entry
////////////////////////////////////////////////////////////////////////////////
void ApplyRepetitiveGateDelayText(
    GtkButton* /*button*/,
    gpointer /*user_data*/ )
{
    // - get the text from the entry
    GtkEntry* entry =
        GTK_ENTRY(gtk_builder_get_object( repetitiveGate_, "delay_entry" ));
    std::string text( gtk_entry_get_text( entry ) );

    // - parse the text
    piflt delay;
    std::istringstream iss( text );
    iss >> delay >> std::ws;
    if( iss.fail() || !iss.eof() )
    {
        DisplayError( "Invalid format for delay." );
        return;
    }

    // - synchronize the scale
    piint position = static_cast<piint>( delay + 0.5 );
    GtkHScale* scale =
        GTK_HSCALE(gtk_builder_get_object( repetitiveGate_, "delay_hscale" ));
    synchronizeHScale_ = true;
    gtk_range_set_value( GTK_RANGE(scale), position );
    synchronizeHScale_ = false;

    // - get the current set up repetitive gate width
    PicamHandle model;
    PicamError error = PicamAdvanced_GetCameraModel( device_, &model );
    if( error != PicamError_None )
    {
        DisplayError( "Failed to get camera model.", error );
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
        DisplayError( "Failed to get repetitive gate.", error );
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
// - sets the repetitive gate width from the entry
////////////////////////////////////////////////////////////////////////////////
void ApplyRepetitiveGateWidthText(
    GtkButton* /*button*/,
    gpointer /*user_data*/ )
{
    // - get the text from the entry
    GtkEntry* entry =
        GTK_ENTRY(gtk_builder_get_object( repetitiveGate_, "width_entry" ));
    std::string text( gtk_entry_get_text( entry ) );

    // - parse the text
    piflt width;
    std::istringstream iss( text );
    iss >> width >> std::ws;
    if( iss.fail() || !iss.eof() )
    {
        DisplayError( "Invalid format for width." );
        return;
    }

    // - synchronize the scale
    piint position = static_cast<piint>( width + 0.5 );
    GtkHScale* scale =
        GTK_HSCALE(gtk_builder_get_object( repetitiveGate_, "width_hscale" ));
    synchronizeHScale_ = true;
    gtk_range_set_value( GTK_RANGE(scale), position );
    synchronizeHScale_ = false;

    // - get the current set up repetitive gate delay
    PicamHandle model;
    PicamError error = PicamAdvanced_GetCameraModel( device_, &model );
    if( error != PicamError_None )
    {
        DisplayError( "Failed to get camera model.", error );
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
        DisplayError( "Failed to get repetitive gate.", error );
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
// - sets the repetitive gate delay from the scale
////////////////////////////////////////////////////////////////////////////////
void ApplyRepetitiveGateDelayPosition(
    GtkRange* range,
    gpointer /*user_data*/ )
{
    // - do nothing if this update was due to synchronizing from the entry
    if( synchronizeHScale_ )
        return;

    // - get the current set up repetitive gate width
    PicamHandle model;
    PicamError error = PicamAdvanced_GetCameraModel( device_, &model );
    if( error != PicamError_None )
    {
        DisplayError( "Failed to get camera model.", error );
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
        DisplayError( "Failed to get repetitive gate.", error );
        return;
    }
    piflt width = pulse->width;
    Picam_DestroyPulses( pulse );

    // - get the delay from the nearest scale position
    piint delay = static_cast<piint>( gtk_range_get_value( range ) + 0.5 );

    // - update the entry
    std::ostringstream oss;
    oss << delay;
    GtkEntry* entry =
        GTK_ENTRY(gtk_builder_get_object( repetitiveGate_, "delay_entry" ));
    gtk_entry_set_text( entry, oss.str().c_str() );

    // - set repetitive gate in the camera
    PicamPulse value = { delay*1000., width };
    ApplyRepetitiveGate( value );
}

////////////////////////////////////////////////////////////////////////////////
// ApplyRepetitiveGateWidthPosition
// - sets the repetitive gate width from the scale
////////////////////////////////////////////////////////////////////////////////
void ApplyRepetitiveGateWidthPosition(
    GtkRange* range,
    gpointer /*user_data*/ )
{
    // - do nothing if this update was due to synchronizing from the entry
    if( synchronizeHScale_ )
        return;

    // - get the current set up repetitive gate delay
    PicamHandle model;
    PicamError error = PicamAdvanced_GetCameraModel( device_, &model );
    if( error != PicamError_None )
    {
        DisplayError( "Failed to get camera model.", error );
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
        DisplayError( "Failed to get repetitive gate.", error );
        return;
    }
    piflt delay = pulse->delay;
    Picam_DestroyPulses( pulse );

    // - get the width from the nearest scale position
    piint width = static_cast<piint>( gtk_range_get_value( range ) + 0.5 );

    // - update the entry
    std::ostringstream oss;
    oss << width;
    GtkEntry* entry =
        GTK_ENTRY(gtk_builder_get_object( repetitiveGate_, "width_entry" ));
    gtk_entry_set_text( entry, oss.str().c_str() );

    // - set repetitive gate in the camera
    PicamPulse value = { delay, width*1000. };
    ApplyRepetitiveGate( value );
}

////////////////////////////////////////////////////////////////////////////////
// CloseRepetitiveGateDialog
// - handles closing of the repetitive gate dialog
////////////////////////////////////////////////////////////////////////////////
void CloseRepetitiveGateDialog(
    GtkDialog* dialog,
    gint /*response_id*/,
    gpointer /*user_data*/ )
{
    // - clean up
    gtk_widget_destroy( GTK_WIDGET(dialog) );
    g_object_unref( G_OBJECT(repetitiveGate_) );
    repetitiveGate_ = 0;
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
// SelectFromCamerasDialog
// - shows the cameras dialog and returns the selected camera
// - takes the lock
////////////////////////////////////////////////////////////////////////////////
const PicamCameraID* SelectFromCamerasDialog()
{
    // - create the dialog
    GtkBuilder* builder =
        LoadDialog(
            _binary_advanced_cameras_dialog_ui_start,
            _binary_advanced_cameras_dialog_ui_end );
    if( !builder )
        return 0;

    // - store cameras dialog
    AutoLock al( lock_ );
    cameras_ = builder;
    al.Release();

    // - populate camera controls
    RefreshCamerasDialog();

    // - populate the available demo models
    const PicamModel* models;
    piint modelCount;
    PicamError error =
        Picam_GetAvailableDemoCameraModels( &models, &modelCount );
    if( error != PicamError_None )
    {
        DisplayError( "Failed to get demo camera models.", error );
        g_object_unref( G_OBJECT(builder) );
        AutoLock al( lock_ );
        cameras_ = 0;
        return 0;
    }
    GtkListStore* demos =
        GTK_LIST_STORE(gtk_builder_get_object( builder, "demo_model" ));
    for( piint i = 0; i < modelCount; ++i )
    {
        // - create a string version of the model
        std::string item =
            GetEnumString( PicamEnumeratedType_Model, models[i] );

        // - add the string and model to the list
        GtkTreeIter iter;
        gtk_list_store_append( demos, &iter );
        gtk_list_store_set( demos, &iter, 0, item.c_str(), 1, models[i], -1 );
    }
    Picam_DestroyModels( models );
    GtkTreeModel* sortedModels =
        gtk_tree_model_sort_new_with_model( GTK_TREE_MODEL(demos) );
    gtk_tree_sortable_set_sort_column_id(
        GTK_TREE_SORTABLE(sortedModels),
        0,
        GTK_SORT_ASCENDING );
    GtkComboBox* demoComboBox =
        GTK_COMBO_BOX(
            gtk_builder_get_object(
                cameras_,
                "selected_demo_camera_combo_box" ));
    gtk_combo_box_set_model( demoComboBox, sortedModels );

    // - set a default serial number
    GtkEntry* entry =
        GTK_ENTRY(
            gtk_builder_get_object(
                builder,
                "demo_camera_serial_number_entry" ));
    gtk_entry_set_text( entry, "00000" );

    // - connect all signal handlers
    GtkButton* connect =
        GTK_BUTTON(
            gtk_builder_get_object( builder, "connect_demo_camera_button" ));
    g_signal_connect( connect, "clicked", G_CALLBACK(ConnectDemoCamera), 0 );

    // - show the modal dialog
    GtkDialog* dialog = GTK_DIALOG(gtk_builder_get_object( builder, "dialog" ));
    gint response = ShowModalDialog( dialog );

    // - get the selected camera
    const PicamCameraID* id = 0;
    if( response == GTK_RESPONSE_OK )
        id = ApplyCamerasDialog();

    // - clean up
    gtk_widget_destroy( GTK_WIDGET(dialog) );
    g_object_unref( G_OBJECT(builder) );
    AutoLock al2( lock_ );
    cameras_ = 0;

    return id;
}

////////////////////////////////////////////////////////////////////////////////
// RefreshCamerasDialog
// - refreshes the camera information in the cameras dialog
// - takes the lock
////////////////////////////////////////////////////////////////////////////////
void RefreshCamerasDialog()
{
    // - lock before accessing shared state
    AutoLock al( lock_ );

    // - nothing to do if dialog is no longer open as this refresh could have
    //   been posted from another thread
    if( !cameras_ )
        return;

    // - get the camera lists
    GtkListStore* selected =
        GTK_LIST_STORE(
            gtk_builder_get_object( cameras_, "selected_camera_model" ));
    GtkListStore* available =
        GTK_LIST_STORE(
            gtk_builder_get_object( cameras_, "available_camera_model" ));
    GtkListStore* unavailable =
        GTK_LIST_STORE(
            gtk_builder_get_object( cameras_, "unavailable_camera_model" ));

    // - clear the lists
    gtk_list_store_clear( selected );
    gtk_list_store_clear( available );
    gtk_list_store_clear( unavailable );

    // - populate the selected and available lists
    for( std::list<PicamCameraID>::const_iterator i = available_.begin();
         i != available_.end();
         ++i )
    {
        // - create a string version of the camera id
        std::ostringstream oss;
        oss << GetEnumString( PicamEnumeratedType_Model, i->model )
             << " (SN: " << i->serial_number << ")";
        std::string item( oss.str() );

        // - add the string to the lists
        GtkTreeIter iter;
        gtk_list_store_append( selected, &iter );
        gtk_list_store_set( selected, &iter, 0, item.c_str(), -1 );
        gtk_list_store_append( available, &iter );
        gtk_list_store_set( available, &iter, 0, item.c_str(), -1 );
    }

    // - populate the unavailable list
    for( std::list<PicamCameraID>::const_iterator i = unavailable_.begin();
         i != unavailable_.end();
         ++i )
    {
        // - create a string version of the camera id
        std::ostringstream oss;
        oss << GetEnumString( PicamEnumeratedType_Model, i->model )
             << " (SN: " << i->serial_number << ")";
        std::string item( oss.str() );

        // - add the string to the list
        GtkTreeIter iter;
        gtk_list_store_append( unavailable, &iter );
        gtk_list_store_set( unavailable, &iter, 0, item.c_str(), -1 );
    }

    // - select the open camera
    PicamCameraID deviceID;
    if( device_ && Picam_GetCameraID( device_, &deviceID ) == PicamError_None )
    {
        gint index = 0;
        for( std::list<PicamCameraID>::const_iterator i = available_.begin();
             i != available_.end();
             ++i, ++index )
        {
            if( *i == deviceID )
            {
                GtkComboBox* selectedComboBox =
                    GTK_COMBO_BOX(
                        gtk_builder_get_object(
                            cameras_,
                            "selected_camera_combo_box" ));
                gtk_combo_box_set_active( selectedComboBox, index );
                break;
            }
        }
    }
}

////////////////////////////////////////////////////////////////////////////////
// ConnectDemoCamera
// - connects a demo camera defined in the cameras dialog
////////////////////////////////////////////////////////////////////////////////
void ConnectDemoCamera( GtkButton* /*button*/, gpointer /*user_data*/ )
{
    // - get selected demo camera model (if any)
    GtkComboBox* demoComboBox =
        GTK_COMBO_BOX(
            gtk_builder_get_object(
                cameras_,
                "selected_demo_camera_combo_box" ));
    GtkTreeIter selectedIter;
    if( !gtk_combo_box_get_active_iter( demoComboBox, &selectedIter ) )
        return;
    gint selectedModel;
    gtk_tree_model_get(
        gtk_combo_box_get_model( demoComboBox ),
        &selectedIter,
        1,
        &selectedModel,
        -1 );

    // - get the serial number
    GtkEntry* serialNumberEntry =
        GTK_ENTRY(
            gtk_builder_get_object(
                cameras_,
                "demo_camera_serial_number_entry" ));
    std::string serialNumber( gtk_entry_get_text( serialNumberEntry ) );
    if( serialNumber.empty() )
    {
        DisplayError( "Serial number required." );
        return;
    }

    // - connect the model
    PicamModel model = static_cast<PicamModel>( selectedModel );
    PicamError error =
        Picam_ConnectDemoCamera( model, serialNumber.c_str(), 0 );
    if( error != PicamError_None )
        DisplayError( "Failed to connect demo camera.", error );
}

////////////////////////////////////////////////////////////////////////////////
// ApplyCamerasDialog
// - handles acceptance from the cameras dialog
// - takes the lock
////////////////////////////////////////////////////////////////////////////////
const PicamCameraID* ApplyCamerasDialog()
{
    const PicamCameraID* id = 0;

    // - lock before accessing shared state
    AutoLock al( lock_ );

    // - get selected camera (if any)
    GtkComboBox* selectedComboBox =
        GTK_COMBO_BOX(
            gtk_builder_get_object(
                cameras_,
                "selected_camera_combo_box" ));
    GtkTreeIter selectedIter;
    if( gtk_combo_box_get_active_iter( selectedComboBox, &selectedIter ) )
    {
        GtkListStore* cameras =
            GTK_LIST_STORE(
                gtk_builder_get_object( cameras_, "selected_camera_model" ));
        gchar* selectedCamera;
        gtk_tree_model_get(
            GTK_TREE_MODEL(cameras),
            &selectedIter,
            0,
            &selectedCamera,
            -1 );
        std::string selected( selectedCamera );
        g_free( selectedCamera );

        // - find a matching available id
        for( std::list<PicamCameraID>::const_iterator i = available_.begin();
             i != available_.end() && !selected.empty();
             ++i )
        {
            // - create a string version of the camera id
            std::ostringstream oss;
            oss << GetEnumString( PicamEnumeratedType_Model, i->model )
                 << " (SN: " << i->serial_number << ")";

            // - set the result if a match is found
            if( selected == oss.str() )
            {
                id = new PicamCameraID( *i );
                break;
            }
        }
    }

    return id;
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
// QuitApplication
// - quits the GTK application
////////////////////////////////////////////////////////////////////////////////
void QuitApplication( GtkWidget* /*object*/ = 0, gpointer /*user_data*/ = 0 )
{
    gtk_main_quit();
}

////////////////////////////////////////////////////////////////////////////////
// ProcessMenuAction
// - handles main window menu
////////////////////////////////////////////////////////////////////////////////
void ProcessMenuAction( GtkAction* action, gpointer /*user_data*/ )
{
    std::string name = gtk_action_get_name( action );
    if( name == "save_frame" )
        SaveFrame();
    else if( name == "quit" )
        QuitApplication();
    else if( name == "set_exposure_time" )
        SetExposureTime();
    else if( name == "set_repetitive_gate" )
        SetRepetitiveGate();
    else if( name == "set_parameters" )
        SetParameters();
    else if( name == "select_camera" )
        SelectCamera( false /*selectDefault*/ );
    else if( name == "preview" )
        Preview();
    else if( name == "acquire" )
        Acquire();
    else if( name == "stop" )
        Stop();
}

////////////////////////////////////////////////////////////////////////////////
// Redraw
// - repaints the main window
// - takes the lock
////////////////////////////////////////////////////////////////////////////////
gboolean Redraw(
    GtkWidget* widget,
    GdkEvent* /*event*/,
    gpointer /*user_data*/ )
{
    // - set a black background
    cairo_t* cr = gdk_cairo_create( gtk_widget_get_window( widget ) );
    cairo_set_source_rgb( cr, 0., 0., 0. );
    cairo_paint( cr );

    // - do nothing if no image surface created yet
    if( !surface_ )
    {
        cairo_destroy( cr );
        return false;
    }

    // - get the bounding area
    GtkAllocation allocation;
    gtk_widget_get_allocation( widget, &allocation );

    // - update shared bitmap information
    piint surfaceWidth, surfaceHeight;
    AutoLock al( lock_ );
    if( !renderedImage_ )
    {
        cairo_destroy( cr );
        return false;
    }
    surfaceWidth = imageDataWidth_;
    surfaceHeight = imageDataHeight_;
    if( surfaceVersion_ != renderedImageVersion_ )
    {
        std::memcpy(
            surfaceData_,
            &(*renderedImage_)[0],
            renderedImage_->size() );
        surfaceVersion_ = renderedImageVersion_;
        cairo_surface_mark_dirty( surface_ );
    }
    al.Release();

    // - determine best-fit scaling
    piflt scaleWidth  = static_cast<piflt>( allocation.width  ) / surfaceWidth;
    piflt scaleHeight = static_cast<piflt>( allocation.height ) / surfaceHeight;
    piflt scale = std::min( scaleWidth, scaleHeight );

    // - determine image area
    piint width = static_cast<piint>( surfaceWidth*scale + 0.5 );
    piint height = static_cast<piint>( surfaceHeight*scale + 0.5 );
    piint x =
        static_cast<piint>( std::abs( width-allocation.width )/2 + 0.5 );
    piint y =
        static_cast<piint>( std::abs( height-allocation.height )/2 + 0.5 );

    // - draw image
    cairo_translate( cr, x, y );
    cairo_scale( cr, scale, scale );
    cairo_set_source_surface( cr, surface_, 0, 0 );
    cairo_paint( cr );

    // - clean up
    cairo_destroy( cr );

    return false;
}

////////////////////////////////////////////////////////////////////////////////
// InitializeMainWindow
// - creates and shows the main window
////////////////////////////////////////////////////////////////////////////////
pibool InitializeMainWindow()
{
    // - create the main window to be shown
    GtkBuilder* builder = gtk_builder_new();
    const gchar* ui = _binary_advanced_main_window_ui_start;
    gint size =
        _binary_advanced_main_window_ui_end - 
        _binary_advanced_main_window_ui_start;
    GError* error = 0;
    if( !gtk_builder_add_from_string( builder, ui, size, &error ) )
    {
        DisplayError( error->message );
        g_error_free( error );
        g_object_unref( G_OBJECT(builder) );
        return false;
    }
    main_ = GTK_WINDOW(gtk_builder_get_object( builder, "main_window" ));

    // - connect all signal handlers
    const gchar* actions[] =
    {
        "save_frame",
        "quit",
        "set_parameters",
        "set_exposure_time",
        "set_repetitive_gate",
        "select_camera",
        "preview",
        "acquire",
        "stop"
    };
    for( unsigned i = 0; i < sizeof(actions)/sizeof(*actions); ++i )
    {
        g_signal_connect(
            gtk_builder_get_object( builder, actions[i] ),
            "activate",
            G_CALLBACK(ProcessMenuAction),
            0 );
    }
    GtkDrawingArea* drawing =
            GTK_DRAWING_AREA(gtk_builder_get_object( builder, "drawing" ));
    g_signal_connect( drawing, "expose-event", G_CALLBACK(Redraw), 0 );
    g_signal_connect( drawing, "configure-event", G_CALLBACK(Redraw), 0 );
    g_signal_connect( main_, "destroy", G_CALLBACK(QuitApplication), 0 );

    // - clean up the builder
    g_object_unref( G_OBJECT(builder) );

    // - create the wait cursor
    waitCursor_ = gdk_cursor_new( GDK_WATCH );

    // - create the acquiring cursor
    acquiringCursor_ = gdk_cursor_new( GDK_SPIDER );

    // - show the main window
    gtk_widget_show_all( GTK_WIDGET(main_) );

    // - cache the drawing area window
    drawingWindow_ = gtk_widget_get_window( GTK_WIDGET(drawing) );

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
// main
// - operating system entry point
////////////////////////////////////////////////////////////////////////////////
piint main( piint argc, pichar* argv[] )
{
    // - create and show the main application window
    g_thread_init( 0 );
    if( !gtk_init_check( &argc, &argv ) )
        return ExitCode_InitializeGtkFailed;
    if( !InitializeMainWindow() )
        return ExitCode_InitializeMainWindowFailed;

    // - initialize state and picam
    if( !Initialize() )
        return ExitCode_FailedInitialize;

    // - try to select a default camera
    SelectCamera( true /*selectDefault*/ );

    // - process GTK signals and events until application is quit
    gtk_main();
    main_ = 0;

    // - clean up camera
    // - note other state is reclaimed by operating system when process exits
    Uninitialize();

    return ExitCode_Success;
}
