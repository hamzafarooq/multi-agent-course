FROM node:20-slim

WORKDIR /app

COPY package.json package-lock.json ./
RUN npm ci --omit=dev

COPY . .
COPY translation-widget.js /widget/translation-widget.js

EXPOSE 8787

CMD ["node", "server.js"]
