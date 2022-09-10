if [ $1 = "true" ]; then 
    echo "------------------------------------------------------------------------"; 
    echo "Creating serverless code bundle"; 
    echo "------------------------------------------------------------------------"; 
    python scripts/create_serverless_code.py; 
    echo "------------------------------------------------------------------------"; 
    echo "Showing generated directory structure"; 
    echo "------------------------------------------------------------------------"; 
    python scripts/tree.py --path $PATH_SERVERLESS_CODE_DEPLOY; 
else 
    python scripts/create_serverless_code.py --quiet; 
fi