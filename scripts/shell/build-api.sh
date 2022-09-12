VERBOSE=$1
if [ $VERBOSE = "true" ]; then 
    echo "------------------------------------------------------------------------"; 
    echo "Creating serverless code build"; 
    echo "------------------------------------------------------------------------"; 
    python scripts/python/create_serverless_code.py; 
    echo "------------------------------------------------------------------------"; 
    echo "Showing build directory structure (Taking into account .gcloudignore)"; 
    echo "------------------------------------------------------------------------"; 
    # Creates csv string of all files that will be uploaded when deploying the 
    # google cloud function (taking into account .gcloud ignore). 
    build_upload_files_csv=$(
        gcloud meta list-files-for-upload "${PATH_SERVERLESS_CODE_DEPLOY}" \
            | xargs \
            | sed -e 's/ /,/g'
    )
    # Shows the directory structure of the build bundle, filtering out files 
    # that are skipped in .gcloudignore 
    echo $PATH_SERVERLESS_CODE_DEPLOY
    python scripts/python/tree.py \
        --path-dir $PATH_SERVERLESS_CODE_DEPLOY \
        --paths-show "${build_upload_files_csv}"
else 
    python scripts/python/create_serverless_code.py --quiet 
fi