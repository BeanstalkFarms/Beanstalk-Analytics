# If the STORAGE_EMULATOR_PORT environment variable, we ensure that there is 
# a corresponding process running on this port. The user should start this process
# up in it's own terminal window to monitor the logs of the emulator, rather 
# than having it run as a part of this script. 
if [[ $STORAGE_EMULATOR_PORT ]]; then 
    PORT_SCAN_CMD="lsof -i :${STORAGE_EMULATOR_PORT}";
    PORT_SCAN_OUTPUT=$(eval $PORT_SCAN_CMD); 
    PORT_SCAN_STATUS=$?
    if [[ $PORT_SCAN_STATUS -eq 0 ]]; then 
        echo "Located process running on emulator port ${STORAGE_EMULATOR_PORT}"
    else 
        echo "------------------------------------------------------------------------"
        echo "Warning"
        echo "------------------------------------------------------------------------"
        echo "If you see an error above this warning, running command '${PORT_SCAN_CMD}' failed" 
        echo "This is likely due to \$STORAGE_EMULATOR_PORT having an invalid value.\n" 
        echo "If you don't see an error above this warning, then the command executed successfully"
        echo "but there was no process listening on the expected port ${STORAGE_EMULATOR_PORT}"
        echo "Make sure that you start the emulator within it's own terminal window before running "
        echo "this command. This will allow you to monitor the logs of the storage emulator."
        exit 1 
    fi
else 
    # TODO: In this case, ensure that the storage emulator host is NOT running on the target port 
    echo "Environment variable STORAGE_EMULATOR_PORT unset, using GCP storage bucket backend."
fi

# The serverless code bundle is always generated prior to running this script. 
# And given that either: 
# 1. STORAGE_EMULATOR_PORT is set and the emulator is running. 
# 2. STORAGE_EMULATOR_PORT is not set, so we are connecting to GCP storage bucket. 
# We can now safely start the local api testing infra. 
echo "------------------------------------------------------------------------"
echo "Launching api in dev mode from ${PATH_SERVERLESS_CODE_DEPLOY}" 
echo "------------------------------------------------------------------------"
cd "${PATH_SERVERLESS_CODE_DEPLOY}"; \
    functions-framework --target=bean_analytics_recalculate_chart
