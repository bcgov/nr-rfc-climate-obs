# Recover Deleted Files From Object Storage

The `RFC Data` object store bucket has versioning enabled on it.  This allows
any files that accidentally get delete to be recovered.  This doc describes the
process that was used to recover all the files in a directory that were accidentally
deleted.

# Recovery

See the script `scripts/python/s3recover.py`.  In a nutshell in the script you can specify
either the directory or a file that you want to recover, and then run the script.