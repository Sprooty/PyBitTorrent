#!/bin/bash

# Expected IP address
EXPECTED_IP="70.34.211.206"

# Fetch the current external IP address using ifconfig.me
CURRENT_IP=$(curl -s curl v4.i-p.show)

# Compare the current IP with the expected IP
if [ "$CURRENT_IP" = "$EXPECTED_IP" ]; then
    echo "IP check passed: External IP matches expected IP ($EXPECTED_IP)"
else
    echo "IP check failed: External IP ($CURRENT_IP) does not match expected IP ($EXPECTED_IP)"
    exit 1
fi