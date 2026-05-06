# -------- Stage 1: Build React --------
FROM node:20-alpine as build

WORKDIR /app

COPY Frontend/package*.json ./
RUN npm install

COPY Frontend/ ./
RUN npm run build

# -------- Stage 2: Nginx --------
FROM nginx:alpine

# Copy nginx config
COPY nginx/default.conf /etc/nginx/conf.d/default.conf
COPY nginx/proxy_params /etc/nginx/proxy_params

# Copy React build into nginx
COPY --from=build /app/build /usr/share/nginx/html