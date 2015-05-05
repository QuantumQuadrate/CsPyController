/******************************************************************************/
/******************************************************************************/
/******************************************************************************/
/******************************************************************************/
/* picam_advanced.h - Princeton Instruments Advanced Camera Control API       */
/******************************************************************************/
/******************************************************************************/
/******************************************************************************/
/******************************************************************************/
#if !defined PICAM_ADVANCED_H
#define PICAM_ADVANCED_H

#include "picam.h"

/******************************************************************************/
/* C++ Prologue                                                               */
/******************************************************************************/
#if defined __cplusplus && !defined PICAM_EXPORTS
    extern "C"
    {
#endif

/******************************************************************************/
/******************************************************************************/
/******************************************************************************/
/******************************************************************************/
/* Plug 'n Play Discovery, Camera Information and Access                      */
/******************************************************************************/
/******************************************************************************/
/******************************************************************************/
/******************************************************************************/

/*----------------------------------------------------------------------------*/
/* Camera Plug 'n Play Discovery ---------------------------------------------*/
/*----------------------------------------------------------------------------*/
typedef enum PicamDiscoveryAction
{
    PicamDiscoveryAction_Found = 1,
    PicamDiscoveryAction_Lost  = 2
} PicamDiscoveryAction; /* (3) */
/*----------------------------------------------------------------------------*/
typedef PicamError (PIL_CALL* PicamDiscoveryCallback)(
    const PicamCameraID* id,
    PicamHandle          device,
    PicamDiscoveryAction action );
/*----------------------------------------------------------------------------*/
PICAM_API PicamAdvanced_RegisterForDiscovery( PicamDiscoveryCallback discover );
/*----------------------------------------------------------------------------*/
PICAM_API PicamAdvanced_UnregisterForDiscovery(
    PicamDiscoveryCallback discover );
/*----------------------------------------------------------------------------*/
PICAM_API PicamAdvanced_DiscoverCameras( void );
/*----------------------------------------------------------------------------*/
PICAM_API PicamAdvanced_StopDiscoveringCameras( void );
/*----------------------------------------------------------------------------*/
PICAM_API PicamAdvanced_IsDiscoveringCameras( pibln* discovering );
/*----------------------------------------------------------------------------*/
/* Camera Access -------------------------------------------------------------*/
/*----------------------------------------------------------------------------*/
PICAM_API PicamAdvanced_OpenCameraDevice(
    const PicamCameraID* id,
    PicamHandle*         device );
/*----------------------------------------------------------------------------*/
PICAM_API PicamAdvanced_CloseCameraDevice( PicamHandle device );
/*----------------------------------------------------------------------------*/
PICAM_API PicamAdvanced_GetOpenCameraDevices(
    const PicamHandle** device_array,
    piint*              device_count ); /* ALLOCATES */
/*----------------------------------------------------------------------------*/
PICAM_API PicamAdvanced_GetCameraModel(
    PicamHandle  camera,
    PicamHandle* model );
/*----------------------------------------------------------------------------*/
PICAM_API PicamAdvanced_GetCameraDevice(
    PicamHandle  camera,
    PicamHandle* device );
/*----------------------------------------------------------------------------*/
typedef enum PicamHandleType
{
    PicamHandleType_CameraDevice = 1,
    PicamHandleType_CameraModel  = 2
} PicamHandleType; /* (3) */
/*----------------------------------------------------------------------------*/
PICAM_API PicamAdvanced_GetHandleType(
    PicamHandle      camera,
    PicamHandleType* type );
/*----------------------------------------------------------------------------*/
/* Camera Information - User State -------------------------------------------*/
/*----------------------------------------------------------------------------*/
PICAM_API PicamAdvanced_GetUserState( PicamHandle camera, void** user_state );
/*----------------------------------------------------------------------------*/
PICAM_API PicamAdvanced_SetUserState( PicamHandle camera, void* user_state );
/*----------------------------------------------------------------------------*/
/* Camera Information - Pixel Defects ----------------------------------------*/
/*----------------------------------------------------------------------------*/
typedef struct PicamPixelLocation
{
    pi16s x;
    pi16s y;
} PicamPixelLocation;
/*----------------------------------------------------------------------------*/
typedef struct PicamColumnDefect
{
    PicamPixelLocation start;
    piint height;
} PicamColumnDefect;
/*----------------------------------------------------------------------------*/
typedef struct PicamRowDefect
{
    PicamPixelLocation start;
    piint width;
} PicamRowDefect;
/*----------------------------------------------------------------------------*/
typedef struct PicamPixelDefectMap
{
    const PicamColumnDefect* column_defect_array;
    piint column_defect_count;
    const PicamRowDefect* row_defect_array;
    piint row_defect_count;
    const PicamPixelLocation* point_defect_array;
    piint point_defect_count;
} PicamPixelDefectMap;
/*----------------------------------------------------------------------------*/
PICAM_API PicamAdvanced_DestroyPixelDefectMaps(
    const PicamPixelDefectMap* pixel_defect_map_array );
/*----------------------------------------------------------------------------*/
PICAM_API PicamAdvanced_GetPixelDefectMap(
    PicamHandle                 camera,
    const PicamPixelDefectMap** pixel_defect_map ); /* ALLOCATES */
/*----------------------------------------------------------------------------*/

/******************************************************************************/
/******************************************************************************/
/******************************************************************************/
/******************************************************************************/
/* Camera Parameter Values, Information, Constraints and Commitment           */
/******************************************************************************/
/******************************************************************************/
/******************************************************************************/
/******************************************************************************/

/*----------------------------------------------------------------------------*/
/* Camera Parameters ---------------------------------------------------------*/
/*----------------------------------------------------------------------------*/
/* Camera Parameter Values - Integer -----------------------------------------*/
/*----------------------------------------------------------------------------*/
typedef PicamError (PIL_CALL* PicamIntegerValueChangedCallback)(
    PicamHandle    camera,
    PicamParameter parameter,
    piint          value );
/*----------------------------------------------------------------------------*/
PICAM_API PicamAdvanced_RegisterForIntegerValueChanged(
    PicamHandle                      camera,
    PicamParameter                   parameter,
    PicamIntegerValueChangedCallback changed );
/*----------------------------------------------------------------------------*/
PICAM_API PicamAdvanced_UnregisterForIntegerValueChanged(
    PicamHandle                      camera,
    PicamParameter                   parameter,
    PicamIntegerValueChangedCallback changed );
/*----------------------------------------------------------------------------*/
/* Camera Parameter Values - Large Integer -----------------------------------*/
/*----------------------------------------------------------------------------*/
typedef PicamError (PIL_CALL* PicamLargeIntegerValueChangedCallback)(
    PicamHandle    camera,
    PicamParameter parameter,
    pi64s          value );
/*----------------------------------------------------------------------------*/
PICAM_API PicamAdvanced_RegisterForLargeIntegerValueChanged(
    PicamHandle                           camera,
    PicamParameter                        parameter,
    PicamLargeIntegerValueChangedCallback changed );
/*----------------------------------------------------------------------------*/
PICAM_API PicamAdvanced_UnregisterForLargeIntegerValueChanged(
    PicamHandle                           camera,
    PicamParameter                        parameter,
    PicamLargeIntegerValueChangedCallback changed );
/*----------------------------------------------------------------------------*/
/* Camera Parameter Values - Floating Point ----------------------------------*/
/*----------------------------------------------------------------------------*/
typedef PicamError (PIL_CALL* PicamFloatingPointValueChangedCallback)(
    PicamHandle    camera,
    PicamParameter parameter,
    piflt          value );
/*----------------------------------------------------------------------------*/
PICAM_API PicamAdvanced_RegisterForFloatingPointValueChanged(
    PicamHandle                            camera,
    PicamParameter                         parameter,
    PicamFloatingPointValueChangedCallback changed );
/*----------------------------------------------------------------------------*/
PICAM_API PicamAdvanced_UnregisterForFloatingPointValueChanged(
    PicamHandle                            camera,
    PicamParameter                         parameter,
    PicamFloatingPointValueChangedCallback changed );
/*----------------------------------------------------------------------------*/
/* Camera Parameter Values - Regions of Interest -----------------------------*/
/*----------------------------------------------------------------------------*/
typedef PicamError (PIL_CALL* PicamRoisValueChangedCallback)(
    PicamHandle      camera,
    PicamParameter   parameter,
    const PicamRois* value );
/*----------------------------------------------------------------------------*/
PICAM_API PicamAdvanced_RegisterForRoisValueChanged(
    PicamHandle                   camera,
    PicamParameter                parameter,
    PicamRoisValueChangedCallback changed );
/*----------------------------------------------------------------------------*/
PICAM_API PicamAdvanced_UnregisterForRoisValueChanged(
    PicamHandle                   camera,
    PicamParameter                parameter,
    PicamRoisValueChangedCallback changed );
/*----------------------------------------------------------------------------*/
/* Camera Parameter Values - Pulse -------------------------------------------*/
/*----------------------------------------------------------------------------*/
typedef PicamError (PIL_CALL* PicamPulseValueChangedCallback)(
    PicamHandle       camera,
    PicamParameter    parameter,
    const PicamPulse* value );
/*----------------------------------------------------------------------------*/
PICAM_API PicamAdvanced_RegisterForPulseValueChanged(
    PicamHandle                    camera,
    PicamParameter                 parameter,
    PicamPulseValueChangedCallback changed );
/*----------------------------------------------------------------------------*/
PICAM_API PicamAdvanced_UnregisterForPulseValueChanged(
    PicamHandle                    camera,
    PicamParameter                 parameter,
    PicamPulseValueChangedCallback changed );
/*----------------------------------------------------------------------------*/
/* Camera Parameter Values - Custom Intensifier Modulation Sequence ----------*/
/*----------------------------------------------------------------------------*/
typedef PicamError (PIL_CALL* PicamModulationsValueChangedCallback)(
    PicamHandle             camera,
    PicamParameter          parameter,
    const PicamModulations* value );
/*----------------------------------------------------------------------------*/
PICAM_API PicamAdvanced_RegisterForModulationsValueChanged(
    PicamHandle                          camera,
    PicamParameter                       parameter,
    PicamModulationsValueChangedCallback changed );
/*----------------------------------------------------------------------------*/
PICAM_API PicamAdvanced_UnregisterForModulationsValueChanged(
    PicamHandle                          camera,
    PicamParameter                       parameter,
    PicamModulationsValueChangedCallback changed );
/*----------------------------------------------------------------------------*/
/* Camera Parameter Information - Relevance ----------------------------------*/
/*----------------------------------------------------------------------------*/
typedef PicamError (PIL_CALL* PicamIsRelevantChangedCallback)(
    PicamHandle    camera,
    PicamParameter parameter,
    pibln          relevant );
/*----------------------------------------------------------------------------*/
PICAM_API PicamAdvanced_RegisterForIsRelevantChanged(
    PicamHandle                    camera,
    PicamParameter                 parameter,
    PicamIsRelevantChangedCallback changed );
/*----------------------------------------------------------------------------*/
PICAM_API PicamAdvanced_UnregisterForIsRelevantChanged(
    PicamHandle                    camera,
    PicamParameter                 parameter,
    PicamIsRelevantChangedCallback changed );
/*----------------------------------------------------------------------------*/
/* Camera Parameter Information - Value Access -------------------------------*/
/*----------------------------------------------------------------------------*/
typedef PicamError (PIL_CALL* PicamValueAccessChangedCallback)(
    PicamHandle      camera,
    PicamParameter   parameter,
    PicamValueAccess access );
/*----------------------------------------------------------------------------*/
PICAM_API PicamAdvanced_RegisterForValueAccessChanged(
    PicamHandle                     camera,
    PicamParameter                  parameter,
    PicamValueAccessChangedCallback changed );
/*----------------------------------------------------------------------------*/
PICAM_API PicamAdvanced_UnregisterForValueAccessChanged(
    PicamHandle                     camera,
    PicamParameter                  parameter,
    PicamValueAccessChangedCallback changed );
/*----------------------------------------------------------------------------*/
/* Camera Parameter Information - Dynamics -----------------------------------*/
/*----------------------------------------------------------------------------*/
typedef enum PicamDynamicsMask
{
    PicamDynamicsMask_None        = 0x0,
    PicamDynamicsMask_Value       = 0x1,
    PicamDynamicsMask_ValueAccess = 0x2,
    PicamDynamicsMask_IsRelevant  = 0x4,
    PicamDynamicsMask_Constraint  = 0x8
} PicamDynamicsMask; /* (0x10) */
/*----------------------------------------------------------------------------*/
PICAM_API PicamAdvanced_GetParameterDynamics(
    PicamHandle        camera,
    PicamParameter     parameter,
    PicamDynamicsMask* dynamics );
/*----------------------------------------------------------------------------*/
/* Camera Parameter Constraints - Collection ---------------------------------*/
/*----------------------------------------------------------------------------*/
PICAM_API PicamAdvanced_GetParameterCollectionConstraints(
    PicamHandle                       camera,
    PicamParameter                    parameter,
    const PicamCollectionConstraint** constraint_array,
    piint*                            constraint_count ); /* ALLOCATES */
/*----------------------------------------------------------------------------*/
typedef PicamError (PIL_CALL*PicamDependentCollectionConstraintChangedCallback)(
    PicamHandle                      camera,
    PicamParameter                   parameter,
    const PicamCollectionConstraint* constraint );
/*----------------------------------------------------------------------------*/
PICAM_API PicamAdvanced_RegisterForDependentCollectionConstraintChanged(
    PicamHandle                                       camera,
    PicamParameter                                    parameter,
    PicamDependentCollectionConstraintChangedCallback changed );
/*----------------------------------------------------------------------------*/
PICAM_API PicamAdvanced_UnregisterForDependentCollectionConstraintChanged(
    PicamHandle                                       camera,
    PicamParameter                                    parameter,
    PicamDependentCollectionConstraintChangedCallback changed );
/*----------------------------------------------------------------------------*/
/* Camera Parameter Constraints - Range --------------------------------------*/
/*----------------------------------------------------------------------------*/
PICAM_API PicamAdvanced_GetParameterRangeConstraints(
    PicamHandle                  camera,
    PicamParameter               parameter,
    const PicamRangeConstraint** constraint_array,
    piint*                       constraint_count ); /* ALLOCATES */
/*----------------------------------------------------------------------------*/
typedef PicamError (PIL_CALL*PicamDependentRangeConstraintChangedCallback)(
    PicamHandle                 camera,
    PicamParameter              parameter,
    const PicamRangeConstraint* constraint );
/*----------------------------------------------------------------------------*/
PICAM_API PicamAdvanced_RegisterForDependentRangeConstraintChanged(
    PicamHandle                                  camera,
    PicamParameter                               parameter,
    PicamDependentRangeConstraintChangedCallback changed );
/*----------------------------------------------------------------------------*/
PICAM_API PicamAdvanced_UnregisterForDependentRangeConstraintChanged(
    PicamHandle                                  camera,
    PicamParameter                               parameter,
    PicamDependentRangeConstraintChangedCallback changed );
/*----------------------------------------------------------------------------*/
/* Camera Parameter Constraints - Regions Of Interest ------------------------*/
/*----------------------------------------------------------------------------*/
PICAM_API PicamAdvanced_GetParameterRoisConstraints(
    PicamHandle                 camera,
    PicamParameter              parameter,
    const PicamRoisConstraint** constraint_array,
    piint*                      constraint_count ); /* ALLOCATES */
/*----------------------------------------------------------------------------*/
typedef PicamError (PIL_CALL* PicamDependentRoisConstraintChangedCallback)(
    PicamHandle                camera,
    PicamParameter             parameter,
    const PicamRoisConstraint* constraint );
/*----------------------------------------------------------------------------*/
PICAM_API PicamAdvanced_RegisterForDependentRoisConstraintChanged(
    PicamHandle                                 camera,
    PicamParameter                              parameter,
    PicamDependentRoisConstraintChangedCallback changed );
/*----------------------------------------------------------------------------*/
PICAM_API PicamAdvanced_UnregisterForDependentRoisConstraintChanged(
    PicamHandle                                 camera,
    PicamParameter                              parameter,
    PicamDependentRoisConstraintChangedCallback changed );
/*----------------------------------------------------------------------------*/
/* Camera Parameter Constraints - Pulse --------------------------------------*/
/*----------------------------------------------------------------------------*/
PICAM_API PicamAdvanced_GetParameterPulseConstraints(
    PicamHandle                  camera,
    PicamParameter               parameter,
    const PicamPulseConstraint** constraint_array,
    piint*                       constraint_count ); /* ALLOCATES */
/*----------------------------------------------------------------------------*/
typedef PicamError (PIL_CALL* PicamDependentPulseConstraintChangedCallback)(
    PicamHandle                 camera,
    PicamParameter              parameter,
    const PicamPulseConstraint* constraint );
/*----------------------------------------------------------------------------*/
PICAM_API PicamAdvanced_RegisterForDependentPulseConstraintChanged(
    PicamHandle                                  camera,
    PicamParameter                               parameter,
    PicamDependentPulseConstraintChangedCallback changed );
/*----------------------------------------------------------------------------*/
PICAM_API PicamAdvanced_UnregisterForDependentPulseConstraintChanged(
    PicamHandle                                  camera,
    PicamParameter                               parameter,
    PicamDependentPulseConstraintChangedCallback changed );
/*----------------------------------------------------------------------------*/
/* Camera Parameter Constraints - Custom Intensifier Modulation Sequence -----*/
/*----------------------------------------------------------------------------*/
PICAM_API PicamAdvanced_GetParameterModulationsConstraints(
    PicamHandle                        camera,
    PicamParameter                     parameter,
    const PicamModulationsConstraint** constraint_array,
    piint*                             constraint_count ); /* ALLOCATES */
/*----------------------------------------------------------------------------*/
typedef PicamError (PIL_CALL* PicamDependentModulationsConstraintChangedCallback)(
    PicamHandle                       camera,
    PicamParameter                    parameter,
    const PicamModulationsConstraint* constraint );
/*----------------------------------------------------------------------------*/
PICAM_API PicamAdvanced_RegisterForDependentModulationsConstraintChanged(
    PicamHandle                                        camera,
    PicamParameter                                     parameter,
    PicamDependentModulationsConstraintChangedCallback changed );
/*----------------------------------------------------------------------------*/
PICAM_API PicamAdvanced_UnregisterForDependentModulationsConstraintChanged(
    PicamHandle                                        camera,
    PicamParameter                                     parameter,
    PicamDependentModulationsConstraintChangedCallback changed );
/*----------------------------------------------------------------------------*/
/* Camera Commitment ---------------------------------------------------------*/
/*----------------------------------------------------------------------------*/
/* Parameter Validation ------------------------------------------------------*/
/*----------------------------------------------------------------------------*/
typedef struct PicamValidationResult
{
    pibln                       is_valid;
    const PicamParameter*       failed_parameter;
    const PicamConstraintScope* failed_error_constraint_scope;
    const PicamConstraintScope* failed_warning_constraint_scope;
    const PicamParameter*       error_constraining_parameter_array;
    piint                       error_constraining_parameter_count;
    const PicamParameter*       warning_constraining_parameter_array;
    piint                       warning_constraining_parameter_count;
} PicamValidationResult;
/*----------------------------------------------------------------------------*/
PICAM_API Picam_DestroyValidationResult(
    const PicamValidationResult* result );
/*----------------------------------------------------------------------------*/
typedef struct PicamValidationResults
{
    pibln                        is_valid;
    const PicamValidationResult* validation_result_array;
    piint                        validation_result_count;
} PicamValidationResults;
/*----------------------------------------------------------------------------*/
PICAM_API Picam_DestroyValidationResults(
    const PicamValidationResults* results );
/*----------------------------------------------------------------------------*/
PICAM_API PicamAdvanced_ValidateParameter(
    PicamHandle                   model,
    PicamParameter                parameter,
    const PicamValidationResult** result ); /* ALLOCATES */
/*----------------------------------------------------------------------------*/
PICAM_API PicamAdvanced_ValidateParameters(
    PicamHandle                    model,
    const PicamValidationResults** results ); /* ALLOCATES */
/*----------------------------------------------------------------------------*/
/* Dependent Parameter Validation --------------------------------------------*/
/*----------------------------------------------------------------------------*/
typedef struct PicamFailedDependentParameter
{
    PicamParameter              failed_parameter;
    const PicamConstraintScope* failed_error_constraint_scope;
    const PicamConstraintScope* failed_warning_constraint_scope;
} PicamFailedDependentParameter;
/*----------------------------------------------------------------------------*/
typedef struct PicamDependentValidationResult
{
    pibln                                is_valid;
    PicamParameter                       constraining_parameter;
    const PicamFailedDependentParameter* failed_dependent_parameter_array;
    piint                                failed_dependent_parameter_count;
} PicamDependentValidationResult;
/*----------------------------------------------------------------------------*/
PICAM_API Picam_DestroyDependentValidationResult(
    const PicamDependentValidationResult* result );
/*----------------------------------------------------------------------------*/
PICAM_API PicamAdvanced_ValidateDependentParameter(
    PicamHandle                            model,
    PicamParameter                         parameter,
    const PicamDependentValidationResult** result ); /* ALLOCATES */
/*----------------------------------------------------------------------------*/
/* Parameter Commitment ------------------------------------------------------*/
/*----------------------------------------------------------------------------*/
PICAM_API PicamAdvanced_CommitParametersToCameraDevice( PicamHandle model );
/*----------------------------------------------------------------------------*/
PICAM_API PicamAdvanced_RefreshParameterFromCameraDevice(
    PicamHandle    model,
    PicamParameter parameter );
/*----------------------------------------------------------------------------*/
PICAM_API PicamAdvanced_RefreshParametersFromCameraDevice(
    PicamHandle model );
/*----------------------------------------------------------------------------*/

/******************************************************************************/
/******************************************************************************/
/******************************************************************************/
/******************************************************************************/
/* Camera Data Acquisition                                                    */
/******************************************************************************/
/******************************************************************************/
/******************************************************************************/
/******************************************************************************/

/*----------------------------------------------------------------------------*/
/* Acquisition Setup - Buffer ------------------------------------------------*/
/*----------------------------------------------------------------------------*/
typedef struct PicamAcquisitionBuffer
{
    void* memory;
    pi64s memory_size;
} PicamAcquisitionBuffer;
/*----------------------------------------------------------------------------*/
PICAM_API PicamAdvanced_GetAcquisitionBuffer(
    PicamHandle             device,
    PicamAcquisitionBuffer* buffer );
/*----------------------------------------------------------------------------*/
PICAM_API PicamAdvanced_SetAcquisitionBuffer(
    PicamHandle                   device,
    const PicamAcquisitionBuffer* buffer );
/*----------------------------------------------------------------------------*/
/* Acquisition Setup - Notification ------------------------------------------*/
/*----------------------------------------------------------------------------*/
typedef PicamError (PIL_CALL* PicamAcquisitionUpdatedCallback)(
    PicamHandle                   device,
    const PicamAvailableData*     available,
    const PicamAcquisitionStatus* status );
/*----------------------------------------------------------------------------*/
PICAM_API PicamAdvanced_RegisterForAcquisitionUpdated(
    PicamHandle                     device,
    PicamAcquisitionUpdatedCallback updated );
/*----------------------------------------------------------------------------*/
PICAM_API PicamAdvanced_UnregisterForAcquisitionUpdated(
    PicamHandle                     device,
    PicamAcquisitionUpdatedCallback updated );
/*----------------------------------------------------------------------------*/
/* Acquisition Control -------------------------------------------------------*/
/*----------------------------------------------------------------------------*/
PICAM_API PicamAdvanced_HasAcquisitionBufferOverrun(
    PicamHandle device,
    pibln*      overran );
/*----------------------------------------------------------------------------*/
PICAM_API PicamAdvanced_ClearReadoutCountOnline(
    PicamHandle device,
    pibln*      cleared );
/*----------------------------------------------------------------------------*/

/******************************************************************************/
/* C++ Epilogue                                                               */
/******************************************************************************/
#if defined __cplusplus && !defined PICAM_EXPORTS
    }   /* end extern "C" */
#endif

#endif
