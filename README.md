# Versión custom de Airbyte para Kemok
## Quick start

### Run Airbyte locally

You can run Airbyte locally with Docker. The shell script below will retrieve the requisite docker files from the [platform repository](https://github.com/airbytehq/airbyte-platform) and run docker compose for you.

```bash
git clone --depth 1 https://github.com/airbytehq/airbyte.git
cd airbyte
./run-ab-platform.sh
```

Login to the web app at [http://localhost:8000](http://localhost:8000) by entering the default credentials found in your .env file.

```
BASIC_AUTH_USERNAME=airbyte
BASIC_AUTH_PASSWORD=password
```

Follow web app UI instructions to set up a source, destination, and connection to replicate data. Connections support the most popular sync modes: full refresh, incremental and change data capture for databases.

Read the [Airbyte docs](https://docs.airbyte.com).

### Manage Airbyte configurations with code

You can also programmatically manage sources, destinations, and connections with YAML files, [Octavia CLI](https://github.com/airbytehq/airbyte/tree/master/octavia-cli), and API.

### Deploy Airbyte to production

Deployment options: [Docker](https://docs.airbyte.com/deploying-airbyte/local-deployment), [AWS EC2](https://docs.airbyte.com/deploying-airbyte/on-aws-ec2), [Azure](https://docs.airbyte.com/deploying-airbyte/on-azure-vm-cloud-shell), [GCP](https://docs.airbyte.com/deploying-airbyte/on-gcp-compute-engine), [Kubernetes](https://docs.airbyte.com/deploying-airbyte/on-kubernetes), [Restack](https://docs.airbyte.com/deploying-airbyte/on-restack), [Plural](https://docs.airbyte.com/deploying-airbyte/on-plural), [Oracle Cloud](https://docs.airbyte.com/deploying-airbyte/on-oci-vm), [Digital Ocean](https://docs.airbyte.com/deploying-airbyte/on-digitalocean-droplet)...
