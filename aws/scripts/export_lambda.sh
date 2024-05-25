#!/bin/bash

unix_code() {
    cd $2
    rm -rf *
    aws lambda get-function --function-name $1 --query 'Code.Location' --output text --region us-east-1 | xargs curl -o exported_lambda_code.zip
    
    unzip -o exported_lambda_code.zip -d . #aws/lambdas/main
    if [ -d "utils" ]; then
        rm -rf ../../utils
        mv -f utils ../..
    fi
    if [ -d "core" ]; then
        rm -rf ../../core
        mv -f core ../..
    fi
    rm -rf exported_lambda_code.zip 

    # aws lambda get-function --function-name $1 --query 'Code.Location' --output text --region us-east-1 | xargs curl -o exported_lambda_code.zip
    # rm -rf $2
    # unzip exported_lambda_code.zip -d $2 #aws/lambdas/main
    # rm -rf exported_lambda_code.zip 
}
wnd_code() {
    aws lambda get-function --function-name $1 --query 'Code.Location' --output text --region us-east-1 | xargs curl -o exported_lambda_code.zip
    del /S $2 /q /s
    tar -xvf exported_lambda_code.zip -C $2
    del /f exported_lambda_code.zip 
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

#unzip -o exported_lambda_code.zip -d ./aws 