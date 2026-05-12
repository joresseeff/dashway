# ── Stage 1 : builder ────────────────────────────────────────────────────────
FROM python:3.11-slim AS builder

WORKDIR /app
COPY scr/          ./scr/
COPY assets/       ./assets/
COPY sounds/       ./sounds/
COPY munro.ttf     ./

RUN printf "0\n0\n0\n" > save.txt && \
    pip install --no-cache-dir pygame pyinstaller

# ── Stage 2 : runtime ────────────────────────────────────────────────────────
FROM python:3.11-slim AS runtime

LABEL org.opencontainers.image.title="Dashway"
LABEL org.opencontainers.image.description="Arcade car dodger inspired by the Nokia 3310"
LABEL org.opencontainers.image.source="https://github.com/joresseeff/dashway"
LABEL org.opencontainers.image.licenses="MIT"

RUN apt-get update && apt-get install -y --no-install-recommends \
    libsdl2-2.0-0 \
    libsdl2-mixer-2.0-0 \
    libsdl2-image-2.0-0 \
    libsdl2-ttf-2.0-0 \
    libgl1 \
    xvfb \
  && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir pygame

WORKDIR /app
COPY --from=builder /app ./

ENV SDL_VIDEODRIVER=x11
ENV DISPLAY=:99

CMD ["sh", "-c", "Xvfb :99 -screen 0 500x800x24 & sleep 1 && cd scr && python main.py"]
