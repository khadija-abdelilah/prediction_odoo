ARG BASE_IMAGE_REF=
FROM registry.smile.fr/bs_devops/env_odoo:18.0_bookworm


ARG TEST=0
ENV TEST=$TEST
ARG TEST_MODULES=
ENV TEST_MODULES=$TEST_MODULES
ENV PIP_BREAK_SYSTEM_PACKAGES=true

# Set Python path so Odoo can locate packages
ENV PYTHONPATH="/home/odoo/.local/lib/python3.11/site-packages:/usr/local/lib/python3.11/dist-packages:/usr/lib/python3/dist-packages:$PYTHONPATH"

USER root

# Install OS-level dependencies
RUN apt -y update && apt -y install \
    gettext-base \
    ipython3 \
    postgresql-client \
    python3-pip \
    python3-dev \
    build-essential \
    libatlas-base-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Python packages from requirements
COPY ./requirements.txt /tmp/requirements.txt
RUN pip3 install --upgrade pip && \
    pip3 install --no-cache-dir -r /tmp/requirements.txt

# Optionally install testing requirements
COPY ./requirements-tests.txt /tmp/requirements-tests.txt
RUN if [ "$TEST" = "1" ]; then \
    pip3 install -r /tmp/requirements-tests.txt; \
fi

# Ensure user local directory exists and is writable
RUN mkdir -p /home/odoo/.local && \
    chown -R odoo:odoo /home/odoo/.local

# Copy application code
COPY --chown=odoo:odoo . .

# Setup file storage directory
RUN pip3 install --break-system-packages --no-cache-dir \
    joblib \
    scikit-learn \
    numpy==1.26.4 \
    lightgbm \
    scipy \
    threadpoolctl \
    pandas

RUN pip3 install debugpy --break-system-packages

# Final setup
USER odoo
ENTRYPOINT ["/bin/bash", "entrypoint.sh"]
