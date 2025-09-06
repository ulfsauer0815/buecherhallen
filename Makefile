OUT = output
ASSETS = src/ui/assets


.PHONY: all
all: assets


.PHONY: clean
clean:
	rm -f $(OUT)/favicon*.svg
	rm -f $(OUT)/favicon*.png
	rm -f $(OUT)/apple-touch-icon.png
	rm -f $(OUT)/*.html


.PHONY: assets
assets: favicons


.PHONY: favicons
favicons: $(patsubst $(ASSETS)/%,$(OUT)/%,$(wildcard $(ASSETS)/favicon*)) $(OUT)/apple-touch-icon.png


$(OUT)/apple-touch-icon.png: $(ASSETS)/favicon-512x512.png
	cp $< $@


$(OUT)/favicon%: $(ASSETS)/favicon%
	cp $< $@
