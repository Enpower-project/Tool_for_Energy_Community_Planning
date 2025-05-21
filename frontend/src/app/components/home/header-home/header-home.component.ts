import { Component, ElementRef, HostListener, Input, OnInit } from '@angular/core';
import { Router } from '@angular/router';
import { KeycloakService } from 'keycloak-angular';
import { APP_ROUTES } from '../../../data/routes';
import { FormGroup, FormBuilder, Validators } from '@angular/forms';
import { TranslateService } from '@ngx-translate/core';
import { KeycloakProfile } from 'keycloak-js';
import { NavigateService } from '../../../services/navigate.service';
import { EXTERNAL_ROUTES } from '../../../data/externalRoutes';

@Component({
  selector: 'app-header',
  templateUrl: './header-home.component.html',
  styleUrls: ['./header-home.component.scss']
})
export class HeaderHomeComponent implements OnInit {

  @Input() homeMode: boolean = false;
  @Input() showLangSelector: boolean = false;

  public langs = [
    {
      name: "LANGUAGE_MENU.ENGLISH",
      value: "en",
      icon: "UnitedKingdom.svg"
    },
    {
      name: "LANGUAGE_MENU.SPANISH",
      value: "es",
      icon: "Spain.svg"
    },
    {
      name: "LANGUAGE_MENU.GERMAN",
      value: "de",
      icon: "Germany.svg"
    },
    {
      name: "LANGUAGE_MENU.ITALIAN",
      value: "it",
      icon: "Italy.svg"
    },
    {
      name: "LANGUAGE_MENU.SWEDISH",
      value: "sv",
      icon: "Sweden.svg"
    },
    {
      name: "LANGUAGE_MENU.BASQUE",
      value: "eu",
      icon: "Basque.svg"
    },
  ]

  public isLoggedIn = false;
  public userProfile: KeycloakProfile | undefined;
  public showBurgerMenu: boolean = false;
  public APP_ROUTES = APP_ROUTES;
  public EXTERNAL_ROUTES = EXTERNAL_ROUTES;
  form: FormGroup = new FormGroup({});

  constructor(
    private readonly keycloak: KeycloakService,
    private formBuilder: FormBuilder,
    private translate: TranslateService,
    private eRef: ElementRef,
    private router: Router,
    private navgigateService: NavigateService
  ) { }

  ngOnInit(): void {
    this.setForm();
    this.isLoggedIn = this.keycloak.isLoggedIn();
    if (this.isLoggedIn) {
      this.keycloak.loadUserProfile().then((profile) => {
        this.userProfile = profile;
      });
    }
  }

  public setForm() {
    this.form = this.formBuilder.group({
      lang: [this.translate.currentLang, Validators.required],
    });
    this.form.controls['lang'].valueChanges.subscribe(() => { this.changeLang() })
  }


  public loginButton() {
    if (!this.isLoggedIn)
      this.login()
    else
      this.logout()
  }

  public login() {
    this.keycloak.login();
  }

  public logout() {
    this.keycloak.logout();
  }

  public register() {
    this.keycloak.register();
  }

  public changePass() {
    this.keycloak.login({
      redirectUri: window.location.href,
      action: 'UPDATE_PASSWORD',
    });
  }

  public changeData() {
    this.keycloak.login({
      redirectUri: window.location.href,
      action: 'UPDATE_PROFILE',
    });
  }

  public externalNavigate(route: string) {
    this.navgigateService.openNewPage(route);
  }

  goTo(route: string) {
    this.router.navigate(['/' + route])
  }

  changeLang() {
    this.translate.use(this.form.controls['lang'].value);
  }

  selectPCLang(lang: string) {
    this.showLangSelector = !this.showLangSelector;
    this.form.controls['lang'].setValue(lang);
  }

  public changeShowBurgerMenu() {
    if (this.showLangSelector === true) {
      this.showLangSelector = false;
    }
    this.showBurgerMenu = !this.showBurgerMenu;
  }

  public changeShowLangSelector(status: boolean) {
    if (this.showBurgerMenu === true && status === true) {
      this.showBurgerMenu = false;
    }
    this.showLangSelector = status;
  }

  @HostListener('document:click', ['$event'])
  public clickFuera(event: any) {
    if (!this.eRef.nativeElement.contains(event.target)) {
      this.showBurgerMenu = false;
      this.showLangSelector = false;
    }
  }

}
