# Superset with Arc JSON dialect pre-installed
FROM apache/superset:latest

USER root

# Fix venv permissions so superset user can install packages
RUN chown -R superset:superset /app/.venv

USER superset

# Install pip into the venv
RUN /app/.venv/bin/python -m ensurepip --upgrade

# Install Arc Superset JSON dialect into the venv
RUN /app/.venv/bin/python -m pip install --no-cache-dir arc-superset-dialect

# Use Superset's default initialization
CMD ["/app/docker/docker-bootstrap.sh", "app-gunicorn"]