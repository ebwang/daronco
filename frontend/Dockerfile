FROM nginx:alpine

# Copies the static files to the default Nginx folder
COPY index.html /usr/share/nginx/html/
COPY script.js /usr/share/nginx/html/

# Exposes the default web server port
EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
