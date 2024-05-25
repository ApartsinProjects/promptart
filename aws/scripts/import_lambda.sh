#!/bin/bash

unix_code() {
    cd $2
    zip -j ../../updated_lambda_code.zip *
    cd ../..
    zip -ur updated_lambda_code.zip core
    zip -ur updated_lambda_code.zip utils
    aws lambda update-function-code --function-name $1 --zip-file fileb://updated_lambda_code.zip --region us-east-1 --no-cli-pager
    rm -rf updated_lambda_code.zip
    # cd $2
    # zip -r9 updated_lambda_code.zip .
    # aws lambda update-function-code --function-name $1 --zip-file fileb://updated_lambda_code.zip --region us-east-1 --no-cli-pager
    # rm -rf updated_lambda_code.zip
}
wnd_code() {
    tar -C $2 -a -c -f updated_lambda_code.zip *
    aws lambda update-function-code --function-name $1 --zip-file fileb://updated_lambda_code.zip --region us-east-1 --no-cli-pager
    del /f updated_lambda_code.zip
}

# Detect the operating system
OS=$(uname -s)

# Execute different code based on the operating system
if [[ "$OS" == "Darwin"* ||  "$OS" == "Linux"* ]]; then
    unix_code $1 $2
elif [[ "$OS" == "MINGW"* || "$OS" == "MSYS"* ]]; then
    wnd_code $1 $2
else
    echo "Unsupported operating system: $OS"
    exit 1
fi


