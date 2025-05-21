## Aplicación en Firefox

Para el buen funcionamiento de la aplicación en el navegador firefox el keycloak y la aplicación front deberás de estar publicados en una dirección https debido a que firefox bloquea las cookies de terceros que no sean seguras. Esto provoca que si no está publicado en https la aplicación se recargue infinitamente.

## Levantar servicio en local

1. Rellenear el fichero environment.ts. (Revisar el apartado de Variables para conocer los valores recomendados).
2. Instalar librerias con el comando: `npm i`
3. Arrancar servicio: `ng serve`

## Desplegar servicio en Docker

1. Renombrar fichero .env-prod por .env y rellenar las variables. (Revisar el apartado de Variables para conocer los valores recomendados).
2. Rellenar las variables que se encuentran en el fichero docker-compose.yml.
3. Desplegar aplicación con el comando `docker-compose up -d --build`

## Variables

* DOCKER_IMAGE_FRONT: nombre de la imagen del docker de la APP.
* DOCKER_CONTAINER_FRONT: nombre del contener docker de la APP.
* API_PORT_FRONT: puerto por defecto que utilizará la aplicación front.
