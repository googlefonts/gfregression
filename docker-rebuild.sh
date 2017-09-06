docker-compose stop
docker rm $(docker ps -a -q)
docker rmi $(docker images -q)
# docker-compose -f production.yml up
