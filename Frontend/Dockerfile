# ---------- 1) Build ----------
FROM node:20-alpine AS build

WORKDIR /app

# nur Dependency-Files zuerst (Cache!)
COPY package*.json ./
RUN npm install

# restlicher Code
COPY . .
RUN npm run build


# ---------- 2) Serve ----------
FROM nginx:alpine

# Standard nginx config löschen
RUN rm /etc/nginx/conf.d/default.conf

# eigene Config
COPY nginx.conf /etc/nginx/conf.d/default.conf

# gebaute Dateien kopieren
COPY --from=build /app/dist /usr/share/nginx/html

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]

