PROTO_DIR=proto
GO_OUT=src
PY_OUT=vector_cache/pb
PROTO_FILE=$(PROTO_DIR)/vector-cache.proto


run_go:
	go run cmd/main.go
	
pb_go:
	protoc --go_out=$(GO_OUT) --go-grpc_out=$(GO_OUT) --proto_path=$(PROTO_DIR) $(PROTO_FILE)

pb_python:
	- mkdir -p $(PY_OUT)
	- python -m grpc_tools.protoc -I$(PROTO_DIR) --python_out=$(PY_OUT) --mypy_out=$(PY_OUT) --grpc_python_out=$(PY_OUT) $(PROTO_FILE)
	- find vector_cache/pb -type f -name "*.py" -exec sed -i '' 's/^import vector_cache_pb2/from vector_cache.pb import vector_cache_pb2/' {} +
	- touch vector_cache/pb/__init__.py

bin_go:
	- mkdir -p vector_cache/bin
	- GOOS=linux GOARCH=amd64 go build -o vector_cache/bin/db_server_linux_amd64 ./cmd/main.go
	- GOOS=darwin GOARCH=amd64 go build -o vector_cache/bin/db_server_darwin_amd64 ./cmd/main.go
	- GOOS=windows GOARCH=amd64 go build -o vector_cache/bin/db_server_windows_amd64.exe ./cmd/main.go

test_go:
	go test