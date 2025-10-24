cd ..
source .env
sudo docker rm ${common_project_name}_postgres
sudo docker run --name ${common_project_name}_postgres -d -p ${sqlalchemy_db_port}:5432 -e POSTGRES_USER=${sqlalchemy_db_user} -e POSTGRES_PASSWORD=${sqlalchemy_db_password} -e POSTGRES_DB=${sqlalchemy_db_database} postgres:16 -c max_connections=100
sudo docker start ${common_project_name}_postgres