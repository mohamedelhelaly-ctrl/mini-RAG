# mini-RAG

## Requirements
- python 3.8 or later

## Installation
- Create virtual env: 
```bash 
$ python3 -m venv .venv
$ source .venv/bin/activate
```
- Install requirements.txt: 
```bash 
$ pip install -r requirements.txt
```

## Setup Environment Variables
- copy .env.example to create .env file
```bash
$ cp .env.example .env
```
- Set environment variables in .env file using .env.example as a template


# Run Docker Compose Services
```bash
$ cd docker
$ cp .env.example .env
```
- update .env with your credentials

## Run FastAPI Server
```bash
$ cd src
$ uvicorn main:app --reload --host 0.0.0.0 --port 8000
```
