////////////////////////////////////////////////////////////////////////////////
// EM Gain Calibration Sample
// - exercises the picam em calibration api in a basic windows application
////////////////////////////////////////////////////////////////////////////////

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

#define WINVER 0x600
#define WIN23_LEAN_AND_MEAN
#define UNICODE
#define NOMINMAX
#include <windows.h>
#include <process.h>
#include <commctrl.h>
#include <stdlib.h>
#include <stdio.h>
#include "picam_em_calibration.h"
#include "EmGainResource.h"

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
INT_PTR CALLBACK EMGainDialogProcedure(HWND hwndDlg, UINT uMsg, WPARAM wParam, LPARAM lParam);
////////////////////////////////////////////////////////////////////////////////
// Custom Window Messages
////////////////////////////////////////////////////////////////////////////////
#define WM_CALIBRATIONSTATE       (WM_USER + 1)
#define WM_CALIBRATIONPROGRESS    (WM_USER + 2)
////////////////////////////////////////////////////////////////////////////////
// State
////////////////////////////////////////////////////////////////////////////////
PicamHandle calibration_ = NULL; 
HANDLE calibrationThread_ = NULL;
HWND dialog_ = NULL;
CRITICAL_SECTION lock_;                 // - protects all shared state below
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
    bool released_;
};
////////////////////////////////////////////////////////////////////////////////
void SetCalibrationState(CalibrationState state)
{
    PostMessage(dialog_, WM_CALIBRATIONSTATE, state, 0);
}
////////////////////////////////////////////////////////////////////////////////
void SetCalibrationProgress(piflt progress)
{
    PostMessage(dialog_, WM_CALIBRATIONPROGRESS, (int)(progress*10.0), 0);    
}
////////////////////////////////////////////////////////////////////////////////
// Windows Main Routine, Just Create a Model Dialog (When it closes we are
// done anyhow)
////////////////////////////////////////////////////////////////////////////////
int CALLBACK WinMain(
    __in  HINSTANCE hInstance,
    __in  HINSTANCE hPrevInstance,
    __in  LPSTR lpCmdLine,
    __in  int nCmdShow )
{
    UNREFERENCED_PARAMETER(hPrevInstance); 
    UNREFERENCED_PARAMETER(lpCmdLine);
    UNREFERENCED_PARAMETER(nCmdShow);

    DialogBox(hInstance, MAKEINTRESOURCE(IDD_EMGAIN_DIALOG), NULL, EMGainDialogProcedure);
    
    return 0;        
}
////////////////////////////////////////////////////////////////////////////////
// Disable Controls (Button and Temperature Edit)
////////////////////////////////////////////////////////////////////////////////
void DisableControls()
{	
    EnableWindow(GetDlgItem(dialog_, IDC_CALIBRATE), false);
    EnableWindow(GetDlgItem(dialog_, IDC_TARGET_TEMP_EDIT), false);
}
////////////////////////////////////////////////////////////////////////////////
// Enable Controls (Button and Temperature Edit)
////////////////////////////////////////////////////////////////////////////////
void EnableControls()
{	
    EnableWindow(GetDlgItem(dialog_, IDC_CALIBRATE), true);
    EnableWindow(GetDlgItem(dialog_, IDC_TARGET_TEMP_EDIT), true);
}
////////////////////////////////////////////////////////////////////////////////
// If some error has occurred we can not continue show the error 
// and disable the dialog.
////////////////////////////////////////////////////////////////////////////////
bool CheckPicamIsValid(PicamError errCode)
{    
    if (errCode != PicamError_None) 
    {                
        WCHAR errorBuffer[512];
        
        // Get the error string, the called function allocates the memory 
        const pichar *errString;
        Picam_GetEnumerationString(PicamEnumeratedType_Error, errCode, &errString);
        
        // Convert picam narrow string to a wide one
        MultiByteToWideChar(CP_ACP, 0, errString, -1, errorBuffer, 512);

        // Since the called function allocated the memory it must free it 
        Picam_DestroyString(errString);

        SetDlgItemText(dialog_, IDC_STATIC_MSG, errorBuffer);                        

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

    // Locking Section
    InitializeCriticalSection(&lock_);

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
                SetDlgItemText(dialog_, IDC_STATIC_MSG, L"No Camera Found");
                            
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
                    // Progress Bar
                    SendDlgItemMessage(dialog_, IDC_PROGRESS,PBM_SETRANGE, 0, 1000 << 16);		

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
        WCHAR buffer[32];	
        swprintf(buffer, 32, L"%.f", temp);
        SetDlgItemText(dialog_, IDC_TARGET_TEMP_EDIT, buffer);

        // Get the Constraints
        const PicamRangeConstraint *tempConstraint;
        errCode = PicamEMCalibration_GetSensorTemperatureSetPointConstraint(calibration_, &tempConstraint);

        // Update UI if no error
        if (errCode == PicamError_None)
        {
            WCHAR tempRange[64];	
            swprintf(tempRange, 64, L"Temperature (%.f to %.f)", tempConstraint->minimum, tempConstraint->maximum);
            SetDlgItemText(dialog_, IDC_STATIC_TG, tempRange);
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
        WCHAR buffer[32];	
        swprintf(buffer, 32, L"%02d/%02d/%04d", date.month, date.day, date.year);
        SetDlgItemText(dialog_, ID_LAST_DATE_TEXT, buffer);
    }
    // If the parameter does not exist we can continue since it simply means that
    // this device has never been calibrated
    else if (errCode == PicamError_ParameterDoesNotExist)
    {                
        SetDlgItemText(dialog_, ID_LAST_DATE_TEXT, L"N/A");
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
        WCHAR buffer[32];
        swprintf(buffer, 32, L"%.f", currentTemp);
        SetDlgItemText(dialog_, IDC_CURRENT_TEMP_TEXT, buffer);
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
pibln PIL_CALL CalibrationCallback(PicamHandle calibration, 
                                   piflt progress, 
                                   void* user_state)
{
    UNREFERENCED_PARAMETER( calibration );	
    UNREFERENCED_PARAMETER( user_state );	
    
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
DWORD __stdcall CalibrationThread(void*)
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
        Sleep(1000);

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
    WCHAR buffer[32];
    GetDlgItemText(dialog_, IDC_TARGET_TEMP_EDIT, buffer, 32);

    // Convert the temperature string into a double string
    wchar_t* endPtr;
    piflt temperature = wcstod(buffer, &endPtr);
    if (*endPtr != 0) 
    {
        SetDlgItemText(dialog_, IDC_STATIC_MSG, L"Temperature Must Be A Number");                
        return;
    }

    // Set the temperature from the control
    if (!SetTemperature(temperature))
        return;

    // Begin the thread
    AutoLock al(lock_);
    calibrating_ = true;    
    al.Release();   
    SetDlgItemText(dialog_, IDC_CALIBRATE, L"Abort");		     
    calibrationThread_ = CreateThread(0, 0, CalibrationThread, NULL, 0, 0);
}
////////////////////////////////////////////////////////////////////////////////
void EndCalibration()
{
    AutoLock al(lock_);    
    calibrating_ = false;                
}
////////////////////////////////////////////////////////////////////////////////
// EMGainDialogProcedure
// - Handle the Gain Dialog
////////////////////////////////////////////////////////////////////////////////
INT_PTR CALLBACK EMGainDialogProcedure(
    HWND hwndDlg,
    UINT uMsg,
    WPARAM wParam,
    LPARAM lParam)
{    
    UNREFERENCED_PARAMETER(lParam);

    switch( uMsg )
    {
        ///////////////////////////////////////////////////////////////////////
        case WM_CALIBRATIONSTATE:
            switch (wParam)
            {
                case WaitingForTemperatureStability:
                {
                    // Serialize picam calls
                    AutoLock al(lock_);
                    bool status = UpdateCurrentTemperature();
                    al.Release();
                    if (status)
                        SetDlgItemText(dialog_, IDC_STATIC_MSG, L"Waiting For Temperature");
                    else
                    {
                        SetDlgItemText(dialog_, IDC_STATIC_MSG, L"Failed Reading Temperature");
                        EndCalibration();            
                    }
                    break;
                }
                case TemperatureLockError:
                    SetDlgItemText(dialog_, IDC_STATIC_MSG, L"Failed Checking Temperature Lock");
                    break;
                case PerformingCalibration:
                    SetDlgItemText(dialog_, IDC_CURRENT_TEMP_TEXT, L"Locked");
                    SetDlgItemText(dialog_, IDC_STATIC_MSG, L"Performing Calibration");
                    break;
                case SuccessfullCalibration:
                    SetDlgItemText(dialog_, IDC_STATIC_MSG, L"Calibration Successful");
                    UpdateCalibrationDate();
                    break;
                case CancelledCalibration:
                    SetDlgItemText(dialog_, IDC_STATIC_MSG, L"Calibration Cancelled");
                    break;
                case FailedCalibration:
                    SetDlgItemText(dialog_, IDC_STATIC_MSG, L"Calibration Failed");
                    break;
            }
            if ((wParam != WaitingForTemperatureStability) && (wParam != PerformingCalibration))
            {
                // Close the handle
                CloseHandle(calibrationThread_);

                // Set the handle to NULL
                calibrationThread_ = NULL;

                // Restore the button and progress to zero
                SetDlgItemText(dialog_, IDC_CALIBRATE, L"Calibrate");		
                SendDlgItemMessage(dialog_, IDC_PROGRESS, PBM_SETPOS, 0, 0);
            }
            break;        
         ///////////////////////////////////////////////////////////////////////
        case WM_CALIBRATIONPROGRESS:
            SendDlgItemMessage(dialog_, IDC_PROGRESS, PBM_SETPOS, wParam, 0);
            break;
        ///////////////////////////////////////////////////////////////////////
        case WM_INITDIALOG: 
            // Cache the handle of the dialog to a global
            dialog_ = hwndDlg;
            InitializeForGain();
            break;
        ///////////////////////////////////////////////////////////////////////
        case WM_CLOSE:
            wParam = IDOK;            
        ///////////////////////////////////////////////////////////////////////
        case WM_COMMAND:
            switch (LOWORD(wParam))
            {
                ///////////////////////////////////////////////////////////////
                case IDC_CALIBRATE:                   
                    // If we are already in a calibration
                    if (calibrationThread_)
                    {
                        // This provides instant status that cancelling has begun
                        SetDlgItemText(dialog_, IDC_STATIC_MSG, L"Cancelling Calibration");                
                        EndCalibration();
                    }
                    // Otherwise start a calibration
                    else
                        BeginCalibration();                    						
                    break;               

                ///////////////////////////////////////////////////////////////
                case IDOK:                                   
                    // Handle the Exiting Case while a calibration is running
                    if (calibrationThread_)
                    {            
                        ShowWindow(dialog_, SW_HIDE);
                        EndCalibration();
                        if (WaitForSingleObject(calibrationThread_, INFINITE) == WAIT_OBJECT_0)
                            CloseHandle(calibrationThread_);
                    }

                    UninitializeForGain();
                    EndDialog(hwndDlg, IDOK);
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
