# --- Base stage ---
FROM node:20-slim AS base
WORKDIR /app

# --- Development stage ---
FROM base AS dev
COPY apps/frontend/package.json apps/frontend/package-lock.json* ./
RUN npm install
# The source code will be mounted as a volume in docker-compose.yml
# Expose Vite's default port
EXPOSE 5173
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0", "--port", "5173"]

# --- Build stage ---
FROM base AS builder
COPY apps/frontend/package.json apps/frontend/package-lock.json* ./
RUN npm install
COPY apps/frontend/ .
RUN npm run build

# --- Production stage ---
FROM nginx:alpine AS prod
COPY --from=builder /app/dist /usr/share/nginx/html
# SPA fallback
RUN echo 'server { \
    listen 80; \
    location / { \
        root /usr/share/nginx/html; \
        index index.html; \
        try_files $uri $uri/ /index.html; \
    } \
}' > /etc/nginx/conf.d/default.conf
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
