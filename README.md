# gcp-services-poc Project

Proof of concept aiming to use the following Google Services:

* [ ] Secret Manager (google just added ability to inject secrets as env variables!)
* [ ] Cloud Storage
* [ ] Speech to Text
* [ ] Automated deploys to Cloud Run using Google GitHub Actions

## Completed Steps

* Created a project and added a Cloud Storage bucket manually
* Created basic FastAPI project
* Added endpoints with python Cloud Storage library to list and upload blobs using "spooled" file type
* Created new GHA workflow with [setup-gcloud](https://github.com/google-github-actions/setup-gcloud)
and [deploy-cloudrun](https://github.com/google-github-actions/deploy-cloudrun)
* Manually created and exported a JSON service account key
* Added GCP_PROJECT_ID, GCP_SERVICE, GCP_REGION, and GCP_SA_KEY as secrets
* Changed service port from 8080 (default) to 8000
* Enabled public access by granting the allUsers member the Cloud Run Invoker role
* Added Speech to Text library
* Enabled Speech to Text API in project

## Pending Steps

* Add [release action](https://github.com/google-github-actions/release-please-action)
* Use [commit convention](https://www.conventionalcommits.org/en/v1.0.0/)
* Make files [public](https://cloud.google.com/storage/docs/access-control/making-data-public)
