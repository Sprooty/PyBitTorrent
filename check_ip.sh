#!/bin/bash

# Wait for 5 seconds before checking the IP
sleep 10

# Expected IP address
EXPECTED_IP="70.34.211.206"

# Fetch the current external IP address using ifconfig.me
# Wait up to 10 seconds for a response
CURRENT_IP=$(curl -s --max-time 10 v4.i-p.show)

# Compare the current IP with the expected IP
if [ "$CURRENT_IP" = "$EXPECTED_IP" ]; then
    echo "IP check passed: External IP matches expected IP ($EXPECTED_IP)"
else
    echo "IP check failed: External IP ($CURRENT_IP) does not match expected IP ($EXPECTED_IP)"
    exit 1
fi