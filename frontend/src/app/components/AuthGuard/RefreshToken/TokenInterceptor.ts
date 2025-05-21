import { Injectable } from '@angular/core';
import { HttpInterceptor, HttpRequest, HttpHandler, HttpEvent } from '@angular/common/http';
import { Observable, from } from 'rxjs';
import { switchMap, catchError } from 'rxjs/operators';
import { KeycloakService } from 'keycloak-angular';

@Injectable()
export class TokenInterceptor implements HttpInterceptor {

  constructor(private keycloak: KeycloakService) {}

  intercept(request: HttpRequest<any>, next: HttpHandler): Observable<HttpEvent<any>> {
    if (this.shouldUpdateToken(request)) {
      return from(this.keycloak.updateToken(5)).pipe(
        switchMap(() => {
          const token = this.keycloak.getKeycloakInstance().token;
          const authReq = request.clone({
            setHeaders: {
              Authorization: `Bearer ${token}`
            }
          });
          return next.handle(authReq);
        }),
        catchError(error => {
          console.error('Error updating token in interceptor', error);
          throw error; 
        })
      );
    } else {
      return next.handle(request);
    }
  }

  shouldUpdateToken(request: HttpRequest<any>): boolean {
    const tokenUpdateHeader = request.headers.get('token-update');
    if (tokenUpdateHeader && tokenUpdateHeader.toLowerCase() === 'true') {
      return false;
    }
    const tokenExpirationDate = this.keycloak?.getKeycloakInstance()?.tokenParsed?.exp;
    const currentTime = new Date().getTime() / 1000;
    const timeUntilExpiration = tokenExpirationDate ?? 0 - currentTime;
    return timeUntilExpiration <= 300;
  }
}