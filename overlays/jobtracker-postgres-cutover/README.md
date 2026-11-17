# Production PostgreSQL configuration

Production runs this overlay with the restricted runtime Secret and verified PostgreSQL CA.
The migration owner Secret is not injected into the web app. The JSON PVC is retained
for rollback; PostgreSQL mode ignores it.

The final frozen backup contains 144 jobs; all imported records reconciled and the
repeat import inserted zero duplicates. After PostgreSQL accepts new writes, a rollback
to JSON requires exporting/reconciling those writes before restarting the JSON app.
