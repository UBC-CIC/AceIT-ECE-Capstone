# Define the AWS region and layer package name
REGION := us-west-2
PACKAGE_NAME := lambda_layer_dependencies

# Define the versions of the dependencies
PYMUPDF_VERSION := 1.25.1   # Replace with the desired PyMuPDF version
PYTHON_DOCX_VERSION := 0.8.11 # Replace with the desired python-docx version

.PHONY: build clean # deploy

# Build the Lambda Layer in a Docker container
build:
	# Run the build process inside an Amazon Linux 2 container
	docker run --rm -v $(shell pwd):/var/task -w /var/task amazonlinux:2 \
	bash -c "\
		yum install -y python3 python3-pip zip && \
		pip3 install PyMuPDF==$(PYMUPDF_VERSION) python-docx==$(PYTHON_DOCX_VERSION) -t python && \
		zip -r $(PACKAGE_NAME).zip python \
	"

# Clean up the build directory and zip file
clean:
	rm -rf python $(PACKAGE_NAME).zip

# Deploy the Lambda Layer to AWS
# deploy: build
# 	# Publish the layer to AWS Lambda
# 	aws lambda publish-layer-version \
# 		--layer-name $(PACKAGE_NAME) \
# 		--description "Lambda layer with PyMuPDF and python-docx dependencies" \
# 		--license-info "MIT" \
# 		--compatible-runtimes python3.9 python3.8 python3.7 \
# 		--zip-file fileb://$(PACKAGE_NAME).zip \
# 		--region $(REGION)

# Default target (build)
# all: build
