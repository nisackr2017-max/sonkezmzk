FROM python:3.13-slim

WORKDIR /app

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    DENO_INSTALL="/root/.deno" \
    PATH="/root/.deno/bin:/usr/local/bin:${PATH}" \
    npm_config_update_notifier=false

COPY requirements.txt .

# ffmpeg + Node 22 + Deno + canvas (bgutil) çalışma kütüphaneleri
RUN apt-get update -y \
    && apt-get install -y --no-install-recommends \
        ffmpeg curl ca-certificates xz-utils unzip git \
        build-essential python3 pkg-config \
        libcairo2-dev libpango1.0-dev libjpeg-dev libgif-dev librsvg2-dev \
        libcairo2 libpango-1.0-0 libpangocairo-1.0-0 libjpeg62-turbo libgif7 librsvg2-2 \
    && NODE_DIST=$(curl -fsSL https://nodejs.org/dist/latest-v22.x/SHASUMS256.txt | awk '/linux-x64.tar.xz$/ {print $2; exit}') \
    && curl -fsSL "https://nodejs.org/dist/latest-v22.x/${NODE_DIST}" | tar -xJ -C /usr/local --strip-components=1 \
    && curl -fsSL https://deno.land/install.sh | sh \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# PO Token sağlayıcısı — token'ları otomatik üretir, cookie gerekmez
RUN git clone --single-branch --branch 2.0.2 --depth 1 \
        https://github.com/Brainicism/bgutil-ytdlp-pot-provider.git /root/bgutil-ytdlp-pot-provider \
    && cd /root/bgutil-ytdlp-pot-provider/server \
    && npm ci && npx tsc

RUN pip3 install -U pip && pip3 install -U -r requirements.txt

COPY . .
RUN sed -i 's/\r$//' start && chmod +x start

EXPOSE 8080

CMD ["bash", "start"]
