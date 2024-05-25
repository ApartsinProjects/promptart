registry_url=388342378766.dkr.ecr.us-east-1.amazonaws.com
repository_url="$registry_url/sqs-events-handler"

sudo systemctl start docker
docker login -u AWS -p "$(aws ecr get-login-password --region us-east-1)" 388342378766.dkr.ecr.us-east-1.amazonaws.com
docker pull $repository_url
docker run -it --rm --name -e ENV PA_SQS_NAME=promptart-dev -e AWS_DEFAULT_REGION=us-east-1 sqs-reader-run $repository_url