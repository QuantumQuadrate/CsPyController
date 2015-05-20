////////////////////////////////////////////////////////////////////////////////
// EM Gain Calibration Sample
// - exercises the picam em calibration api in a basic linux GTK application
////////////////////////////////////////////////////////////////////////////////

#include <gtk/gtk.h>
#include <stdlib.h>
#include <stdio.h>
#include <string.h>
#include "picam_em_calibration.h"

////////////////////////////////////////////////////////////////////////////////
// Embedded User Interface XML
////////////////////////////////////////////////////////////////////////////////
extern "C" const gchar _binary_em_gain_calibration_dialog_ui_start[];
extern "C" const gchar _binary_em_gain_calibration_dialog_ui_end[];
////////////////////////////////////////////////////////////////////////////////
// Dialog Function Prototypes
////////////////////////////////////////////////////////////////////////////////
void InitializeForGain();
bool UpdateCurrentTemperature();
bool UpdateCalibrationDate();
bool UpdateTemperatureSetPoint();
void UninitializeForGain();
void BeginCalibration();
void EndCalibration();
gboolean UpdateCalibrationState(gpointer user_data);
gboolean UpdateCalibrationProgress(gpointer user_data);
void CalibrateGain(GtkButton* button, gpointer user_data);
void CloseDialog(GtkButton* button, gpointer user_data);
void QuitApplication(GtkDialog* dialog, gint response_id, gpointer user_data);
void UpdateMessage(const gchar* message);
////////////////////////////////////////////////////////////////////////////////
// State
////////////////////////////////////////////////////////////////////////////////
PicamHandle calibration_ = NULL; 
GThread* calibrationThread_ = NULL;
GtkBuilder* ui_ = NULL;
GMutex* lock_ = NULL;                 // - protects all shared state below
pibool calibrating_ = false;
////////////////////////////////////////////////////////////////////////////////
enum CalibrationState 
{
    WaitingForTemperatureStability,
    TemperatureLockError,
    PerformingCalibration,
    SuccessfullCalibration,
    CancelledCalibration,
    FailedCalibration
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
    bool released_;
};
////////////////////////////////////////////////////////////////////////////////
void SetCalibrationState(CalibrationState state)
{
    g_idle_add_full(
        G_PRIORITY_HIGH,
        UpdateCalibrationState,
        new CalibrationState(state),
        0);
}
////////////////////////////////////////////////////////////////////////////////
void SetCalibrationProgress(piflt progress)
{
    g_idle_add_full(
        G_PRIORITY_HIGH,
        UpdateCalibrationProgress,
        new piflt(progress/100.0),
        0);
}
////////////////////////////////////////////////////////////////////////////////
// Main Routine, Just Create a Model Dialog (When it closes we are
// done anyhow)
////////////////////////////////////////////////////////////////////////////////
piint main(piint argc, pichar* argv[])
{
    g_thread_init(0);
    gtk_init(&argc, &argv);

    ui_ = gtk_builder_new();
    const gchar* ui = _binary_em_gain_calibration_dialog_ui_start;
    gint size =
        _binary_em_gain_calibration_dialog_ui_end - 
        _binary_em_gain_calibration_dialog_ui_start;
    if (!gtk_builder_add_from_string(ui_, ui, size, 0))
    {
        g_object_unref(G_OBJECT(ui_));
        return -1;
    }
    
    InitializeForGain();

    g_signal_connect(
        GTK_BUTTON(gtk_builder_get_object(ui_, "calibrate_button")),
        "clicked",
        G_CALLBACK(CalibrateGain),
        0);
    g_signal_connect(
        GTK_BUTTON(gtk_builder_get_object(ui_, "close_button")),
        "clicked",
        G_CALLBACK(CloseDialog),
        0);
    GtkDialog* dialog = GTK_DIALOG(gtk_builder_get_object(ui_, "dialog"));
    g_signal_connect(
        dialog,
        "response",
        G_CALLBACK(QuitApplication),
        0 );
    gtk_widget_show_all(gtk_dialog_get_content_area(dialog));
    gtk_widget_show_all(gtk_dialog_get_action_area(dialog));
    gtk_dialog_run(dialog);
    gtk_widget_destroy(GTK_WIDGET(dialog));
    g_object_unref(G_OBJECT(ui_));

    UninitializeForGain();

    return 0;
}
////////////////////////////////////////////////////////////////////////////////
// Disable Controls (Button and Temperature Entry)
////////////////////////////////////////////////////////////////////////////////
void DisableControls()
{	
    gtk_widget_set_sensitive(
        GTK_WIDGET(gtk_builder_get_object(ui_, "calibrate_button")),
        false);
    gtk_widget_set_sensitive(
        GTK_WIDGET(gtk_builder_get_object(ui_, "target_entry")),
        false);
}
////////////////////////////////////////////////////////////////////////////////
// Enable Controls (Button and Temperature Entry)
////////////////////////////////////////////////////////////////////////////////
void EnableControls()
{	
    gtk_widget_set_sensitive(
        GTK_WIDGET(gtk_builder_get_object(ui_, "calibrate_button")),
        true);
    gtk_widget_set_sensitive(
        GTK_WIDGET(gtk_builder_get_object(ui_, "target_entry")),
        true);
}
////////////////////////////////////////////////////////////////////////////////
// If some error has occurred we can not continue show the error 
// and disable the dialog.
////////////////////////////////////////////////////////////////////////////////
bool CheckPicamIsValid(PicamError errCode)
{    
    if (errCode != PicamError_None) 
    {                
        // Get the error string, the called function allocates the memory 
        const pichar *errString;
        Picam_GetEnumerationString(PicamEnumeratedType_Error, errCode, &errString);
        
        UpdateMessage(errString);

        // Since the called function allocated the memory it must free it 
        Picam_DestroyString(errString);

        // There is an error
        return false;
    }
    // There is no error
    return true;
}
////////////////////////////////////////////////////////////////////////////////
// Setup the camera and dialog for the gain calibration function
////////////////////////////////////////////////////////////////////////////////
void InitializeForGain()
{
    PicamError errCode              = PicamError_None;	
    const PicamCameraID *cameraList = 0;    
    piint cameraCount               = 0;

    // Locking Mutex
    lock_ = g_mutex_new();

    // Assume errors
    DisableControls(); 

    // Initialize Library
    errCode = Picam_InitializeLibrary();
        
    if (errCode == PicamError_None)
    {
        // Get available cameras
        errCode = Picam_GetAvailableCameraIDs(&cameraList, &cameraCount);
              
        if (errCode == PicamError_None)
        {
            // Open for calibration (1st camera)
            if (cameraCount > 0)                            
                errCode = PicamEMCalibration_OpenCalibration(&cameraList[0], &calibration_);
            else
                UpdateMessage("No Camera Found");
                            
            // Destroy the List
            Picam_DestroyCameraIDs(cameraList); 
        }
    }
    // Check for an error, if there is no error than update the dialog from the camera
    if (CheckPicamIsValid(errCode) && cameraCount > 0)
    {
        // Update The Date
        if (UpdateCalibrationDate())
        {
            // Update Temperature
            if (UpdateCurrentTemperature())
            {       
                // Get The Temperature
                if (UpdateTemperatureSetPoint())
                {
                    // Complete success we can enable the calibration button
                    EnableControls();
                }
            }
        }
    }
}
////////////////////////////////////////////////////////////////////////////////
// Read the temperature and update the dialog with the temperature set point
////////////////////////////////////////////////////////////////////////////////
bool UpdateTemperatureSetPoint()
{
    PicamError errCode = PicamError_None;	
    // Temperature Set Point
    piflt temp;
    
    errCode = PicamEMCalibration_GetSensorTemperatureSetPoint(calibration_, &temp);

    if (errCode == PicamError_None)
    {
        gchar buffer[32];	
        sprintf(buffer, "%.f", temp);
        gtk_entry_set_text(
            GTK_ENTRY(gtk_builder_get_object(ui_, "target_entry")),
            buffer);

        // Get the Constraints
        const PicamRangeConstraint *tempConstraint;
        errCode = PicamEMCalibration_GetSensorTemperatureSetPointConstraint(calibration_, &tempConstraint);

        // Update UI if no error
        if (errCode == PicamError_None)
        {
            gchar tempRange[64];	
            sprintf(tempRange, "Temperature (%.f to %.f)", tempConstraint->minimum, tempConstraint->maximum);
            gtk_frame_set_label(
                GTK_FRAME(gtk_builder_get_object(ui_, "temperature_frame")),
                tempRange);
        }
        // Free the constraint
        Picam_DestroyRangeConstraints(tempConstraint);
    }
    // Final Error Check
    return CheckPicamIsValid(errCode);
}
////////////////////////////////////////////////////////////////////////////////
// Get the date of the calibration and show it
////////////////////////////////////////////////////////////////////////////////
bool UpdateCalibrationDate()
{
    // Get Date
    PicamEMCalibrationDate date;
    PicamError errCode = PicamEMCalibration_GetCalibrationDate(calibration_, &date);	
    
    // Update UI if no error
    if (errCode == PicamError_None)
    {
        gchar buffer[32];	
        sprintf(buffer, "%02d/%02d/%04d", date.month, date.day, date.year);
        gtk_label_set_text(
            GTK_LABEL(gtk_builder_get_object(ui_, "last_calibration_label")),
            buffer);
    }
    // If the parameter does not exist we can continue since it simply means that
    // this device has never been calibrated
    else if (errCode == PicamError_ParameterDoesNotExist)
    {                
        gtk_label_set_text(
            GTK_LABEL(gtk_builder_get_object(ui_, "last_calibration_label")),
            "N/A");
        return true;
    }

    // Final Error Check
    return CheckPicamIsValid(errCode);
}
////////////////////////////////////////////////////////////////////////////////
// Get the current temperature 
////////////////////////////////////////////////////////////////////////////////
bool UpdateCurrentTemperature()
{
    // Get Current Temperature
    piflt currentTemp;
    PicamError errCode = PicamEMCalibration_ReadSensorTemperatureReading(calibration_, &currentTemp);

    // Update UI if no error
    if (errCode == PicamError_None)
    {    
        gchar buffer[32];
        sprintf(buffer, "%.f", currentTemp);
        gtk_label_set_text(
            GTK_LABEL(gtk_builder_get_object(ui_, "current_label")),
            buffer);
    }
    // Final Error Check
    return CheckPicamIsValid(errCode);
}
////////////////////////////////////////////////////////////////////////////////
// Set the temperature returning false if it fails
////////////////////////////////////////////////////////////////////////////////
bool SetTemperature(piflt temperature)
{       
    // Final Error Check
    return CheckPicamIsValid(PicamEMCalibration_SetSensorTemperatureSetPoint(calibration_, temperature));
}
////////////////////////////////////////////////////////////////////////////////
void UninitializeForGain()
{    
    // Close The Camera & Clean up
    if (calibration_ != NULL)
        PicamEMCalibration_CloseCalibration(calibration_);	

    Picam_UninitializeLibrary();
}
////////////////////////////////////////////////////////////////////////////////
pibln PIL_CALL CalibrationCallback(PicamHandle, 
                                   piflt progress, 
                                   void*)
{
    bool calibRunning = true;

    // User Cancel Button Check
    AutoLock al(lock_);
    calibRunning = calibrating_;
    al.Release();

    // Still Running
    if (calibRunning)
    {
        // Update the progress position on the dialog        
        SetCalibrationProgress(progress);
        return 1;
    }
    // Cancelling (User pressed the cancel button) but the calibration can only die
    // during a callback or error
    else
        return 0;
}
////////////////////////////////////////////////////////////////////////////////
gpointer CalibrationThread(gpointer)
{
    int lockCount = 0;
    int stableTime= 5;
    bool stableTemp= false;
    bool cancel = false;
    
    PicamSensorTemperatureStatus locked = PicamSensorTemperatureStatus_Unlocked;	
    do 
    {
        // Wait for temperature    
        SetCalibrationState(WaitingForTemperatureStability);
        
        // Polling Delay
        g_usleep( 1e6 );

        // Serialize picam calls
        AutoLock al(lock_);
        // User Cancel Button Check
        if (!calibrating_)
            cancel = true;
        // Check for stable temperature
        PicamError error = PicamEMCalibration_ReadSensorTemperatureStatus(calibration_, &locked);
        al.Release();

        // Check if ok to continue
        if (error != PicamError_None)
        {
            SetCalibrationState(TemperatureLockError);
            EndCalibration();      
            return 0;
        }
        if (locked != PicamSensorTemperatureStatus_Locked)
            lockCount = 0;
        else 
            lockCount++;

        if (lockCount >= stableTime)
            stableTemp = true;
    } 
    while (!stableTemp && !cancel);
        
    // Perform the calibration
    if ((stableTemp) && (!cancel))
    {
        // Performing State
        SetCalibrationState(PerformingCalibration);

        PicamError error = PicamEMCalibration_Calibrate(calibration_, CalibrationCallback, NULL);
        if (error == PicamError_None)
            SetCalibrationState(SuccessfullCalibration);
        // The calibration has been cancelled or failed (either by the user or by the routine)
        else if (error == PicamError_OperationCanceled)
            cancel = true;
        else
            SetCalibrationState(FailedCalibration);
    }
    // If the cancel flag is set show the cancelled message.
    if (cancel)	
        SetCalibrationState(CancelledCalibration);
   
    // End the calibration
    EndCalibration();        

    return 0;
}
////////////////////////////////////////////////////////////////////////////////
void BeginCalibration()
{	        
    const gchar* buffer = gtk_entry_get_text(GTK_ENTRY(gtk_builder_get_object(ui_, "target_entry")));

    // Convert the temperature string into a double string
    gchar* endPtr;
    piflt temperature = strtod(buffer, &endPtr);
    if (*endPtr != 0) 
    {
        UpdateMessage("Temperature Must Be A Number");                
        return;
    }

    // Set the temperature from the control
    if (!SetTemperature(temperature))
        return;

    // Begin the thread
    AutoLock al(lock_);
    calibrating_ = true;    
    al.Release();   
    gtk_button_set_label(
        GTK_BUTTON(gtk_builder_get_object(ui_, "calibrate_button")),
        "Abort");
    calibrationThread_ = g_thread_create(CalibrationThread, NULL, true, NULL);
}
////////////////////////////////////////////////////////////////////////////////
void EndCalibration()
{
    AutoLock al(lock_);    
    calibrating_ = false;                
}
////////////////////////////////////////////////////////////////////////////////
gboolean UpdateCalibrationState(gpointer user_data)
{
    CalibrationState* state = static_cast<CalibrationState*>(user_data);
    switch (*state)
    {
        case WaitingForTemperatureStability:
        {
            // Serialize picam calls
            AutoLock al(lock_);
            bool status = UpdateCurrentTemperature();
            al.Release();
            if (status)
                UpdateMessage("Waiting For Temperature");
            else
            {
                UpdateMessage("Failed Reading Temperature");
                EndCalibration();            
            }
            break;
        }
        case TemperatureLockError:
            UpdateMessage("Failed Checking Temperature Lock");
            break;
        case PerformingCalibration:
            gtk_label_set_text(
                GTK_LABEL(gtk_builder_get_object(ui_, "current_label")),
                "Locked");
            UpdateMessage("Performing Calibration");
            break;
        case SuccessfullCalibration:
            UpdateMessage("Calibration Successful");
            UpdateCalibrationDate();
            break;
        case CancelledCalibration:
            UpdateMessage("Calibration Cancelled");
            break;
        case FailedCalibration:
            UpdateMessage("Calibration Failed");
            break;
    }
    if ((*state != WaitingForTemperatureStability) && (*state != PerformingCalibration))
    {
        g_thread_join(calibrationThread_);
        calibrationThread_ = NULL;

        // Restore the button and progress to zero
        gtk_button_set_label(
            GTK_BUTTON(gtk_builder_get_object(ui_, "calibrate_button")),
            "Calibrate");
        gtk_progress_bar_set_fraction(
            GTK_PROGRESS_BAR(gtk_builder_get_object(ui_, "progress_bar")),
            0.0);
    }
    delete state;
    return false;
}
////////////////////////////////////////////////////////////////////////////////
gboolean UpdateCalibrationProgress(gpointer user_data)
{
    piflt* progress = static_cast<piflt*>(user_data);
    gtk_progress_bar_set_fraction(
        GTK_PROGRESS_BAR(gtk_builder_get_object(ui_, "progress_bar")),
        *progress);
    delete progress;
    return false;
}
////////////////////////////////////////////////////////////////////////////////
void CalibrateGain(GtkButton*, gpointer)
{	
    // If we are already in a calibration
    if (calibrationThread_)
    {
        // This provides instant status that cancelling has begun
        UpdateMessage("Cancelling Calibration");                
        EndCalibration();
    }
    // Otherwise start a calibration
    else
        BeginCalibration();                    						
}
////////////////////////////////////////////////////////////////////////////////
void CloseDialog(GtkButton*, gpointer)
{
    gtk_dialog_response(
        GTK_DIALOG(gtk_builder_get_object(ui_, "dialog")),
        GTK_RESPONSE_CLOSE);
}
////////////////////////////////////////////////////////////////////////////////
void QuitApplication(GtkDialog* dialog, gint, gpointer)
{
    // Handle the Exiting Case while a calibration is running
    if (calibrationThread_)
    {
        gtk_widget_hide(GTK_WIDGET(dialog));
        EndCalibration();
        g_thread_join(calibrationThread_);
    }
}
////////////////////////////////////////////////////////////////////////////////
void UpdateMessage(const gchar* message)
{
    gtk_label_set_text(
        GTK_LABEL(gtk_builder_get_object(ui_, "message_label")),
        message);
}
