# Frontend Dockerfile for React app
FROM node:18-alpine AS build

WORKDIR /app

# Enable Corepack for Yarn
RUN corepack enable && corepack prepare yarn@stable --activate

# Copy package files
COPY webfront/package.json webfront/yarn.lock* ./

# Install dependencies
RUN yarn install --frozen-lockfile

# Copy application code
COPY webfront/ .

# Build the React app
RUN yarn build

# Production stage with nginx
FROM nginx:alpine

# Copy custom nginx config
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Copy built app from build stage
COPY --from=build /app/build /usr/share/nginx/html

# Expose port 80
EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
