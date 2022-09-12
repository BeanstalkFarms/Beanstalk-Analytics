# If the STORAGE_EMULATOR_HOST environment variable, we ensure that there is 
# a corresponding process running on this port. The user should start this process
# up in it's own terminal window to monitor the logs of the emulator, rather 
# than having it run as a part of this script. 
PORT_SCAN_CMD="lsof -i :${STORAGE_EMULATOR_PORT} | grep ${STORAGE_EMULATOR_HOST_NAME}";
PORT_SCAN_OUTPUT=$(eval $PORT_SCAN_CMD); 
PORT_SCAN_STATUS=$?
if [[ $STORAGE_EMULATOR_HOST ]]; then 
    echo "Environment variable STORAGE_EMULATOR_HOST set."
    echo "Attempting to use local backend ${STORAGE_EMULATOR_HOST}"
    if [[ $PORT_SCAN_STATUS -eq 0 ]]; then 
        echo "Located emulator process."
    else 
        echo "\nIf you see an error above this, running command '${PORT_SCAN_CMD}' failed" 
        echo "This is likely due to \$STORAGE_EMULATOR_HOST having an invalid value.\n" 
        echo "If you don't see an error above this, then the command executed successfully "
        echo "but we did not locate a process on the expected host:port combination."
        echo "Make sure that you start the emulator within it's own terminal window before running "
        echo "this command. This will allow you to monitor the logs of the storage emulator."
        exit 1 
    fi
else 
    echo "Environment variable STORAGE_EMULATOR_PORT not set"
    echo "attempting to use GCP backend ${NEXT_PUBLIC_CDN}"
    if [[ $PORT_SCAN_STATUS -eq 0 ]]; then 
        echo "Warning: Found process running at host ${STORAGE_EMULATOR_HOST_NAME} and port ${STORAGE_EMULATOR_PORT}" 
        echo "reserved for storage emulator. This won't impact cause a failure, but you should terminate "
        echo "the emulator process when not in use."
    fi
fi

# The serverless code bundle is always generated prior to running this script. 
# And given that either: 
# 1. STORAGE_EMULATOR_HOST is set and the emulator is running. 
# 2. STORAGE_EMULATOR_HOST is not set, so we are connecting to GCP storage bucket. 
# We can now safely start the local api testing infra. 
echo "------------------------------------------------------------------------"
echo "Launching api in dev mode from ${PATH_SERVERLESS_CODE_DEPLOY}" 
echo "------------------------------------------------------------------------"
cd "${PATH_SERVERLESS_CODE_DEPLOY}"; \
    functions-framework --target="${SERVERLESS_HANDLER}"
