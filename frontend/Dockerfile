# Vue 3 + Vite. Em dev, o Vite serve com hot reload via 'npm run dev'.
FROM node:20-alpine

WORKDIR /app

COPY package*.json ./
RUN npm install

COPY . .

EXPOSE 5173
