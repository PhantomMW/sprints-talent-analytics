FROM nginx:alpine

LABEL org.opencontainers.image.title="Sprints Talent Analytics"
LABEL org.opencontainers.image.description="Interactive talent analytics dashboard"
LABEL org.opencontainers.image.source="https://github.com/PhantomMW/sprints-talent-analytics"

COPY dashboard/index.html /usr/share/nginx/html/index.html

EXPOSE 80
