import { Injectable } from '@angular/core';
import { KeycloakService } from 'keycloak-angular';

@Injectable({
  providedIn: 'root'
})
export class KeycloakToolsService {

  constructor(private readonly keycloak: KeycloakService,) { }


  public async getUserUID() {

    if (this.keycloak.isLoggedIn()) {
      const token = await this.keycloak.getToken();
      const parsedToken = this.parseJwt(token);
      const uid = parsedToken.sub;

      return uid;
    }

    return null

  }

  public parseJwt(token: string) {
    const base64Url = token.split('.')[1];
    const base64 = base64Url.replace(/-/g, '+').replace(/_/g, '/');
    const jsonPayload = decodeURIComponent(
      atob(base64)
        .split('')
        .map(function (c) {
          return '%' + ('00' + c.charCodeAt(0).toString(16)).slice(-2);
        })
        .join('')
    );
    return JSON.parse(jsonPayload);
  }

}
