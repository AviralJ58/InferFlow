FROM node:20-slim AS builder

WORKDIR /app

COPY apps/frontend/package.json apps/frontend/package-lock.json* ./
RUN npm install

COPY apps/frontend/ .
RUN npm run build

# --- Production stage ---
FROM nginx:alpine

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
