# PharmaLink: setup tutorial


## How to setup and start the containers
**Important** - you need Docker Desktop installed

1. Clone this repository.  
1. Ensure the file named `db_root_password.txt` in the `secrets/` folder has the password: pharmalink 
1. Ensure the file named `db_password.txt` in the `secrets/` folder has the password: pharmalink 
1. In a terminal or command prompt, navigate to the folder with the `docker-compose.yml` file / root directory.
1. Build the images with `docker compose build`
1. Start the containers with `docker compose up`.  To run in detached mode, run `docker compose up -d`.





