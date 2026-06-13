# Cloud Storage + Database Integration

## Project Overview
This project demonstrates a cloud-based file storage system using AWS services.

Users can:
- Upload files to Amazon S3
- Store file metadata in DynamoDB
- Retrieve uploaded files using API Gateway and Lambda
- View uploaded files through a web interface

## AWS Services Used

- Amazon S3
- AWS Lambda
- Amazon API Gateway
- Amazon DynamoDB

## Architecture

Frontend → API Gateway → Lambda → S3 + DynamoDB

## Features

- File Upload
- Metadata Storage
- File Listing
- Serverless Architecture
- REST API Integration

## Project Structure

frontend/
├── index.html
├── style.css
└── app.js

lambda/
├── save_metadata.py
└── get_files.py


## Screenshots

Screenshots are available in the screenshots folder.

## Author

Manikanta Naripeddi
