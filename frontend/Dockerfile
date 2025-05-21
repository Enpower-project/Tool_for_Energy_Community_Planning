FROM node:20-alpine AS builder
WORKDIR /app
RUN npm install -g @compodoc/compodoc
COPY . .
## Disable anonymous telemetry data about general usage.
ENV NEXT_TELEMETRY_DISABLED 1
RUN npm install
RUN npm run build --prod -- --base-href='./'
RUN compodoc -p tsconfig.base.json -d documentation

FROM nginx:alpine AS runner
WORKDIR /app
COPY --from=builder /app/dist/enpower/browser /usr/share/nginx/html
ARG PUBLISH_COMPODOC
ENV PUBLISH_COMPODOC=${PUBLISH_COMPODOC}
COPY --from=builder /app/documentation /usr/share/nginx/html/documentation
RUN if [ "$PUBLISH_COMPODOC" = "false" ]; then rm -rf /usr/share/nginx/html/documentation; fi

EXPOSE 80