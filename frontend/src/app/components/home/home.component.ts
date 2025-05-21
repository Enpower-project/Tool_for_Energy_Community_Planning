import { Component, OnInit } from '@angular/core';
import { Router } from '@angular/router';
import { APP_ROUTES } from '../../data/routes';
import { NavigateService } from '../../services/navigate.service';
import { EXTERNAL_ROUTES } from '../../data/externalRoutes';
import { ViewportScroller } from '@angular/common';
import { KeycloakToolsService } from '../../services/keycloak-tools.service';
import { FindCommunityService } from '../../services/find-community.service';
import { KeycloakService } from 'keycloak-angular';
import { CardInfo } from '../../data/types';
/**
 * home page
 *
 * @export
 * @class HomeComponent
 * @typedef {HomeComponent}
 */
@Component({
  selector: 'app-home',
  templateUrl: './home.component.html',
  styleUrls: ['./home.component.scss']
})
export class HomeComponent implements OnInit {

  /**
   * is active the burger menu modal
   *
   * @public
   * @type {boolean}
   */
  public showBurgerMenu: boolean = false;
  /**
   * Routes from the APP
   *
   * @public
   * @type {*}
   */
  public APP_ROUTES = APP_ROUTES;
  /**
   * External routes
   *
   * @public
   * @type {*}
   */
  public EXTERNAL_ROUTES = EXTERNAL_ROUTES;

  /**
   * Array with cards image name 
   *
   * @public
   * @type {{}}
   */
  public home_images = [
    "play.svg",
    "community.svg",
    "books-blue.svg",
    "network_sizing.svg"
  ]

  public communityList: any;
  public cardCommunityList: CardInfo[] = [];

  public limitCommunity: number = 2;
  public MaxlimitCommunity: number = 2;
  public showMoreCards: boolean = false;

  public isUserLogged: boolean = false;

  public loadingCommunitiesList: boolean = false;

  /**
   * Creates an instance of HomeComponent.
   *
   * @constructor
   * @param {Router} router
   * @param {NavigateService} navigateService
   * @param {ViewportScroller} viewportScroller
   */
  constructor(
    private router: Router,
    private navigateService: NavigateService,
    private viewportScroller: ViewportScroller,
    private keyToolsService: KeycloakToolsService,
    private findCommunityService: FindCommunityService,
    private readonly keycloak: KeycloakService,
  ) { }

  ngOnInit(): void {
    this.isUserLogged = this.keycloak.isLoggedIn()
    if (this.isUserLogged) {
      this.getCommunityList();
    }
  }

  /**
   * Allows navigate inside the app and puts you at the top 
   *
   * @param {string} route
   */
  goTo(route: string) {
    this.viewportScroller.scrollToPosition([0, 0]);
    this.router.navigate(['/' + route])
  }

  /**
   *  Allows navigate outside the app
   *
   * @param {?string} [name]
   */
  navigateMoreSites(name?: string) {
    if (name) {
      this.navigateService.openNewPage((EXTERNAL_ROUTES as any)[name])
    } else {
      this.navigateService.openNewPage(EXTERNAL_ROUTES.MORE_SITES)
    }
  }

  /**
   *  Allows navigate yo a custom screen inside formulary 
   *
   * @param {boolean} guide
   */
  goToForm(guide: boolean) {
    this.viewportScroller.scrollToPosition([0, 0]);
    this.router.navigate(["/" + APP_ROUTES.FORMULARY], guide ? { queryParams: { guided_modeling: 'true' } } : { queryParams: { explore_my_community: 'true' } });
  }

  private getCommunityList() {
    this.loadingCommunitiesList = true;
    this.keyToolsService.getUserUID().then(uid => {
      this.findCommunityService.getCommunityList().subscribe({
        next: (data: any) => {
          this.communityList = data.filter((da: any) => da.author === uid);
          if (this.communityList) {
            this.generateCardArrayList();
          }
        }, error: (err: any) => {
          console.error(err.message)
        }
      })
    })
  }

  private generateCardArrayList() {
    this.cardCommunityList = [];
    this.MaxlimitCommunity = this.communityList?.length ?? 2;
    this.communityList.forEach((community: any) => {
      this.cardCommunityList.push({
        id: community.id,
        name: community.name,
        description: community.description,
        infoIcon: false,
        title: community.name,
        parentID: community.context_parent,
        iconName: "community.svg"
      } as CardInfo)
    });
    setTimeout(() => {
      this.loadingCommunitiesList = false;
    }, 250);
  }

  public changeCardLimit() {
    if (!this.showMoreCards) {
      this.limitCommunity = this.MaxlimitCommunity;
      this.showMoreCards = true;
    } else {
      this.limitCommunity = 2;
      this.showMoreCards = false;
    }
  }

  public goToCommunity(card: CardInfo) {

    if (card.parentID) {
      this.navigateToAlternative(card)
    } else {
      this.router.navigate([`/${APP_ROUTES.COMMUNITY}/${card.id}`]);
    }

  }

  public navigateToAlternative(alternative: any) {
    const route = APP_ROUTES.COMMUNITY + "/" + alternative.parentID + "/" + APP_ROUTES.ALTERNATIVE + "/" + alternative.id;
    this.router.navigate([route])
  }

}
