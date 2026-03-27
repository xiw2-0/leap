poetry build

scp dist/*.whl x@139.196.19.116:/home/x/
scp .env x@139.196.19.116:/home/x/
scp ./deploy/deploy.sh x@139.196.19.116:/home/x/