# Rutx-AI-services

## Overview
This application combines a LiveKit agents service with voice agent to help with the visit details, and a outbound call agent to promote the new product launched and an agent to check the retailer availability in the shop to make a visit or not, and also has a FastAPI backend for high-performance AI services.

## Architecture
- **LiveKit Agent**: Visit agent, Product-Promotional call agent and Retailer-availabilty call agent each runs as seperate docker container and connects to Livekit.
- **FastAPI Backend**: Handles HTTP requests with optimized performance

## Running the Application

### Combined Mode (Both Agent and API)
``` 
### Build and run
docker-compose up --build

### Run
docker-compose up -d     

```

