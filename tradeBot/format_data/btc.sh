#!/bin/bash

# Create directory for downloads
mkdir -p btc_data

# Start date: 2023-07
# End date: 2024-09
# Format the dates into an array
declare -a dates=(
    "2023-07" "2023-08" "2023-09" "2023-10" "2023-11" "2023-12"
    "2024-01" "2024-02" "2024-03" "2024-04" "2024-05" "2024-06"
    "2024-07" "2024-08" "2024-09"
)

# Base URL
base_url="https://data.binance.vision/data/futures/um/monthly/klines/BTCUSDT/1h"

# Download each file
for date in "${dates[@]}"; do
    filename="BTCUSDT-1h-${date}.zip"
    url="${base_url}/${filename}"
    
    echo "Downloading ${filename}..."
    wget -P binance_data "${url}"
    
    # Add a small delay to be nice to the server
    sleep 1
done

echo "Download complete! Files are saved in the binance_data directory."
