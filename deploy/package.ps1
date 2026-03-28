poetry build

ssh x@139.196.19.116 'mkdir -p /tmp/leap'
scp dist/*.whl x@139.196.19.116:/tmp/leap/
scp .env x@139.196.19.116:/tmp/leap/
scp ./deploy/deploy.sh x@139.196.19.116:/tmp/leap/