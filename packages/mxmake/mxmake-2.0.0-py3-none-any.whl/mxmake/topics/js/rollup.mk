#:[rollup]
#:title = Rollup JavaScript module bundler
#:description = Create JavaScript bundles with rollup.
#:depends = js.nodejs
#:
#:[target.rollup]
#:description = Run rollup JavaScript bundler.
#:
#:[setting.ROLLUP_CONFIG]
#:description = Rollup config file.
#:default = rollup.conf.js

##############################################################################
# rollup
##############################################################################

NODEJS_DEV_PACKAGES+=\
	rollup \
	rollup-plugin-cleanup \
	@rollup/plugin-terser

.PHONY: rollup
rollup: $(NODEJS_TARGET)
	@rollup --config $(ROLLUP_CONFIG)
