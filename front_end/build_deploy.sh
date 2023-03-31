#az login
#az acr login --name regprotocolsfds
export COMMIT_ID=`git show -s --format=%ci_%h | sed s/[^_a-z0-9]//g | sed s/0[012]00_/_/g`
docker build -t harmony --build-arg COMMIT_ID=$COMMIT_ID .
docker tag harmony regprotocolsfds.azurecr.io/harmony:$COMMIT_ID
docker push regprotocolsfds.azurecr.io/harmony:$COMMIT_ID
echo "The container version is $COMMIT_ID"
