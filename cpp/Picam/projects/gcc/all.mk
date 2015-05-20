################################################################################
# Solution-Specific Variables
################################################################################
SOLUTION := all
#-------------------------------------------------------------------------------
SDK_PRJ := acquire advanced configure em_gain_calibration gating kinetics \
           metadata multicam param_info poll rois save_data wait_for_trig
################################################################################

################################################################################
# Debug-Specific Variables
################################################################################
ifdef NDEBUG
    DBG_DIR := release
else
    DBG_DIR := debug
endif
################################################################################

################################################################################
# Standard PI Variables
################################################################################
OUT_DIR := objlin/x86_64/$(DBG_DIR)
################################################################################

.PHONY: all checkdirs checksdk $(SDK_PRJ) clean mostlyclean

all: checkdirs checksdk

checkdirs: $(OUT_DIR)

$(OUT_DIR):
	@mkdir -p $@

checksdk: $(SDK_PRJ)

$(SDK_PRJ):
	@$(MAKE) -f $@.mk


clean: mostlyclean
	@for sdk in $(SDK_PRJ); do \
		$(MAKE) -f $$sdk.mk clean; \
	done

mostlyclean:
	@echo Cleaning $(SOLUTION)
	@rm -f -r $(OUT_DIR)
