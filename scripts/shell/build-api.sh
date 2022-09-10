VERBOSE=$1
if [ $VERBOSE = "true" ]; then 
    echo "------------------------------------------------------------------------"; 
    echo "Creating serverless code bundle"; 
    echo "------------------------------------------------------------------------"; 
    python scripts/python/create_serverless_code.py; 
    echo "------------------------------------------------------------------------"; 
    echo "Showing generated directory structure"; 
    echo "------------------------------------------------------------------------"; 
    python scripts/python/tree.py --path $PATH_SERVERLESS_CODE_DEPLOY; 
else 
    python scripts/python/create_serverless_code.py --quiet; 
fi