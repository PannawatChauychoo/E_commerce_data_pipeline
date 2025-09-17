#!/bin/bash

#Creating the database
python3 /Users/macos/Personal_projects/Portfolio/Project_1_Walmart/Walmart_sim/backend/database/load_to_postgres.py


connect=false

# Parse options
while getopts ":c" opt; do
  case $opt in
    c)
      connect=true
      ;;
    \?)
      echo "Invalid option: -$OPTARG" >&2
      exit 1
      ;;
  esac
done

#Entering the databse
if [ "$connect" = true ]; then
    echo "Connecting to the database..."
    psql -h 100.97.140.87 -U Pan -d ecommerce_cloud
fi