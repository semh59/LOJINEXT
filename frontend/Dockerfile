# Frontend Dockerfile - Multi-stage Build
# ============================================================
# Stage 1: Build
FROM node:18-alpine AS build-stage

WORKDIR /app

# Accept build-time API URL
ARG VITE_API_URL=/api/v1
ENV VITE_API_URL=${VITE_API_URL}

# Copy package files
COPY package*.json ./

# Install dependencies
RUN npm ci --no-audit --no-fund 2>/dev/null || npm install

# Copy source code
COPY . .

# Build the application
RUN npm run build

# ============================================================
# Stage 2: Serve with Nginx
FROM nginx:stable-alpine AS production-stage

# Copy custom nginx config
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Copy build artifacts from stage 1
COPY --from=build-stage /app/dist /usr/share/nginx/html

# Expose port 80
EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
