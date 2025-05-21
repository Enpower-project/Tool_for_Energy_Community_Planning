import { Component, EventEmitter, Input, OnChanges, OnInit, Output, SimpleChanges } from '@angular/core';
import { FormGroup, FormBuilder, Validators } from '@angular/forms';
import { Router } from '@angular/router';
import { TranslateService } from '@ngx-translate/core';
import { KeycloakService } from 'keycloak-angular';
import { KeycloakProfile } from 'keycloak-js';
import { NAV_URL_TYPE, NavigationControl, priNavigationMenu, secNavigationMenu } from '../../../data/types';
import { NavigateService } from '../../../services/navigate.service';
import { APP_ROUTES } from '../../../data/routes';
import { EXTERNAL_ROUTES } from '../../../data/externalRoutes';

@Component({
  selector: 'sidebaritups',
  templateUrl: './sidebar.component.html',
  styleUrls: ['./sidebar.component.scss']
})
export class SidebarComponent implements OnInit, OnChanges {

  @Input() currentStep: number = 0;
  @Input() currentPage: string = "";
  @Input() priNavigationMenu: NavigationControl[] = priNavigationMenu;
  @Input() secNavigationMenu: NavigationControl[] = secNavigationMenu;
  @Output() changeFormStep = new EventEmitter();
  @Output() changesecNavigationMenu = new EventEmitter();
  @Output() internalURL = new EventEmitter();


  showLangSelector: boolean = false;
  public NAV_URL_TYPE = NAV_URL_TYPE;

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

  public APP_ROUTES = APP_ROUTES;
  public isLoggedIn = false;
  public userProfile: KeycloakProfile | undefined;
  form: FormGroup = new FormGroup({});

  constructor(
    private readonly keycloak: KeycloakService,
    private router: Router,
    private formBuilder: FormBuilder,
    private translate: TranslateService,
    private navgigateService: NavigateService
  ) { }

  ngOnChanges(changes: SimpleChanges): void {
    if (changes['currentPage']) {
      this.activeNavItem({ name: this.currentPage })
    }
  }

  ngOnInit() {
    this.setForm();
    this.isLoggedIn = this.keycloak.isLoggedIn();
    if (this.isLoggedIn) {
      this.keycloak.loadUserProfile().then((profile) => {
        this.userProfile = profile;
      });
    }
    this.activeNavItem({ name: this.currentPage })
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

  public setForm() {
    this.form = this.formBuilder.group({
      lang: [this.translate.currentLang, Validators.required],
    });
    this.form.controls['lang'].valueChanges.subscribe(() => { this.changeLang() })
  }

  private changeLang() {
    this.translate.use(this.form.controls['lang'].value);
  }

  public goTo(route: string) {
    this.router.navigate(['/' + route])
  }

  public selectPCLang(lang: string) {
    this.showLangSelector = !this.showLangSelector;
    this.form.controls['lang'].setValue(lang);
  }

  public changeShowLangSelector(status: boolean) {
    this.showLangSelector = status;
  }

  public externalNavigate(route: string) {
    this.navgigateService.openNewPage(route);
  }

  public navigate(navControl: any) {
    switch (navControl.urlType) {
      case NAV_URL_TYPE.EXTERNAL:
        this.externalNavigate(navControl.url);
        break;
      case NAV_URL_TYPE.INTERNAL:
        this.internalURL.next(navControl.url);
        this.goTo(navControl.url);
        this.activeNavItem(navControl.item);
        if (navControl.url === APP_ROUTES.FORMULARY) {
          this.changeFormStep.next({
            steps: 0,
            selectedCardWelcome: 0
          })
        }
        break;
      case NAV_URL_TYPE.FORMULARY:
        this.activeNavItem(navControl.item);
        this.changeFormStep.next(navControl.url);
        break;
      case NAV_URL_TYPE.COMMUNITYURL:
        this.internalURL.next(navControl.url);
        this.goTo(navControl.url);
        this.activeNavItem(navControl.item);
        break;
    }
  }

  public secundaryNav(navControl: any) {

    if (this.keycloak.isLoggedIn()) {
      if(navControl.url.includes(APP_ROUTES.ALTERNATIVE)){
        navControl.item.parentId = navControl.item.url.split("/")[1] as number;
      }

      if (!navControl.urlType) {
        navControl.urlType = NAV_URL_TYPE.COMMUNITYURL;
        navControl.name = navControl.url;
      }
      if (!navControl.url || navControl.url == APP_ROUTES.COMMUNITY) {
        navControl.url = APP_ROUTES.COMMUNITY + "/-1";
      }

      this.navigate(navControl);
    } else {
      // this.login();
      this.navigate(navControl);
    }
  }

  public activeNavItem(navControl: any) {
    this.priNavigationMenu.forEach(i => {
      this.clearNavigation(i);
      this.activeNavControl(i, navControl.name)
    });
    this.secNavigationMenu.forEach(i => {
      this.clearNavigation(i);
      if (navControl.id) {
        this.activeNavControlId(i, navControl.id)
      } else {
        this.activeNavControl(i, navControl.name)
      }
    });
  }

  private activeNavControlId(item: any, id: number, i?:number) {
    
    if (item.id === id) {
      item.active = true;
      return true;
    } else {
      if(item?.alternative?.childs){
        item?.alternative?.childs.forEach((child: any, index: number,) => {
          let childTrue = this.activeNavControlId(child, id);
          if (childTrue) {
            item.active = true;
            const com= {
              parent: i,
              alternative: child.id
            }
            this.changesecNavigationMenu.next(com)
            return true;
          }
          return false;
        });
      }
      
      if (item.childs) {
        item.childs.forEach((child: any, index: number,) => {
          let childTrue = this.activeNavControlId(child, id, index);
          if (childTrue) {
            item.active = true;
            const com= {
              parent: index,
              alternative: null
            }
            this.changesecNavigationMenu.next(com)
            return true;
          }
          return false;
        });
      }
      return false
    }

  }

  private activeNavControl(item: any, name: string) {
    if (item.name === name) {
      item.active = true;
      return true;
    } else {
      if (item.childs) {
        item.childs.forEach((child: any) => {
          let childTrue = this.activeNavControl(child, name);
          if (childTrue) {
            item.active = true;
            return true;
          }
          return false;
        });
      }
      return false
    }
  }

  private clearNavigation(item: any) {
    item.active = false
    item.hover = false
    if (item.childs) {
      item.childs.forEach((child: any) => {
        this.clearNavigation(child);
      })
    }
    return item;
  }

}
