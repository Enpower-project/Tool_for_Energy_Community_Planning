import { Component, OnInit } from '@angular/core';
import { SwUpdate } from '@angular/service-worker';
import { TranslateService } from '@ngx-translate/core';
import { KeycloakService } from 'keycloak-angular';
import { KeycloakProfile } from 'keycloak-js';

@Component({
  selector: 'app-root',
  templateUrl: './app.component.html',
  styleUrls: ['./app.component.scss']
})
export class AppComponent implements OnInit {
  title = 'ENPOWER';
  language = 'en';

  public isLoggedIn = false;
  public userProfile: any;

  constructor(
    private translate: TranslateService,
    private readonly keycloak: KeycloakService,
    private swUpdate: SwUpdate
  ) { }

  ngOnInit(): void {
    this.checkVersionPWA();
    this.translate.setDefaultLang(this.language);
    this.translate.use(navigator.language.split('-')[0] ?? this.language);
    // this.translate.use( this.language);
    this.isLoggedIn = this.keycloak.isLoggedIn();
    if (this.isLoggedIn) {
      this.userProfile = this.keycloak.loadUserProfile();
    }
    // else{
    //   this.login();
    // }

  }

  private checkVersionPWA() {
    if (this.swUpdate.isEnabled) {
      this.swUpdate.versionUpdates.subscribe(event => {
        if (event.type === 'VERSION_READY') {
          if (confirm('A new version is available. Do you want to update?')) {
            window.location.reload();
          } else {
            setTimeout(() => {
              this.checkForUpdate();
            }, 360000);// recuerdo cada 5 min que hay una version disponible si hemos dado a cancelar 
          }
        }
      });

      setTimeout(() => {
        this.swUpdate.checkForUpdate();
      }, 720000); // reviso cada 10 min si hay actualizaciones
    }
  }

  private checkForUpdate() {
    this.swUpdate.checkForUpdate().then(value => {
      if (value === true) {
        if (confirm('A new version is available. Do you want to update?')) {
          window.location.reload();
        }
      }
    });
  }

  /**
   * Allows you to log in or log out
   *
   * @public
   */
  public loginButton() {
    if (!this.isLoggedIn)
      this.login()
    else
      this.logout()
  }

  /**
 * Allows you to log in 
 *
 * @public
 */
  public login() {
    this.keycloak.login();
  }

  /**
* Allows you to log out 
*
* @public
*/
  public logout() {
    this.keycloak.logout();
  }

  /**
* Allows you to register
*
* @public
*/
  public register() {
    this.keycloak.register();
  }

  /**
* Allows you to change the password
*
* @public
*/
  public changePass() {
    this.keycloak.login({
      redirectUri: window.location.href,
      action: 'UPDATE_PASSWORD',
    });
  }

  /**
* Allows you to change your user data
*
* @public
*/
  public changeData() {
    this.keycloak.login({
      redirectUri: window.location.href,
      action: 'UPDATE_PROFILE',
    });
  }

  /**
* Allows you to change the app lang
*
* @public
*/
  setLanguage(language: string) {
    this.language = language;
    this.translate.use(language);
  }

}
