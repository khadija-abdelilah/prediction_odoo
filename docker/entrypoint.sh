#!/bin/bash
# Run server in detached mode
# In $TEST = 1 (test_mode) mode

ADMIN_PWD=${ADMIN_PWD:-admin}
DB_NAME=${DB_NAME:-odoo}
# ------- Set server_wide_modules -------
SERVER_WIDE_MODULES=${SERVER_WIDE_MODULES:-web,base}
TEST_SERVER_WIDE_MODULES="$SERVER_WIDE_MODULES"
CFG_FILE=${CFG_FILE:-config/odoo.conf}
ODOO_CMD=${ODOO_CMD:-python3 server/odoo-bin -c $CFG_FILE}

# TEST_TAGS: Automatically generate a comma-separated list of modules to test.
# removes duplicates, sorts them, and joins them into a comma-separated string.

TEST_TAGS=${TEST_TAGS:-$(find . -name 'Prediction_*' | cut -d '/' -f 3 | sort | uniq  | tr -s '\n' ',')}

if [ $TEST_MODULES ]; then
  INSTALL_TEST_MODULES="-i $TEST_MODULES"
fi


echo "-----> Starting server"
if [ $TEST = 1 ]; then
  echo "-----> Install server in test mode with command: $ODOO_CMD --stop-after-init  --load=$SERVER_WIDE_MODULES $INSTALL_TEST_MODULES"
  $ODOO_CMD --max-cron-threads=0 --stop-after-init --load=$SERVER_WIDE_MODULES $INSTALL_TEST_MODULES
else
  $ODOO_CMD
fi



# Run Tests
if [ $TEST = 1 ]; then
  rm -rf odoo_tests/*
  mkdir -p odoo_tests

  coverage run --rcfile=config/.coveragerc server/odoo-bin -c config/odoo-test.conf --test-tags "$TEST_TAGS" --max-cron-threads=0 --stop-after-init

  # Generate coverage reports
  echo "Generating coverage reports..."
  TOTAL_COVERAGE=$(coverage report --rcfile=config/.coveragerc --format=total)
  echo "Code coverage: ${TOTAL_COVERAGE} %"
  coverage html --rcfile=config/.coveragerc -d odoo_tests/htmlcov && coverage xml --rcfile=config/.coveragerc -o odoo_tests/coverage.xml
  # Search and replace "<function" with "function" in .xml files to fix junit-viewer bad format
  for file in odoo_tests/*.xml; do
    sed -i 's/<function/function/g' "$file"
  done
  # Check for test failures and errors
  for file in odoo_tests/*.xml; do grep -q '<failure\|<error' "$file" && { echo "Error in $file" >&2; exit 1; }; done; echo "0 error in test reports." >&2; exit 0
fi


exit 0
