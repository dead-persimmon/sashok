from os import environ as environment

open(environment['OPENSHIFT_REPO_DIR'] + 'crawler-test.log', 'a').close()