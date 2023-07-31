# deployment notes

running the helm chart

create the following env vars:

* OBJ_STORE_BUCKET
* OBJ_STORE_SECRET
* OBJ_STORE_USER
* OBJ_STORE_HOST

```
helm upgrade --install \
--set obj_store.bucket=$OBJ_STORE_BUCKET \
--set obj_store.secret=$OBJ_STORE_SECRET \
--set obj_store.user_id=$OBJ_STORE_USER \
--set obj_store.host=$OBJ_STORE_HOST \
--set fire_data_job.fire_data_mnt_point=/data \
fireweather \
fireweather
```


# test run the job

oc create job --from=cronjob/fire-data-acquisition-job "fire-data-manual-run-$(date +%s)"
