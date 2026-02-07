FROM mmcauliffe/montreal-forced-aligner:latest

# -----------------------------
# Environment variables
# -----------------------------
# Where MFA stores models/config
ENV MFA_ROOT_DIR=/mfa

# Prevent Python buffering
ENV PYTHONUNBUFFERED=1

# -----------------------------
# System setup
# -----------------------------
USER root

# Install FastAPI + Uvicorn inside the existing conda env
# (The MFA image already has conda + python)
RUN conda install -y -c conda-forge \
    fastapi \
    uvicorn \
    python-multipart \
 && conda clean -afy

# Create directories
RUN mkdir -p /app /data /mfa

# -----------------------------
# App setup
# -----------------------------
WORKDIR /app

# Copy your FastAPI app
# (expects aligner/main.py)
COPY . /app

# -----------------------------
# Runtime
# -----------------------------
EXPOSE 8000

# Default command: run FastAPI
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
