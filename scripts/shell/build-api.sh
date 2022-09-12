# IMPORTANT: Ensure that this command is run from the root project directory 
#           Protects against nuking your filesystem. 
if [[ $(pwd) != $(pwd | grep -o '^.*\/beanstalk-data-playground') ]]; then 
    echo "ERROR: Only run the api build script from the beanstalk-data-playground root directory"
    exit 1 
fi 
# Build code bundle 
if [ $BUILD_API_VERBOSE = "true" ]; then 
    echo "------------------------------------------------------------------------"; 
    echo "Creating serverless code build"; 
    echo "------------------------------------------------------------------------"; 
    python scripts/python/create_serverless_code.py; 
    cp requirements.txt "${PATH_SERVERLESS_CODE_DEPLOY}/requirements.txt"
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
    cp requirements.txt "${PATH_SERVERLESS_CODE_DEPLOY}/requirements.txt"
fi