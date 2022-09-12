VERBOSE=$1
if [ $VERBOSE = "true" ]; then 
    echo "------------------------------------------------------------------------"; 
    echo "Creating serverless code build"; 
    echo "------------------------------------------------------------------------"; 
    python scripts/python/create_serverless_code.py; 
    echo "------------------------------------------------------------------------"; 
    echo "Showing build directory structure (Taking into account .gcloudignore)"; 
    echo "------------------------------------------------------------------------"; 
    echo $PATH_SERVERLESS_CODE_DEPLOY
    # List of all files that will be uploaded when deploying the cloud function. 
    # Note that this command takes into account the contents of .gcloudignore
    build_upload_files_csv=$(
        gcloud meta list-files-for-upload "${PATH_SERVERLESS_CODE_DEPLOY}" \
            | xargs \
            | sed -e 's/ /,/g'
    )
    python scripts/python/tree.py \
        --path-dir $PATH_SERVERLESS_CODE_DEPLOY \
        --paths-show "${build_upload_files_csv}"
else 
    python scripts/python/create_serverless_code.py --quiet 
fi