cp -r ../../utils .
cp -r ../../core .

registry_url=388342378766.dkr.ecr.us-east-1.amazonaws.com
repository_url="$registry_url/sqs-events-handler"

docker build -t sqs-reader-app .
docker tag sqs-reader-app $repository_url
docker login -u AWS -p "$(aws ecr get-login-password --region us-east-1)" $registry_url
docker push $repository_url

rm -rf ./utils
rm -rf ./core


