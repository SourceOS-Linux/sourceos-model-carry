.PHONY: build test validate dist release-dry-run clean

BIN := sourceos-ai
DIST_DIR := dist
VERSION ?= 0.1.0-dev
COMMIT ?= $(shell git rev-parse --short HEAD 2>/dev/null || echo unknown)
DATE ?= $(shell date -u +%Y-%m-%dT%H:%M:%SZ)
GOOS ?= $(shell go env GOOS 2>/dev/null || uname -s | tr A-Z a-z)
GOARCH ?= $(shell go env GOARCH 2>/dev/null || uname -m)
DIST_NAME := $(BIN)_$(VERSION)_$(GOOS)_$(GOARCH)
LDFLAGS := -X main.version=$(VERSION) -X main.commit=$(COMMIT) -X main.date=$(DATE)

build:
	mkdir -p bin
	go build -ldflags "$(LDFLAGS)" -o bin/$(BIN) ./cmd/sourceos-ai

test:
	go test ./...

validate: build
	python3 tools/validate_carry_refs.py
	bin/$(BIN) carry validate --refs examples
	bin/$(BIN) validate --refs examples
	bin/$(BIN) list --refs examples
	bin/$(BIN) doctor --refs examples
	bin/$(BIN) self-test --refs examples
	bin/$(BIN) emit-evidence --refs examples >/tmp/sourceos-ai-evidence.json

dist: validate
	mkdir -p $(DIST_DIR)
	cp bin/$(BIN) $(DIST_DIR)/$(DIST_NAME)
	(cd $(DIST_DIR) && sha256sum $(DIST_NAME) > $(DIST_NAME).sha256)

release-dry-run: dist
	@echo "release dry-run complete: $(DIST_DIR)/$(DIST_NAME)"

clean:
	rm -rf bin $(DIST_DIR)
