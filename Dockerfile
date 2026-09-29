# FILP Platform — container image, built for Hugging Face Spaces (Docker SDK).
#
# Everything the app needs to run a federated ILP simulation (Flower
# server + clients, Popper, Andante, clingo) lives inside this single
# image: the simulation itself is multiple *local* subprocesses talking
# over localhost sockets, not separate machines, so one container is
# enough — no multi-container orchestration required for the app to work.
#
# Local test:  docker compose up --build   (then open http://localhost:7860)
# HF Spaces:   push this repo to a Space with sdk: docker in README.md —
#              Spaces builds this same Dockerfile automatically.

FROM python:3.11-slim

# --- System dependencies -------------------------------------------------
# swi-prolog: pyswip talks to it via ctypes (libswipl) — Popper's engine
#   depends on this at *runtime*, not just at pip-install time.
# build-essential: some pinned deps (e.g. clingo's C extension) may need
#   to compile from source depending on the platform's available wheels.
# git: a couple of pip deps in requirements-lock.txt are pulled from VCS.
RUN apt-get update && apt-get install -y --no-install-recommends \
    swi-prolog \
    build-essential \
    git \
    curl \
    && rm -rf /var/lib/apt/lists/*

# --- Hugging Face Spaces runs every container as UID 1000 ------------------
# Files owned by root (the default) are unreadable/unwritable for that user,
# so create "user" and do every COPY/RUN below as them, into their own home
# directory, per HF's documented pattern for Docker Spaces.
RUN useradd -m -u 1000 user
USER user
ENV HOME=/home/user \
    PATH=/home/user/.local/bin:$PATH

WORKDIR $HOME/app

# --- Python dependencies ---------------------------------------------------
# Copy requirements first so this layer is cached across rebuilds that
# only touch application code.
COPY --chown=user requirements.txt ./
COPY --chown=user symbolic ./symbolic

RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt \
    # requirements.txt only lists `symbolic/andante` as an editable
    # install; Popper (symbolic/popper-core) needs the same treatment or
    # `import popper` fails at runtime.
    && pip install --no-cache-dir -e ./symbolic/popper-core

# --- Application code -------------------------------------------------------
COPY --chown=user . .

# Local absolute paths from the author's own machine — see config/paths.yaml.
# Nothing in the running app currently calls EngineManager (core/engine_manager.py)
# with these, but ship a container-relative version anyway so the file is not
# actively wrong if that ever changes.
RUN mkdir -p data artifacts \
    && printf 'engines:\n  collaboration: %s/app/engines/collaboration\n  coordination: %s/app/engines/coordination\n' "$HOME" "$HOME" > config/paths.yaml

RUN python initialize_db.py

# Hugging Face Spaces routes public traffic to this port by default
# (set via app_port in README.md's YAML block if you ever change it).
EXPOSE 7860

HEALTHCHECK --interval=30s --timeout=5s --start-period=20s \
    CMD curl -f http://localhost:7860/_stcore/health || exit 1

ENTRYPOINT ["streamlit", "run", "apps/Home.py", \
            "--server.port=7860", "--server.address=0.0.0.0", \
            "--server.headless=true"]
